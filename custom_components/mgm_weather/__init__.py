"""MGM Hava Durumu Entegrasyonu için kurulum dosyası."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Bu entegrasyonun desteklediği platformlar (Sadece Hava Durumu)
PLATFORMS: list[Platform] = [Platform.WEATHER]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Config entry'den entegrasyonu kur."""
    hass.data.setdefault(DOMAIN, {})
    
    # Platformları (weather.py) yükle
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Entegrasyonu kaldır."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        # Gerekirse veri temizliği yapılabilir
        pass
    return unload_ok
