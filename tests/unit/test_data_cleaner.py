"""
Модульные тесты для модуля очистки данных src/data/cleaner.py.
Верификация физико-химических правил отсева и полиморфизма.
"""

import pytest
import pandas as pd
from src.data.cleaner import DataCleaner


@pytest.fixture
def mock_materials_df():
    """Синтетический тестовый датасет, содержащий как валидные полупроводники, так и мусор."""
    return pd.DataFrame([
        # 1. Валидные целевые полупроводники (ДОЛЖНЫ ОСТАТЬСЯ)
        {
            "material_id": "mp-149",
            "formula_pretty": "Si",
            "band_gap": 1.12,
            "density": 2.33,
            "volume": 40.88,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Si"],
        },
        {
            "material_id": "mp-66",
            "formula_pretty": "C",
            "band_gap": 5.47,
            "density": 3.52,
            "volume": 11.4,
            "energy_above_hull": 0.025,  # Алмаз метастабилен на 0.025 эВ относительно графита!
            "is_metal": False,
            "elements": ["C"],
        },
        {
            "material_id": "mp-804",
            "formula_pretty": "GaN",
            "band_gap": 3.44,
            "density": 6.15,
            "volume": 46.2,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Ga", "N"],
        },
        {
            "material_id": "mp-406",
            "formula_pretty": "CdTe",
            "band_gap": 1.50,
            "density": 5.85,
            "volume": 69.8,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Cd", "Te"],
        },
        # 2. Полиморфы TiO2 (оба валидны, но в Ground State должен войти рутил)
        {
            "material_id": "mp-2657",
            "formula_pretty": "TiO2",
            "band_gap": 3.05,
            "density": 4.25,
            "volume": 62.4,
            "energy_above_hull": 0.0,  # Рутил (Ground State)
            "is_metal": False,
            "elements": ["Ti", "O"],
        },
        {
            "material_id": "mp-390",
            "formula_pretty": "TiO2",
            "band_gap": 3.20,
            "density": 3.89,
            "volume": 68.2,
            "energy_above_hull": 0.015,  # Анатаз (Метастабильная фаза)
            "is_metal": False,
            "elements": ["Ti", "O"],
        },

        # 3. НЕВАЛИДНЫЕ СОЕДИНЕНИЯ (ДОЛЖНЫ БЫТЬ ОТСЕЯНЫ)
        # А) Щелочные галогениды (F-центры, каменная соль)
        {
            "material_id": "mp-22862",
            "formula_pretty": "NaCl",
            "band_gap": 5.2,
            "density": 2.16,
            "volume": 45.0,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Na", "Cl"],
        },
        # Б) Оксосоли: Селитра (KNO3) - радиолиз с газом NO2
        {
            "material_id": "mp-7186",
            "formula_pretty": "KNO3",
            "band_gap": 4.1,
            "density": 2.11,
            "volume": 82.0,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["K", "N", "O"],
        },
        # В) Оксосоли: Мел/Известняк (CaCO3) - радиолиз с газом CO2
        {
            "material_id": "mp-3958",
            "formula_pretty": "CaCO3",
            "band_gap": 4.9,
            "density": 2.71,
            "volume": 61.3,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Ca", "C", "O"],
        },
        # Г) Оксосоли: Гипс (CaSO4) - радиолиз с газом SO2
        {
            "material_id": "mp-4235",
            "formula_pretty": "CaSO4",
            "band_gap": 5.8,
            "density": 2.96,
            "volume": 76.0,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Ca", "S", "O"],
        },
        # Д) Гидриды: LiH - выбивание водорода Ed < 3 эВ
        {
            "material_id": "mp-23703",
            "formula_pretty": "LiH",
            "band_gap": 3.2,
            "density": 0.78,
            "volume": 16.8,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Li", "H"],
        },
        # Е) Щелочные халькогениды: Na2S - гидролиз парами воды с H2S
        {
            "material_id": "mp-2342",
            "formula_pretty": "Na2S",
            "band_gap": 2.6,
            "density": 1.86,
            "volume": 70.0,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Na", "S"],
        },
        # Ж) Черный список элементов: Радиоактивный уран (UO2)
        {
            "material_id": "mp-1900",
            "formula_pretty": "UO2",
            "band_gap": 2.1,
            "density": 10.97,
            "volume": 40.0,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["U", "O"],
        },
        # З) Псевдометалл: is_metal == True
        {
            "material_id": "mp-9999",
            "formula_pretty": "FeAl",
            "band_gap": 0.2,
            "density": 5.6,
            "volume": 30.0,
            "energy_above_hull": 0.0,
            "is_metal": True,
            "elements": ["Fe", "Al"],
        },
        # И) Нефизичные значения (Sanity): отрицательная плотность
        {
            "material_id": "mp-0000",
            "formula_pretty": "Ghost",
            "band_gap": 1.5,
            "density": -1.0,
            "volume": 50.0,
            "energy_above_hull": 0.0,
            "is_metal": False,
            "elements": ["Si"],
        }
    ])


def test_data_cleaner_filtering(mock_materials_df):
    """Проверка правильности фильтрации нежизнеспособных классов."""
    cleaner = DataCleaner()
    df_cleaned, df_unique_ground = cleaner.clean_pipeline(mock_materials_df)

    # 1. Проверяем, что настоящие полупроводники выжили
    surviving_formulas = set(df_cleaned["formula_pretty"])
    assert "Si" in surviving_formulas
    assert "C" in surviving_formulas
    assert "GaN" in surviving_formulas
    assert "CdTe" in surviving_formulas
    assert "TiO2" in surviving_formulas

    # 2. Проверяем, что нежизнеспособные классы и мусор отсеяны
    assert "NaCl" not in surviving_formulas      # Щелочной галогенид
    assert "KNO3" not in surviving_formulas      # Нитрат
    assert "CaCO3" not in surviving_formulas     # Карбонат
    assert "CaSO4" not in surviving_formulas     # Сульфат
    assert "LiH" not in surviving_formulas       # Неорганический гидрид
    assert "Na2S" not in surviving_formulas      # Щелочной халькогенид
    assert "UO2" not in surviving_formulas       # Радиоактивный элемент
    assert "FeAl" not in surviving_formulas      # Металл
    assert "Ghost" not in surviving_formulas     # Отрицательная плотность

    # 3. Проверка полиморфизма
    # В df_cleaned должны быть обе фазы TiO2 (рутил и анатаз)
    tio2_polymorphs = df_cleaned[df_cleaned["formula_pretty"] == "TiO2"]
    assert len(tio2_polymorphs) == 2

    # В df_unique_ground должен остаться только 1 рутил (mp-2657, E_hull=0.0)
    ground_tio2 = df_unique_ground[df_unique_ground["formula_pretty"] == "TiO2"]
    assert len(ground_tio2) == 1
    assert ground_tio2.iloc[0]["material_id"] == "mp-2657"
    assert ground_tio2.iloc[0]["energy_above_hull"] == 0.0
