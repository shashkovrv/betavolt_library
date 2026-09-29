"""
Модуль очистки, физической фильтрации и разрешения полиморфизма полупроводников.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set, Optional
import yaml
import pandas as pd
import numpy as np

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("DataCleaner")

# Константы семейств элементов периодической таблицы Менделеева
ALKALI_METALS = {"Li", "Na", "K", "Rb", "Cs"}
ALKALINE_EARTH_METALS = {"Be", "Mg", "Ca", "Sr", "Ba"}
HALOGENS = {"F", "Cl", "Br", "I"}
CHALCOGENS = {"S", "Se", "Te"}


class DataCleaner:
    """
    Класс для комплексной очистки и физико-химической фильтрации
    кандидатов в бетавольтаические полупроводники.
    """

    def __init__(self, config_path: str = "configs/data_config.yaml"):
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.config_path = self.project_root / config_path
        self.config = self._load_config()

        self.blacklist = set(self.config.get("blacklist_elements", []))
        self.stats: Dict[str, int] = {}

    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации из YAML."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def clean_pipeline(self, df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Полный конвейер очистки:
        1. Sanity check (физическая корректность числовых полей).
        2. Фильтрация псевдометаллов.
        3. Фильтрация по черному списку элементов (радиоактивные, газы, Hg, Tl, Pm).
        4. Физико-химическая отбраковка нежизнеспособных классов (соли, мел, гидриды).
        5. Разрешение полиморфизма (выделение уникальных основных фаз Ground State).
        
        Возвращает:
            (df_cleaned, df_unique_ground)
        """
        n_initial = len(df_raw)
        self.stats["0_initial_raw"] = n_initial
        logger.info("=== ОЧИСТКА ДАННЫХ (Вход: %d записей) ===", n_initial)

        # 1. Физическая валидация базовых числовых полей
        df = self._filter_sanity(df_raw)

        # 2. Исключение псевдометаллов и полуметаллов
        df = self._filter_metals(df)

        # 3. Фильтрация по черному списку элементов
        df = self._filter_blacklist(df)

        # 4. Физико-химическая фильтрация классов соединений
        df = self._filter_unviable_classes(df)

        self.stats["4_all_valid_polymorphs"] = len(df)
        logger.info("Успешно отобрано валидных полупроводниковых фаз: %d (отсеяно суммарно: %d)", len(df), n_initial - len(df))

        # 5. Разрешение кристаллического полиморфизма (наиболее стабильная фаза на формулу)
        df_unique_ground = self._resolve_polymorphism(df)
        self.stats["5_unique_ground_states"] = len(df_unique_ground)
        logger.info("Уникальных стабильных химических соединений (Ground State): %d", len(df_unique_ground))

        return df, df_unique_ground

    def _filter_sanity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Отсечение пропусков и нефизичных значений (отрицательная плотность, объем, щель)."""
        initial_len = len(df)
        critical_cols = ["formula_pretty", "band_gap", "density", "volume", "energy_above_hull"]
        df_clean = df.dropna(subset=critical_cols).copy()

        df_clean = df_clean[
            (df_clean["density"] > 0.05) &
            (df_clean["volume"] > 1.0) &
            (df_clean["band_gap"] >= 0.1) &
            (df_clean["band_gap"] <= 8.0) &
            (df_clean["energy_above_hull"] >= 0.0) &
            (df_clean["energy_above_hull"] <= 0.05)
        ]

        dropped = initial_len - len(df_clean)
        self.stats["1_dropped_sanity"] = dropped
        logger.info("1. Sanity check: отсеяно %d строк с некорректными физическими значениями. Осталось: %d", dropped, len(df_clean))
        return df_clean

    def _filter_metals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Исключение записей, помеченных DFT как металлы (ошибки расчета псевдощелей)."""
        initial_len = len(df)
        if "is_metal" in df.columns:
            df_clean = df[df["is_metal"] == False].copy()
        else:
            df_clean = df.copy()

        dropped = initial_len - len(df_clean)
        self.stats["2_dropped_metals"] = dropped
        logger.info("2. Metal check: отсеяно %d псевдометаллов. Осталось: %d", dropped, len(df_clean))
        return df_clean

    def _filter_blacklist(self, df: pd.DataFrame) -> pd.DataFrame:
        """Исключение соединений, содержащих элементы из черного списка."""
        initial_len = len(df)

        def contains_blacklisted(row) -> bool:
            elements = row.get("elements", [])
            if isinstance(elements, (list, np.ndarray, set)):
                return bool(set(elements) & self.blacklist)
            # Запасной вариант парсинга через строку элементов
            formula = str(row.get("formula_pretty", ""))
            return any(el in formula for el in self.blacklist)

        mask = df.apply(contains_blacklisted, axis=1)
        df_clean = df[~mask].copy()

        dropped = initial_len - len(df_clean)
        self.stats["3_dropped_blacklist"] = dropped
        logger.info("3. Blacklist check: отсеяно %d материалов с радиоактивными/токсичными элементами. Осталось: %d", dropped, len(df_clean))
        return df_clean

    def _filter_unviable_classes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Физико-химическая отбраковка классов:
        - Щелочные галогениды (F-центры по Лущику, экситонный распад, гигроскопичность).
        - Оксосоли (нитраты, сульфаты, карбонаты: радиолиз с газовыделением).
        - Неорганические гидриды (Ed < 3 эВ, выбивание протонов бета-электронами).
        - Щелочные халькогениды (бурный гидролиз с H2S).
        - Интерметаллиды (металлический перенос, экранировка).
        """
        initial_len = len(df)
        rejection_reasons = []

        def check_class_unviability(row) -> Optional[str]:
            elements = set(row.get("elements", []))
            formula = str(row.get("formula_pretty", ""))

            # А) Щелочные галогениды (NaCl, LiF, KBr, CsI)
            if (elements & ALKALI_METALS) and (elements & HALOGENS):
                return "Alkali Halide (STE F-centers, hygroscopic)"

            # Б) Щелочные халькогениды (Na2S, K2Se, Li2Te)
            if (elements & ALKALI_METALS) and (elements & CHALCOGENS) and not (elements - ALKALI_METALS - CHALCOGENS):
                return "Alkali Chalcogenide (Rapid ambient air hydrolysis)"

            # В) Неорганические гидриды (LiH, CaH2)
            if "H" in elements and "C" not in elements:
                return "Inorganic Hydride (Low displacement threshold Ed < 3 eV, H2 gas radiolysis)"

            # Г) Оксосоли (радиолиз ковалентных связей аниона с выделением газов)
            if "O" in elements:
                # Оценка стехиометрии по pymatgen composition
                try:
                    from pymatgen.core import Composition
                    comp = Composition(formula)
                    elem_dict = comp.as_dict()
                    o_count = elem_dict.get("O", 0.0)

                    # Нитраты/нитриты (N + O при O/N >= 2)
                    if "N" in elem_dict and (o_count / max(elem_dict["N"], 1e-4) >= 2.0):
                        return "Oxysalt: Nitrate/Nitrite (NO2 gas radiolysis)"

                    # Сульфаты/сульфиты (S + O при O/S >= 2.5)
                    if "S" in elem_dict and (o_count / max(elem_dict["S"], 1e-4) >= 2.5):
                        return "Oxysalt: Sulfate/Sulfite (SO2 gas radiolysis)"

                    # Карбонаты (C + O при наличии металлов и O/C >= 2.5)
                    if "C" in elem_dict and (o_count / max(elem_dict["C"], 1e-4) >= 2.5):
                        return "Oxysalt: Carbonate (CO2 gas radiolysis)"

                    # Фосфаты (P + O при O/P >= 2.5)
                    if "P" in elem_dict and (o_count / max(elem_dict["P"], 1e-4) >= 2.5):
                        return "Oxysalt: Phosphate (P-O radiolysis)"
                except Exception:
                    pass

            return None

        # Применяем фильтр
        unviable_masks = []
        for _, row in df.iterrows():
            reason = check_class_unviability(row)
            if reason:
                rejection_reasons.append(reason)
                unviable_masks.append(True)
            else:
                unviable_masks.append(False)

        df_clean = df[~np.array(unviable_masks)].copy()
        dropped = initial_len - len(df_clean)
        self.stats["4_dropped_unviable_classes"] = dropped

        # Логируем статистику причин отбраковки
        if rejection_reasons:
            from collections import Counter
            counts = Counter(rejection_reasons)
            logger.info("4. Детализация отсева по классам (суммарно %d):", dropped)
            for reason, count in counts.most_common():
                logger.info("   - %s: %d шт.", reason, count)

        logger.info("Осталось после фильтрации: %d", len(df_clean))
        return df_clean

    def _resolve_polymorphism(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Разрешение полиморфизма:
        Для каждой химической формулы отбирается модификация с минимальной
        энергией над выпуклой оболочкой (наиболее термодинамически стабильная).
        """
        df_sorted = df.sort_values(by=["formula_pretty", "energy_above_hull", "density"], ascending=[True, True, False])
        df_unique = df_sorted.drop_duplicates(subset=["formula_pretty"], keep="first").reset_index(drop=True)
        return df_unique

    def save_cleaned_data(
        self,
        df_cleaned: pd.DataFrame,
        df_unique_ground: pd.DataFrame,
        out_cleaned: Optional[str] = None,
        out_ground: Optional[str] = None
    ) -> Tuple[Path, Path]:
        """Сохранение очищенных данных в Parquet."""
        storage = self.config.get("storage", {})
        inter_dir = self.project_root / storage.get("intermediate_dir", "data/02_intermediate")
        inter_dir.mkdir(parents=True, exist_ok=True)

        path_cleaned = inter_dir / (out_cleaned or storage.get("cleaned_filename", "semiconductors_cleaned.parquet"))
        path_ground = inter_dir / (out_ground or storage.get("ground_state_filename", "semiconductors_unique_ground.parquet"))

        df_cleaned.to_parquet(path_cleaned, index=False, engine="pyarrow", compression="zstd")
        df_unique_ground.to_parquet(path_ground, index=False, engine="pyarrow", compression="zstd")

        logger.info("Сохранено: %s (все фазы, %d строк)", path_cleaned, len(df_cleaned))
        logger.info("Сохранено: %s (только Ground State, %d строк)", path_ground, len(df_unique_ground))
        return path_cleaned, path_ground


def main():
    """CLI запуска модуля очистки."""
    import argparse
    parser = argparse.ArgumentParser(description="Data Cleaning & Polymorphism Pipeline")
    parser.add_argument("--input", type=str, default=None, help="Путь к сырому Parquet файлу")
    args = parser.parse_args()

    cleaner = DataCleaner()
    input_path = args.input or "data/01_raw/materials_project_raw.parquet"
    if not Path(input_path).exists():
        print(f"[ОШИБКА] Сырой файл не найден: {input_path}. Сначала выполните fetcher.py!")
        sys.exit(1)

    df_raw = pd.read_parquet(input_path)
    df_clean, df_ground = cleaner.clean_pipeline(df_raw)
    cleaner.save_cleaned_data(df_clean, df_ground)
    print("\n[УСПЕХ] Конвейер очистки завершен успешно!")


if __name__ == "__main__":
    main()
