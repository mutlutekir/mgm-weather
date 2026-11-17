"""MGM Hava Durumu: weather from the Turkish State Meteorological Service."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import MgmConfigEntry, MgmCoordinator

PLATFORMS = [Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: MgmConfigEntry) -> bool:
    """Start polling MGM for this location and create its weather entities."""
    coordinator = MgmCoordinator(hass, entry)
    # Raises ConfigEntryNotReady when MGM can't be reached, so HA retries later.
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MgmConfigEntry) -> bool:
    """Remove the weather entities for this location."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
