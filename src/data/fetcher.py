"""
Модуль выгрузки первичных квантово-структурных данных из Materials Project API.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import pandas as pd
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MaterialsFetcher")


class MaterialsFetcher:
    """
    Класс для подключения к Materials Project API (v2) и выгрузки
    кандидатов в полупроводниковые преобразователи.
    """

    def __init__(self, config_path: str = "configs/data_config.yaml", env_path: str = ".env"):
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.config_path = self.project_root / config_path
        self.env_path = self.project_root / env_path
        
        self.config = self._load_config()
        self.api_key = self._load_api_key()

    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из YAML-файла."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Конфигурационный файл не найден: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logger.info("Конфигурация успешно загружена: %s", self.config_path)
        return config

    def _load_api_key(self) -> str:
        """Безопасная загрузка API-ключа из .env файла."""
        if self.env_path.exists():
            load_dotenv(self.env_path)
        
        api_key = os.getenv("MP_API_KEY")
        if not api_key:
            raise ValueError(
                f"Ключ MP_API_KEY не найден в переменных окружения или файле {self.env_path}. "
                "Создайте .env и укажите MP_API_KEY=ваш_ключ."
            )
        
        # Проверка на плейсхолдер
        placeholders = {"your_materials_project_api_key_here", "YOUR_API_KEY_HERE", "your_actual_api_key_here"}
        if api_key in placeholders or len(api_key.strip()) < 10:
            raise ValueError(
                "В файле .env указан плейсхолдер вместо реального ключа Materials Project API. "
                "Пожалуйста, вставьте ваш реальный ключ."
            )
        
        logger.info("API-ключ успешно получен из окружения (длина: %d символов).", len(api_key))
        return api_key.strip()

    def fetch_data(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Выполнение запроса к Materials Project summary API.
        
        Параметры:
            limit: Максимальное количество записей (для тестовых запусков).
                   Если None — выгружаются все доступные записи по фильтрам.
        """
        try:
            from mp_api.client import MPRester
        except ImportError:
            raise ImportError(
                "Библиотека mp-api не установлена. "
                "Установите зависимости: pip install mp-api"
            )

        filters = self.config.get("screening_filters", {})
        min_bg = float(filters.get("min_band_gap", 0.1))
        max_bg = float(filters.get("max_band_gap", 8.0))
        max_hull = float(filters.get("max_energy_above_hull", 0.05))
        max_sites = int(filters.get("max_num_sites", 50))

        requested_fields = self.config.get("requested_fields", [])
        logger.info(
            "Старт выгрузки из Materials Project API (v2):\n"
            "  - Запрещенная зона: [%.2f, %.2f] эВ\n"
            "  - Макс. энергия над оболочкой: %.3f эВ/атом\n"
            "  - Макс. атомов в ячейке: %d\n"
            "  - Лимит записей: %s",
            min_bg, max_bg, max_hull, max_sites, limit if limit else "Все доступные"
        )

        records: List[Dict[str, Any]] = []

        with MPRester(self.api_key) as mpr:
            # Поиск в summary endpoint с серверной фильтрацией
            docs = mpr.materials.summary.search(
                band_gap=(min_bg, max_bg),
                energy_above_hull=(0.0, max_hull),
                num_sites=(1, max_sites),
                fields=requested_fields,
            )

            total_found = len(docs)
            logger.info("Получен ответ API: найдено %d материалов, удовлетворяющих первичным фильтрам.", total_found)

            for i, doc in enumerate(docs):
                if limit and i >= limit:
                    logger.info("Достигнут заданный лимит записей: %d", limit)
                    break

                row = self._parse_doc_to_dict(doc)
                records.append(row)

                if (i + 1) % 5000 == 0:
                    logger.info("Обработано %d / %d записей...", i + 1, total_found if not limit else limit)

        df = pd.DataFrame(records)
        logger.info("Сформирован DataFrame сырых данных: %d строк, %d колонок.", len(df), len(df.columns))
        return df

    def _parse_doc_to_dict(self, doc: Any) -> Dict[str, Any]:
        """
        Преобразование объекта MPDataDoc в плоский словарь для сохранения в Parquet.
        """
        row: Dict[str, Any] = {}

        # 1. Базовые квантовые свойства
        row["material_id"] = str(getattr(doc, "material_id", ""))
        row["formula_pretty"] = str(getattr(doc, "formula_pretty", ""))
        row["band_gap"] = float(getattr(doc, "band_gap", 0.0) or 0.0)
        row["is_gap_direct"] = bool(getattr(doc, "is_gap_direct", False))
        row["is_metal"] = bool(getattr(doc, "is_metal", False))
        row["is_stable"] = bool(getattr(doc, "is_stable", False))
        row["theoretical"] = bool(getattr(doc, "theoretical", True))

        # 2. Термодинамика и геометрия
        row["density"] = float(getattr(doc, "density", 0.0) or 0.0)
        row["volume"] = float(getattr(doc, "volume", 0.0) or 0.0)
        row["nsites"] = int(getattr(doc, "nsites", 0) or 0)
        row["energy_per_atom"] = float(getattr(doc, "energy_per_atom", 0.0) or 0.0)
        row["energy_above_hull"] = float(getattr(doc, "energy_above_hull", 0.0) or 0.0)
        row["formation_energy_per_atom"] = float(getattr(doc, "formation_energy_per_atom", 0.0) or 0.0)

        # 3. Симметрия и кристаллография
        sym = getattr(doc, "symmetry", None)
        if sym:
            row["crystal_system"] = str(getattr(sym, "crystal_system", "")).replace("CrystalSystem.", "").lower()
            row["symbol"] = str(getattr(sym, "symbol", ""))
            row["spacegroup_number"] = int(getattr(sym, "number", 0) or 0)
        else:
            row["crystal_system"] = "unknown"
            row["symbol"] = "unknown"
            row["spacegroup_number"] = 0

        # 4. Химический состав и формула
        comp = getattr(doc, "composition", None)
        if comp:
            row["composition"] = str(comp.reduced_formula if hasattr(comp, "reduced_formula") else comp)
            # Список химических элементов и число компонентов
            if hasattr(comp, "elements"):
                row["elements"] = [el.symbol for el in comp.elements]
                row["nelements"] = len(row["elements"])
            else:
                row["elements"] = []
                row["nelements"] = 0
        else:
            row["composition"] = row["formula_pretty"]
            row["elements"] = []
            row["nelements"] = 0

        # 5. Магнетизм и спиновые свойства
        row["total_magnetization"] = float(getattr(doc, "total_magnetization", 0.0) or 0.0)
        row["is_magnetic"] = bool(getattr(doc, "is_magnetic", False))
        ord_val = getattr(doc, "ordering", None)
        row["ordering"] = str(ord_val.value if hasattr(ord_val, "value") else (ord_val or "NM"))

        # 6. Энергетические уровни краев зон (для контактов Шоттки и гетеропереходов)
        row["cbm"] = float(getattr(doc, "cbm", 0.0) or 0.0)
        row["vbm"] = float(getattr(doc, "vbm", 0.0) or 0.0)
        row["efermi"] = float(getattr(doc, "efermi", 0.0) or 0.0)

        # 7. Модули упругости (для корреляции с радиационной жесткостью Ed)
        bm = getattr(doc, "bulk_modulus", None)
        sm = getattr(doc, "shear_modulus", None)
        if isinstance(bm, dict):
            row["bulk_modulus_vrh"] = float(bm.get("vrh", 0.0) or 0.0)
        else:
            row["bulk_modulus_vrh"] = float(bm) if bm is not None else None

        if isinstance(sm, dict):
            row["shear_modulus_vrh"] = float(sm.get("vrh", 0.0) or 0.0)
        else:
            row["shear_modulus_vrh"] = float(sm) if sm is not None else None

        # 8. Экспериментальные базы данных (ICSD)
        db_ids = getattr(doc, "database_IDs", None)
        if db_ids and isinstance(db_ids, dict):
            icsd_ids = db_ids.get("icsd", [])
            row["has_icsd"] = len(icsd_ids) > 0
            row["icsd_ids"] = str(icsd_ids)
        else:
            row["has_icsd"] = False
            row["icsd_ids"] = ""

        return row

    def save_raw_data(self, df: pd.DataFrame, output_path: Optional[str] = None) -> Path:
        """Сохранение сырых данных в формат Apache Parquet."""
        storage = self.config.get("storage", {})
        if output_path is None:
            raw_dir = self.project_root / storage.get("raw_data_dir", "data/01_raw")
            filename = storage.get("raw_filename", "materials_project_raw.parquet")
            target_path = raw_dir / filename
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        # Сохранение с zstd-сжатием
        df.to_parquet(target_path, index=False, engine="pyarrow", compression="zstd")
        logger.info("Сырые данные успешно сохранены: %s (размер: %.2f МБ)", target_path, target_path.stat().st_size / (1024 * 1024))
        return target_path


def main():
    """Точка входа CLI для автономного запуска модуля выгрузки."""
    import argparse
    parser = argparse.ArgumentParser(description="Materials Project Ingestion Script")
    parser.add_argument("--limit", type=int, default=None, help="Лимит на количество выгружаемых кристаллов (для теста)")
    parser.add_argument("--output", type=str, default=None, help="Пользовательский путь сохранения parquet")
    args = parser.parse_args()

    fetcher = MaterialsFetcher()
    df = fetcher.fetch_data(limit=args.limit)
    out_file = fetcher.save_raw_data(df, output_path=args.output)
    print(f"\n[УСПЕХ] Загрузка завершена! Сохранено {len(df)} записей в файл:\n{out_file}")


if __name__ == "__main__":
    main()
