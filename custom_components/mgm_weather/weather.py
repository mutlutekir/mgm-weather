"""Weather entities for MGM Hava Durumu: one daily, one 3-hourly per location."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfPressure, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import MgmConfigEntry, MgmCoordinator
from .hadise import condition_for, fold_name, icon_for, text_for


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MgmConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create the daily and hourly weather entities for a location."""
    coordinator = entry.runtime_data
    async_add_entities([MgmDailyWeather(coordinator), MgmHourlyWeather(coordinator)])


class MgmWeather(SingleCoordinatorWeatherEntity[MgmCoordinator]):
    """Current MGM observation for a location; subclasses add the forecast."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    # Unique ID suffix and display name suffix. The unique ID format
    # (mgm_<place>[_saatlik]) must not change, or users lose their entities.
    unique_id_suffix = ""
    name_suffix = ""

    def __init__(self, coordinator: MgmCoordinator) -> None:
        """Name the entity after its province/district."""
        super().__init__(coordinator)
        city, district = coordinator.city, coordinator.district
        place = f"{city}_{district}" if district else city
        self._attr_unique_id = f"mgm_{fold_name(place)}{self.unique_id_suffix}"
        self._attr_name = " ".join(part for part in (city, district, self.name_suffix) if part)

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data or {}

    @property
    def _code(self) -> str | None:
        return self._data.get("mgm_code")

    def _daytime(self) -> bool:
        if (sun := self.hass.states.get("sun.sun")) is not None:
            return sun.state == "above_horizon"
        return 6 <= dt_util.now().hour < 19

    @property
    def condition(self) -> str | None:
        """Current condition, with clear-night after sunset."""
        return condition_for(self._code, self._daytime()) if self._code else None

    @property
    def icon(self) -> str | None:
        """MDI icon matching the MGM phenomenon code."""
        return icon_for(self._code, self._daytime()) if self._code else None

    @property
    def native_temperature(self) -> float | None:
        """Temperature in °C."""
        return self._data.get("temperature")

    @property
    def native_pressure(self) -> float | None:
        """Pressure in hPa."""
        return self._data.get("pressure")

    @property
    def humidity(self) -> float | None:
        """Relative humidity in %."""
        return self._data.get("humidity")

    @property
    def native_wind_speed(self) -> float | None:
        """Wind speed in km/h."""
        return self._data.get("wind_speed")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """MGM's own code and its Turkish description."""
        if not self.coordinator.data:
            return None
        return {
            "detayli_hadise": text_for(self._code) if self._code else "Bilinmiyor",
            "mgm_hadise_kodu": self._code,
        }


class MgmDailyWeather(MgmWeather):
    """Current conditions plus the 5-day forecast."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
    name_suffix = "Hava Durumu"

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        return self._data.get("forecast") if self.coordinator.data else None


class MgmHourlyWeather(MgmWeather):
    """Current conditions plus the 3-hourly forecast."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY
    unique_id_suffix = "_saatlik"
    name_suffix = "Saatlik"

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        return self._data.get("forecast_hourly") if self.coordinator.data else None
