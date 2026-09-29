"""
Физические модульные тесты и верификация инвариантов расчетного ядра src/physics/.
"""

import pytest
import numpy as np
from src.physics.constants import ISOTOPES, get_isotope
from src.physics.energy_loss import (
    joy_luo_stopping_power,
    feldman_range,
    csda_range_integral,
    optimal_converter_thickness
)
from src.physics.generation import (
    ehp_generation_energy,
    carrier_pairs_per_decay,
    self_absorption_factor
)
from src.physics.radiation_damage import (
    max_recoil_energy,
    displacement_threshold_van_vechten,
    check_radiation_immunity,
    mckinley_feshbach_cross_section
)
from src.physics.electrical import (
    reverse_saturation_current,
    open_circuit_voltage,
    fill_factor_green,
    olsen_theoretical_efficiency
)


def test_silicon_benchmark():
    """Тест контрольных физических инвариантов для кремния (Si)."""
    Eg = 1.12
    rho = 2.33
    A = 28.085
    Z = 14
    ni63 = get_isotope("Ni-63")

    # 1. Правило Кляйна
    eps = ehp_generation_energy(Eg)
    assert eps == pytest.approx(3.686, abs=1e-3)

    # 2. Пробег Фельдмана для средней энергии Ni-63 (17.4 кэВ)
    r_um = feldman_range(ni63.mean_energy_keV, rho)
    assert r_um == pytest.approx(2.58, abs=0.05)

    # 3. Максимальная кинетическая отдача ядра для Ni-63 (E_max = 66.9 кэВ)
    t_max = max_recoil_energy(ni63.max_energy_keV, A)
    assert t_max == pytest.approx(5.57, abs=0.05)

    # Порог смещения кремния ~21 эВ -> отдача 5.57 эВ < 21 эВ -> радиационный иммунитет
    is_immune, _ = check_radiation_immunity(ni63.max_energy_keV, A, Ed_eV=21.0)
    assert is_immune is True


def test_sic_sublattice_recoil_benchmark():
    """Тест радиационной кинематики 4H-SiC с учетом легкой подрешетки углерода."""
    Eg = 3.26
    rho = 3.21
    A_eff = 20.05
    A_min_C = 12.011  # Легкая подрешетка углерода
    ni63 = get_isotope("Ni-63")

    # Энергия пары
    eps = ehp_generation_energy(Eg)
    assert eps == pytest.approx(9.678, abs=1e-3)

    # Отдача по средней массе vs легкой подрешетке
    t_max_eff = max_recoil_energy(ni63.max_energy_keV, A_eff)
    t_max_light = max_recoil_energy(ni63.max_energy_keV, A_min_C)

    # Отдача легкого углерода должна быть существенно выше средней!
    assert t_max_light > t_max_eff
    assert t_max_light == pytest.approx(13.03, abs=0.1)

    # Порог углерода в SiC ~35 эВ -> 13.03 эВ < 35 эВ -> стойкость подтверждена
    assert t_max_light < 35.0


def test_diamond_carbon14_benchmark():
    """Тест эталонного алмазного полупроводника под изотоп C-14."""
    Eg = 5.47
    A = 12.011
    Ed_diamond = 45.0
    c14 = get_isotope("C-14")

    # Энергия пары Кляйна
    eps = ehp_generation_energy(Eg)
    assert eps == pytest.approx(15.866, abs=1e-3)

    # Отдача при ударе электрона с E_max = 156.5 кэВ
    t_max = max_recoil_energy(c14.max_energy_keV, A)
    assert t_max == pytest.approx(32.97, abs=0.1)

    # Алмаз устойчив к C-14: T_max (32.97 эВ) < Ed (45.0 эВ)
    is_immune, _ = check_radiation_immunity(c14.max_energy_keV, A, Ed_diamond)
    assert is_immune is True


def test_joy_luo_stopping_power_invariants():
    """Тест физических инвариантов тормозной способности Джоя-Ло."""
    rho = 2.33
    Z_eff = 14
    A_eff = 28.085

    # Торможение при нулевой энергии строго равно нулю
    sp_zero = joy_luo_stopping_power(0.0, rho, Z_eff, A_eff)
    assert sp_zero == 0.0

    # Торможение строго положительно для диапазона 1 - 100 кэВ
    energies = np.linspace(1.0, 100.0, 50)
    sp = joy_luo_stopping_power(energies, rho, Z_eff, A_eff)
    assert np.all(sp > 0)
    assert np.all(np.isfinite(sp))

    # С ростом энергии при высоких энергиях тормозная способность монотонно падает (1/E)
    sp_10 = joy_luo_stopping_power(10.0, rho, Z_eff, A_eff)
    sp_100 = joy_luo_stopping_power(100.0, rho, Z_eff, A_eff)
    assert sp_10 > sp_100


def test_csda_integral_consistency():
    """Проверка сходимости численного CSDA-интеграла пробега."""
    rho = 2.33
    Z_eff = 14
    A_eff = 28.085

    r_csda = csda_range_integral(17.4, rho, Z_eff, A_eff)
    r_feldman = feldman_range(17.4, rho)

    # Численный CSDA-интеграл и полуэмпирическая формула Фельдмана должны лежать в одном порядке
    assert r_csda > 0
    assert 0.5 * r_feldman <= r_csda <= 2.5 * r_feldman


def test_electrical_olsen_invariants():
    """Проверка инвариантов диодной модели Олсена."""
    # При Eg = 0 возбуждается исключение
    with pytest.raises(ValueError):
        ehp_generation_energy(0.0)

    # КПД Олсена лежит в пределах 0.1 - 23.5%
    gaps = np.linspace(0.5, 6.0, 20)
    etas = olsen_theoretical_efficiency(gaps)
    assert np.all(etas >= 0.1)
    assert np.all(etas <= 23.5)

    # Пик КПД должен приходиться на диапазон 2.0 - 4.5 эВ (широкозонники вроде GaN, SiC, AlN)
    peak_idx = np.argmax(etas)
    optimal_eg = gaps[peak_idx]
    assert 2.0 <= optimal_eg <= 4.5


def test_mckinley_feshbach_threshold():
    """Проверка порога сечения смещения Мак-Кинли-Фешбаха."""
    # Если энергия отдачи T_max <= Ed, сечение строго 0.0
    sigma_zero = mckinley_feshbach_cross_section(E_keV=10.0, Z=14, Ed_eV=25.0, A_amu=28.0)
    assert sigma_zero == 0.0

    # Если энергия электрона огромная (1 МэВ = 1000 кэВ), сечение становится строго положительным
    sigma_high = mckinley_feshbach_cross_section(E_keV=1000.0, Z=14, Ed_eV=21.0, A_amu=28.0)
    assert sigma_high > 0.0
