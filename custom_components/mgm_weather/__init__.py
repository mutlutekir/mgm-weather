"""MGM Hava Durumu Entegrasyonu için kurulum dosyası."""
from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import DOMAIN, CONF_CITY, CONF_DISTRICT

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.WEATHER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Config entry'den entegrasyonu kur."""
    from .weather import MGMDataUpdateCoordinator  # ← burada import ediliyor

    hass.data.setdefault(DOMAIN, {})
    city = entry.data.get(CONF_CITY, "")
    district = entry.data.get(CONF_DISTRICT, "")
    coordinator = MGMDataUpdateCoordinator(hass, city, district)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        from homeassistant.exceptions import ConfigEntryNotReady
        raise ConfigEntryNotReady(f"MGM verisine ulaşılamadı: {err}") from err
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kaldır."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
