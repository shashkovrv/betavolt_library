"""
Модуль расчета диодных вольт-амперных характеристик, выходной мощности и КПД (модель Олсена).
"""

from typing import Union, Optional
import numpy as np
from src.physics.constants import (
    K_BOLTZMANN_EV,
    ROOM_TEMPERATURE_K
)
from src.physics.generation import ehp_generation_energy


def reverse_saturation_current(
    Eg_eV: Union[float, np.ndarray],
    T_K: float = ROOM_TEMPERATURE_K,
    ideality_factor: float = 1.2,
    C0: float = 1.5e5
) -> Union[float, np.ndarray]:
    """
    Плотность темнового тока насыщения p-n / Schottky диода в микротоковом режиме (Olsen, 1974).
    
    Формула:
        J_0 = C_0 * exp( - E_g / (n * k_B * T / q) )  [А / см2]
        
    Параметры:
        Eg_eV: Ширина запрещенной зоны, эВ
        T_K: Температура полупроводника, К (по умолчанию 300 К)
        ideality_factor: Фактор идеальности диода n (1.2 - 1.5)
        C0: Эмпирический предэкспоненциальный множитель, А/см2 (типично ~10^5 А/см2)
        
    Возвращает:
        Плотность тока J_0 в А/см2 (с защитой от underflow до 10^-35 А/см2).
    """
    is_scalar = np.isscalar(Eg_eV)
    Eg = np.atleast_1d(np.asarray(Eg_eV, dtype=float))

    vt = K_BOLTZMANN_EV * T_K  # k_B * T в эВ (~0.02585 эВ при 300 К)
    exponent = - Eg / (ideality_factor * vt)

    # Защита от переполнения снизу (underflow)
    exponent = np.maximum(exponent, -80.0)
    j0 = C0 * np.exp(exponent)
    j0 = np.maximum(j0, 1e-35)

    if is_scalar:
        return float(j0[0])
    return j0


def open_circuit_voltage(
    Jsc: float,
    J0: float,
    ideality_factor: float = 1.2,
    T_K: float = ROOM_TEMPERATURE_K,
    Eg_eV: Optional[float] = None
) -> float:
    """
    Напряжение холостого хода преобразователя V_oc.
    
    Формула:
        V_oc = (n * k_B * T / q) * ln( J_sc / J_0 + 1 )  [В]
        
    Физическое ограничение:
        V_oc не может превышать контактную разность потенциалов V_bi (V_oc <= E_g - 0.2 В).
    """
    if Jsc <= 0 or J0 <= 0:
        return 0.0

    vt = K_BOLTZMANN_EV * T_K
    ratio = Jsc / J0
    voc = (ideality_factor * vt) * np.log1p(ratio)

    if Eg_eV is not None and Eg_eV > 0.2:
        voc = min(voc, Eg_eV - 0.2)

    return float(max(0.0, voc))


def fill_factor_green(
    Voc: float,
    ideality_factor: float = 1.2,
    T_K: float = ROOM_TEMPERATURE_K
) -> float:
    """
    Коэффициент заполнения вольт-амперной характеристики FF по полуэмпирической
    формуле Мартина Грина (Martin Green, 1982).
    
    Формула:
        v_oc = V_oc / (n * k_B * T / q)
        FF = [ v_oc - ln(v_oc + 0.72) ] / [ v_oc + 1 ]
    """
    vt = ideality_factor * K_BOLTZMANN_EV * T_K
    if vt <= 0 or Voc <= 0.01:
        return 0.25

    voc_norm = Voc / vt
    if voc_norm <= 0.1:
        return 0.25

    ff = (voc_norm - np.log(voc_norm + 0.72)) / (voc_norm + 1.0)
    return float(np.clip(ff, 0.25, 0.89))


def olsen_theoretical_efficiency(
    Eg_eV: Union[float, np.ndarray],
    FF: float = 0.85
) -> Union[float, np.ndarray]:
    """
    Аналитическая инженерная модель теоретического КПД Олсена для массового экспресс-скрининга.
    Учитывает микротоковый режим бетавольтаики и рекомбинационный спад в глубоких диэлектриках.
    
    Формула:
        V_oc(Eg) = Eg * 0.72 * [ 1 - exp(-Eg / 0.75) ] / [ 1 + (Eg / 5.2)^4.5 ]  [В]
        eta_theor = [ V_oc(Eg) / eps_ehp(Eg) ] * FF * 100%  [%]
        
    Параметры:
        Eg_eV: Ширина запрещенной зоны, эВ
        FF: Фактор заполнения ВАХ (по умолчанию 0.85)
        
    Возвращает:
        Теоретический КПД в процентах (%) в диапазоне [0.1%, 23.5%].
    """
    is_scalar = np.isscalar(Eg_eV)
    Eg = np.atleast_1d(np.asarray(Eg_eV, dtype=float))

    eps = ehp_generation_energy(Eg)

    # Модель V_oc Олсена
    term_sat = 1.0 - np.exp(- Eg / 0.75)
    term_doping_limit = 1.0 + (Eg / 5.2) ** 4.5
    voc = Eg * 0.72 * (term_sat / term_doping_limit)

    eta = (voc / eps) * FF * 100.0
    eta = np.clip(eta, 0.1, 23.5)

    if is_scalar:
        return float(eta[0])
    return eta


def betavoltaic_efficiency(
    Jsc_A_cm2: float,
    Voc_V: float,
    FF: float,
    Pin_W_cm2: float
) -> float:
    """
    Реальный КПД бетавольтаической батареи по входной и выходной мощности.
    
    Формула:
        P_max = J_sc * V_oc * FF  [Вт / см2]
        eta = (P_max / P_in) * 100%  [%]
    """
    if Pin_W_cm2 <= 0 or Jsc_A_cm2 <= 0 or Voc_V <= 0 or FF <= 0:
        return 0.0

    p_max = Jsc_A_cm2 * Voc_V * FF
    eta = (p_max / Pin_W_cm2) * 100.0
    return float(eta)
