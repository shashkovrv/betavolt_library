"""
Физико-математический пакет для расчета характеристик бетавольтаических преобразователей.
"""

from src.physics.constants import (
    Q_ELECTRON,
    K_BOLTZMANN,
    K_BOLTZMANN_EV,
    SPEED_OF_LIGHT,
    ELECTRON_REST_ENERGY_KEV,
    ATOMIC_MASS_UNIT_KEV,
    ROOM_TEMPERATURE_K,
    ISOTOPES,
    IsotopeProperties,
    get_isotope
)

from src.physics.energy_loss import (
    joy_luo_stopping_power,
    feldman_range,
    csda_range_integral,
    optimal_converter_thickness
)

from src.physics.generation import (
    ehp_generation_energy,
    carrier_pairs_per_decay,
    self_absorption_factor,
    generation_current_density
)

from src.physics.radiation_damage import (
    max_recoil_energy,
    displacement_threshold_van_vechten,
    check_radiation_immunity,
    radiation_hardness_score,
    mckinley_feshbach_cross_section
)

from src.physics.electrical import (
    reverse_saturation_current,
    open_circuit_voltage,
    fill_factor_green,
    olsen_theoretical_efficiency,
    betavoltaic_efficiency
)

__all__ = [
    "Q_ELECTRON",
    "K_BOLTZMANN",
    "K_BOLTZMANN_EV",
    "SPEED_OF_LIGHT",
    "ELECTRON_REST_ENERGY_KEV",
    "ATOMIC_MASS_UNIT_KEV",
    "ROOM_TEMPERATURE_K",
    "ISOTOPES",
    "IsotopeProperties",
    "get_isotope",
    "joy_luo_stopping_power",
    "feldman_range",
    "csda_range_integral",
    "optimal_converter_thickness",
    "ehp_generation_energy",
    "carrier_pairs_per_decay",
    "self_absorption_factor",
    "generation_current_density",
    "max_recoil_energy",
    "displacement_threshold_van_vechten",
    "check_radiation_immunity",
    "radiation_hardness_score",
    "mckinley_feshbach_cross_section",
    "reverse_saturation_current",
    "open_circuit_voltage",
    "fill_factor_green",
    "olsen_theoretical_efficiency",
    "betavoltaic_efficiency",
]
