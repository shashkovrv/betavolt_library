"""
Модуль расчета радиационной кинематики, порогов смещения атомов и радиационной стойкости.
"""

from typing import Tuple, Union
import numpy as np
from src.physics.constants import (
    ELECTRON_REST_ENERGY_KEV,
    ATOMIC_MASS_UNIT_KEV,
    FINE_STRUCTURE_CONST,
    PI_RE_SQUARED_BARNS,
    VAN_VECHTEN_D0,
    VAN_VECHTEN_D1,
    VAN_VECHTEN_D2,
    VAN_VECHTEN_D3
)


def max_recoil_energy(
    E_beta_keV: Union[float, np.ndarray],
    A_min_amu: float
) -> Union[float, np.ndarray]:
    """
    Максимальная кинетическая энергия отдачи ядра атома мишени при лобовом
    упругом соударении с релятивистским бета-электроном.
    
    Формула:
        T_max = [ 2 * E_beta * (E_beta + 2 * m_e * c^2) ] / [ M_nucleus * c^2 ] * 10^3  [эВ]
        
    Физическое обоснование:
        В сложных бинарных и многокомпонентных кристаллах (SiC, GaN, TiO2) энергия
        отдачи T_max обратно пропорциональна массе ядра (1 / A).
        Поэтому при оценке радиационной стойкости всегда берется масса ЛЕГЧАЙШЕЙ
        подрешетки A_min, так как именно легкие атомы (углерод, азот, кислород)
        первыми выбиваются из узлов решетки.
        
    Параметры:
        E_beta_keV: Энергия бета-электрона, кэВ
        A_min_amu: Масса легчайшего ядра решетки, а.е.м.
        
    Возвращает:
        Энергия отдачи T_max в электрон-вольтах (эВ).
    """
    if A_min_amu <= 0:
        raise ValueError(f"Атомная масса должна быть строго положительной: A={A_min_amu}")

    is_scalar = np.isscalar(E_beta_keV)
    E = np.atleast_1d(np.asarray(E_beta_keV, dtype=float))

    # M_nucleus * c^2 в кэВ
    M_c2_keV = A_min_amu * ATOMIC_MASS_UNIT_KEV
    
    # 2 * m_e * c^2 в кэВ
    two_mc2 = 2.0 * ELECTRON_REST_ENERGY_KEV

    numerator = 2.0 * E * (E + two_mc2)
    # * 1000 для перевода кэВ -> эВ
    t_max_eV = (numerator / M_c2_keV) * 1000.0

    if is_scalar:
        return float(t_max_eV[0])
    return t_max_eV


def displacement_threshold_van_vechten(
    Eg_eV: float,
    Ecoh_eV: float,
    Tm_K: float = 1500.0
) -> float:
    """
    Пороговая энергия смещения атома из узла кристаллической решетки по полуэмпирической
    модели Ван-Вехтена / Келли–Гроувса (Van Vechten, 1980).
    
    Формула:
        E_d = 8.0 + 1.8 * E_g + 2.0 * E_coh + 0.002 * T_m  [эВ]
        
    Параметры:
        Eg_eV: Ширина запрещенной зоны, эВ
        Ecoh_eV: Энергия когезии решетки, эВ/атом
        Tm_K: Температура плавления решетки, К (по умолчанию 1500 К)
        
    Возвращает:
        Пороговая энергия смещения E_d в эВ (физический диапазон 10 - 55 эВ).
    """
    ed = VAN_VECHTEN_D0 + VAN_VECHTEN_D1 * Eg_eV + VAN_VECHTEN_D2 * Ecoh_eV + VAN_VECHTEN_D3 * Tm_K
    # Ограничение физическим интервалом
    return float(np.clip(ed, 10.0, 55.0))


def check_radiation_immunity(
    E_max_keV: float,
    A_min_amu: float,
    Ed_eV: float
) -> Tuple[bool, float]:
    """
    Проверка условия абсолютного термодинамического радиационного иммунитета полупроводника.
    
    Критерий:
        Материал радиационно неуязвим (is_immune = True) <=> T_max(E_max, A_min) < E_d
        
    Возвращает:
        (is_immune: bool, T_max_eV: float)
    """
    t_max = float(max_recoil_energy(E_max_keV, A_min_amu))
    is_immune = bool(t_max < Ed_eV)
    return is_immune, t_max


def radiation_hardness_score(Ed_eV: float, Ed_diamond_eV: float = 45.0) -> float:
    """
    Относительный индекс радиационной стойкости полупроводника по отношению к алмазу.
    Алмаз принят за эталон прочности (R_score = 100%).
    
    Формула:
        R_score = (E_d / E_d_diamond) * 100%
    """
    return float((Ed_eV / Ed_diamond_eV) * 100.0)


def mckinley_feshbach_cross_section(
    E_keV: float,
    Z: int,
    Ed_eV: float,
    A_amu: float
) -> float:
    """
    Релятивистское сечение смещения атома Мотта в приближении Мак-Кинли–Фешбаха (McKinley-Feshbach, 1948).
    
    Параметры:
        E_keV: Кинетическая энергия налетающего бета-электрона, кэВ
        Z: Атомный номер ядра мишени
        Ed_eV: Порог смещения атома, эВ
        A_amu: Атомная масса ядра мишени, а.е.м.
        
    Возвращает:
        Сечение дефектообразования sigma_d в барнах (1 барн = 10^-24 см2).
        Если T_max <= Ed, возвращает 0.0 (образование дефектов термодинамически запрещено).
    """
    t_max = max_recoil_energy(E_keV, A_amu)
    if t_max <= Ed_eV or Ed_eV <= 0:
        return 0.0

    # Релятивистские коэффициенты
    gamma = 1.0 + (E_keV / ELECTRON_REST_ENERGY_KEV)
    beta_sq = 1.0 - (1.0 / (gamma ** 2))
    beta = np.sqrt(beta_sq)

    ratio = t_max / Ed_eV
    ln_ratio = np.log(ratio)

    term1 = ratio - 1.0
    term2 = - beta_sq * ln_ratio
    term3 = np.pi * FINE_STRUCTURE_CONST * beta * Z * (2.0 * (np.sqrt(ratio) - 1.0) - ln_ratio)

    prefactor = PI_RE_SQUARED_BARNS * (Z ** 2) * ((1.0 - beta_sq) / (beta_sq ** 2))
    sigma = prefactor * (term1 + term2 + term3)

    return float(max(0.0, sigma))
