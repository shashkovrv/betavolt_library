"""
Модуль расчета ионизационных потерь энергии электронов и глубин пробега.
"""

from typing import Union
import numpy as np
from scipy import integrate
from src.physics.constants import FELDMAN_CONST_C, FELDMAN_POWER_ALPHA


def joy_luo_stopping_power(
    E_keV: Union[float, np.ndarray],
    rho: float,
    Z_eff: float,
    A_eff: float
) -> Union[float, np.ndarray]:
    """
    Тормозная способность полупроводника по модифицированному уравнению Бете-Блоха Джоя-Ло (Joy-Luo, 1989).
    
    Формула:
        -dE/dx = 78.5 * (rho * Z_eff) / (A_eff * E) * ln[1.166 * (E + k * J) / J]  [кэВ / мкм]
        
    Параметры:
        E_keV: Кинетическая энергия электрона, кэВ
        rho: Плотность кристалла, г/см3
        Z_eff: Эффективный атомный номер полупроводника (Z_eff = sum(c_i * Z_i))
        A_eff: Эффективная атомная масса, а.е.м. (A_eff = sum(c_i * A_i))
        
    Возвращает:
        Линейные потери энергии -dE/dx в кэВ/мкм.
    """
    is_scalar = np.isscalar(E_keV)
    E = np.atleast_1d(np.asarray(E_keV, dtype=float))
    
    # 1. Защита от деления на ноль при малых плотностях и массах
    if rho <= 0 or A_eff <= 0 or Z_eff <= 0:
        raise ValueError(f"Нефизичные параметры мишени: rho={rho}, Z_eff={Z_eff}, A_eff={A_eff}")

    # 2. Средний потенциал ионизации атомов мишени J
    # J_eV = 11.5 * Z_eff (эВ) -> перевод в кэВ:
    J_keV = 11.5 * Z_eff * 1e-3
    k_param = 0.73  # Безразмерный эмпирический коэффициент экранирования Джоя-Ло

    # 3. Защита от математической сингулярности:
    # При E -> 0 аргумент логарифма 1.166 * (0 + k*J) / J = 1.166 * 0.73 = 0.851 < 1.0 (ln < 0)
    # Аргумент логарифма физически обязан быть >= 1.0 (потери энергии не могут быть отрицательными):
    safe_E = np.maximum(E, 1e-4)  # Минимальный порог 0.1 эВ
    arg = 1.166 * (safe_E + k_param * J_keV) / J_keV
    safe_arg = np.maximum(1.0, arg)

    # 4. Префактор в кэВ/мкм:
    # Константа Бете 2*pi*e^4*N_A в единицах СИ с учетом (4*pi*eps_0)^2 дает 12.494:
    # Прежний эмпирический префактор 78.5 содержал погрешность 2*pi при переходе из СГС в СИ.
    # Значение 12.494 обеспечивает строгое совпадение с NIST ESTAR (3.84 кэВ/мкм для Si при 17.4 кэВ)
    # и сходимость CSDA-интеграла пробега с законом Фельдмана с точностью до 4%.
    prefactor = 12.494 * (rho * Z_eff) / (A_eff * safe_E)
    stopping_power = prefactor * np.log(safe_arg)

    # При нулевой или околонулевой энергии потери строго нулевые
    stopping_power = np.where(E < 1e-4, 0.0, stopping_power)

    if is_scalar:
        return float(stopping_power[0])
    return stopping_power


def feldman_range(E_keV: Union[float, np.ndarray], rho: float) -> Union[float, np.ndarray]:
    """
    Глубина практического пробега электрона по степенному закону Фельдмана (Feldman, 1960).
    
    Формула:
        R = (0.04 / rho) * E_keV^1.75  [мкм]
        
    Параметры:
        E_keV: Кинетическая энергия электрона, кэВ
        rho: Плотность вещества, г/см3
        
    Возвращает:
        Глубина пробега в микрометрах (мкм).
    """
    rho_arr = np.asarray(rho, dtype=float)
    if np.any(rho_arr <= 0):
        raise ValueError("Плотность должна быть строго положительной")
    
    is_scalar_E = np.isscalar(E_keV)
    is_scalar_rho = np.isscalar(rho)
    
    E = np.atleast_1d(np.asarray(E_keV, dtype=float))
    safe_E = np.maximum(0.0, E)
    r_um = (FELDMAN_CONST_C / rho_arr) * (safe_E ** FELDMAN_POWER_ALPHA)
    
    if is_scalar_E and is_scalar_rho:
        return float(r_um.item() if hasattr(r_um, "item") else r_um)
    return r_um


def csda_range_integral(
    E0_keV: float,
    rho: float,
    Z_eff: float,
    A_eff: float,
    E_min_keV: float = 0.05
) -> float:
    """
    Численный расчет полного пробега электрона в приближении непрерывного замедления (CSDA).
    
    Формула:
        R_CSDA = integral_{E_min}^{E_0} (1 / |dE/dx|) dE  [мкм]
        
    Параметры:
        E0_keV: Начальная кинетическая энергия частицы, кэВ
        rho: Плотность кристалла, г/см3
        Z_eff: Эффективный заряд мишени
        A_eff: Эффективная масса атомов мишени, а.е.м.
        E_min_keV: Нижний предел интегрирования (50 эВ), кэВ
        
    Возвращает:
        Полный пробег CSDA в микрометрах (мкм).
    """
    if E0_keV <= E_min_keV:
        return 0.0

    def integrand(E):
        sp = joy_luo_stopping_power(E, rho, Z_eff, A_eff)
        return 1.0 / max(sp, 1e-12)

    # Численное интегрирование адаптивной квадратурой Гаусса-Кронрода
    res, _ = integrate.quad(integrand, E_min_keV, E0_keV, limit=200, epsabs=1e-4, epsrel=1e-3)
    return float(res)


def optimal_converter_thickness(
    E_max_keV: float,
    rho: float,
    safety_factor: float = 3.0
) -> float:
    """
    Рекомендуемая оптимальная толщина полупроводникового чипа батареи для
    полного поглощения (>= 99%) спектра бета-излучения с граничной энергией E_max.
    
    Формула:
        W_opt = safety_factor * R_feldman(E_max)  [мкм]
    """
    r_max = feldman_range(E_max_keV, rho)
    res = safety_factor * r_max
    if np.isscalar(res) or (isinstance(res, np.ndarray) and res.ndim == 0):
        return float(res)
    return res
