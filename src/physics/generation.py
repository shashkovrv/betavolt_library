"""
Модуль расчета радиационной генерации пар электрон-дырка и выходного бета-тока.
"""

from typing import Union
import numpy as np
from src.physics.constants import (
    Q_ELECTRON,
    KLEIN_COEFF_A,
    KLEIN_CONST_B_EV
)


def ehp_generation_energy(Eg_eV: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    """
    Средняя энергия образования электронно-дырочной пары по правилу Кляйна (Claude Klein, 1968).
    
    Формула:
        eps_ehp = 2.8 * E_g + 0.55  [эВ]
        
    Физический смысл:
        - Коэффициент 2.8 отражает распределение кинетической энергии между электроном
          и дыркой с сохранением квазиимпульса решетки;
        - Свободный член 0.55 эВ аппроксимирует оптические потери на возбуждение фононов.
        
    Параметры:
        Eg_eV: Ширина запрещенной зоны полупроводника, эВ
        
    Возвращает:
        Энергия образования пары в эВ.
    """
    is_scalar = np.isscalar(Eg_eV)
    Eg = np.atleast_1d(np.asarray(Eg_eV, dtype=float))

    if np.any(Eg <= 0):
        raise ValueError("Ширина запрещенной зоны должна быть строго больше нуля (не металл)!")

    eps = KLEIN_COEFF_A * Eg + KLEIN_CONST_B_EV
    
    if is_scalar:
        return float(eps[0])
    return eps


def carrier_pairs_per_decay(
    E_keV: Union[float, np.ndarray],
    Eg_eV: float
) -> Union[float, np.ndarray]:
    """
    Число пар электрон-дырка, генерируемых одним бета-электроном с кинетической энергией E_keV.
    
    Формула:
        N_pairs = (E_keV * 1000) / eps_ehp(E_g)
    """
    eps = ehp_generation_energy(Eg_eV)
    return (np.asarray(E_keV) * 1000.0) / eps


def self_absorption_factor(
    d_cm: float,
    rho_source: float,
    E_max_keV: float
) -> float:
    """
    Коэффициент выхода бета-частиц с учетом самопоглощения в радиоизотопном слое источника
    (Модель МИСиС / ТИСНУМ, Краснов, Леготин, 2020).
    
    Формула:
        eta_self = (1 - exp(-mu * d)) / (mu * d)
        где mu = 0.017 * (E_max / 1000)^(-1.43) * rho_source  [см^-1]
        
    Параметры:
        d_cm: Толщина радиоактивного слоя, см
        rho_source: Плотность материала источника, г/см3
        E_max_keV: Граничная энергия спектра бета-распада, кэВ
        
    Возвращает:
        Доля частиц, покинувших слой источника без поглощения (0 < eta_self <= 1.0).
    """
    if d_cm <= 0 or rho_source <= 0 or E_max_keV <= 0:
        return 1.0

    # Линейный коэффициент самопоглощения (E_max переводится в МэВ)
    E_max_MeV = E_max_keV / 1000.0
    mu = 0.017 * (E_max_MeV ** -1.43) * rho_source

    mu_d = mu * d_cm
    if mu_d < 1e-6:
        # Предел при mu*d -> 0 по правилу Лопиталя
        return 1.0 - 0.5 * mu_d

    return float((1.0 - np.exp(-mu_d)) / mu_d)


def generation_current_density(
    flux_beta: float,
    E_mean_keV: float,
    Eg_eV: float,
    collection_efficiency: float = 1.0
) -> float:
    """
    Предельная плотность тока короткого замыкания (генерационного тока), А/см2.
    
    Формула:
        J_sc = q * flux_beta * N_pairs(E_mean) * eta_coll
        
    Параметры:
        flux_beta: Плотность потока бета-частиц, частиц / (см2 * с)
        E_mean_keV: Средняя кинетическая энергия бета-частиц спектра, кэВ
        Eg_eV: Ширина запрещенной зоны, эВ
        collection_efficiency: Коэффициент собирания носителей ОПЗ (0 <= eta_coll <= 1.0)
        
    Возвращает:
        Плотность тока в А/см2.
    """
    n_pairs = carrier_pairs_per_decay(E_mean_keV, Eg_eV)
    j_sc = Q_ELECTRON * flux_beta * n_pairs * collection_efficiency
    return float(j_sc)
