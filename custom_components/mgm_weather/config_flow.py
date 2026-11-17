"""UI setup for MGM Hava Durumu: ask for a province and an optional district."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from .const import CONF_CITY, CONF_DISTRICT, DOMAIN

LOCATION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CITY): str,
        vol.Optional(CONF_DISTRICT, default=""): str,
    }
)


class MgmWeatherConfigFlow(ConfigFlow, domain=DOMAIN):
    """One config entry per province/district pair."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the location form, then create the entry."""
        errors: dict[str, str] = {}
        if user_input is not None:
            city = user_input[CONF_CITY].strip()
            district = user_input.get(CONF_DISTRICT, "").strip()
            if not city:
                errors[CONF_CITY] = "city_required"
            else:
                # Same unique ID format as earlier releases, so duplicates of
                # existing entries are still detected.
                location_id = f"{city}_{district}" if district else city
                await self.async_set_unique_id(location_id.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{city} - {district}" if district else city,
                    data={CONF_CITY: city, CONF_DISTRICT: district},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(LOCATION_SCHEMA, user_input),
            errors=errors,
        )
