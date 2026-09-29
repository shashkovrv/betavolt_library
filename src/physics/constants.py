"""
Фундаментальные физические константы (CODATA 2022) и параметры бета-активных изотопов.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from pathlib import Path
import yaml


# ==============================================================================
# ФУНДАМЕНТАЛЬНЫЕ ФИЗИЧЕСКИЕ КОНСТАНТЫ (CODATA 2022 / NIST)
# ==============================================================================

# Элементарный заряд электрона, Кл
Q_ELECTRON: float = 1.602176634e-19

# Постоянная Больцмана, Дж/К
K_BOLTZMANN: float = 1.380649e-23

# Постоянная Больцмана, эВ/К
K_BOLTZMANN_EV: float = 8.617333262e-5

# Скорость света в вакууме, м/с
SPEED_OF_LIGHT: float = 299792458.0

# Масса покоя электрона, кг
ELECTRON_MASS_KG: float = 9.1093837015e-31

# Энергия покоя электрона m_e * c^2, кэВ и эВ
ELECTRON_REST_ENERGY_KEV: float = 510.99895
ELECTRON_REST_ENERGY_EV: float = 510998.95

# Электрическая постоянная (диэлектрическая проницаемость вакуума), Ф/м
VACUUM_PERMITTIVITY: float = 8.8541878128e-12

# Атомная единица массы (а.е.м.), кг
ATOMIC_MASS_UNIT_KG: float = 1.66053906660e-27

# Энергетический эквивалент 1 а.е.м. (u * c^2), кэВ
ATOMIC_MASS_UNIT_KEV: float = 931494.0

# Постоянная Планка приведенная (дирак), Дж * с
H_BAR: float = 1.054571817e-34

# Постоянная тонкой структуры
FINE_STRUCTURE_CONST: float = 1.0 / 137.035999084

# Классический радиус электрона r_e, см
CLASSICAL_ELECTRON_RADIUS_CM: float = 2.8179403262e-13

# Сечение pi * r_e^2, барн (1 барн = 10^-24 см^2)
PI_RE_SQUARED_BARNS: float = 0.249435

# Нормальная комнатная температура T, К
ROOM_TEMPERATURE_K: float = 300.0

# Тепловое напряжение V_T = k_B * T / q при 300 К, В
THERMAL_VOLTAGE_300K: float = K_BOLTZMANN_EV * ROOM_TEMPERATURE_K  # ~ 0.025852 В


# ==============================================================================
# ПАРАМЕТРЫ РАДИОАКТИВНЫХ БЕТА-ИЗОТОПОВ
# ==============================================================================

@dataclass(frozen=True)
class IsotopeProperties:
    """Паспорт радиоактивного бета-активного изотопа."""
    name: str                       # Название изотопа
    symbol: str                     # Обозначение ядра
    half_life_years: float          # Период полураспада, лет
    half_life_seconds: float        # Период полураспада, с
    mean_energy_keV: float          # Средняя энергия спектра Ферми, кэВ
    max_energy_keV: float           # Максимальная граничная энергия E_max, кэВ
    specific_activity_TBq_g: float  # Удельная активность, ТБк/г
    density_g_cm3: float            # Плотность источника, г/см3
    daughter_z: int                 # Заряд дочернего ядра Z
    decay_type: str                 # Тип распада (чистый бета-минус)
    safety_notes: str               # Инженерные примечания по радиационной безопасности


ISOTOPES: Dict[str, IsotopeProperties] = {
    "Ni-63": IsotopeProperties(
        name="Никель-63",
        symbol="63Ni",
        half_life_years=100.1,
        half_life_seconds=3.159e9,
        mean_energy_keV=17.4,
        max_energy_keV=66.9,
        specific_activity_TBq_g=2.1,
        density_g_cm3=8.90,
        daughter_z=29,  # Cu-63
        decay_type="pure_beta_minus",
        safety_notes="Металлическое гальваническое покрытие. Нет газовыделения. Взрывобезопасен на 100 лет."
    ),
    "H-3": IsotopeProperties(
        name="Тритий",
        symbol="3H",
        half_life_years=12.32,
        half_life_seconds=3.888e8,
        mean_energy_keV=5.7,
        max_energy_keV=18.6,
        specific_activity_TBq_g=357.0,
        density_g_cm3=3.90,  # В матрице гидрида/тритида титана TiT2
        daughter_z=2,   # He-3
        decay_type="pure_beta_minus",
        safety_notes="Связывание в матрицах TiT2/ScT2. Мягкое излучение, нет радиационных дефектов решетки."
    ),
    "C-14": IsotopeProperties(
        name="Углерод-14",
        symbol="14C",
        half_life_years=5730.0,
        half_life_seconds=1.808e11,
        mean_energy_keV=49.5,
        max_energy_keV=156.5,
        specific_activity_TBq_g=0.165,
        density_g_cm3=3.515,  # Алмазная форма 14C
        daughter_z=7,   # N-14
        decay_type="pure_beta_minus",
        safety_notes="Внедрение в решетку синтетического алмаза. Экстремальный ресурс (тысячи лет)."
    ),
    "Pm-147": IsotopeProperties(
        name="Прометрий-147",
        symbol="147Pm",
        half_life_years=2.62,
        half_life_seconds=8.268e7,
        mean_energy_keV=62.0,
        max_energy_keV=224.1,
        specific_activity_TBq_g=34.3,
        density_g_cm3=7.26,   # Керамика оксида Pm2O3
        daughter_z=62,  # Sm-147
        decay_type="beta_minus_low_gamma",
        safety_notes="Высокая удельная мощность для короткоживущих автономных датчиков. Требует экранирования."
    )
}


# ==============================================================================
# ПАРАМЕТРЫ ЭМПИРИЧЕСКИХ МОДЕЛЕЙ
# ==============================================================================

# Правило Кляйна: eps_ehp = a * E_g + b (эВ)
KLEIN_COEFF_A: float = 2.8
KLEIN_CONST_B_EV: float = 0.55

# Уравнение пробега электронов Фельдмана: R = (c_f * E^alpha) / rho (мкм)
FELDMAN_CONST_C: float = 0.04
FELDMAN_POWER_ALPHA: float = 1.75

# Порог смещения атомов Ван-Вехтена: E_d = d0 + d1*Eg + d2*Ecoh + d3*Tm (эВ)
VAN_VECHTEN_D0: float = 8.0
VAN_VECHTEN_D1: float = 1.8
VAN_VECHTEN_D2: float = 2.0
VAN_VECHTEN_D3: float = 0.002


def get_isotope(key: str) -> IsotopeProperties:
    """Получение паспорта изотопа по ключу (Ni-63, H-3, C-14, Pm-147)."""
    normalized_key = key.replace(" ", "").replace("_", "-")
    if normalized_key in ISOTOPES:
        return ISOTOPES[normalized_key]
    raise KeyError(f"Неизвестный изотоп '{key}'. Допустимые: {list(ISOTOPES.keys())}")
