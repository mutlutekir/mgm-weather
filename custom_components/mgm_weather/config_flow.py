"""MGM Weather için konfigürasyon akışı (UI)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

# const.py dosyanıza CONF_DISTRICT eklediğiniz varsayılmıştır.
from .const import DOMAIN, CONF_CITY, CONF_DISTRICT 

_LOGGER = logging.getLogger(__name__)

# Kullanıcıdan istenecek veri şeması (Şehir ve İlçe)
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CITY, default="Istanbul"): str,
        vol.Optional(CONF_DISTRICT, default=""): str, # İlçe alanı eklendi
    }
)

class MgmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """MGM konfigürasyon akışını yönet."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Kullanıcıdan gelen girdiyi işle."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Kullanıcının girdiği şehir ve ilçe adını al
            city = user_input[CONF_CITY].strip()
            district = user_input.get(CONF_DISTRICT, "").strip()
            
            # Aynı ilin farklı ilçelerini ekleyebilmek için benzersiz ID'yi birleştiriyoruz
            unique_id_str = f"{city}_{district}".lower() if district else city.lower()
            
            await self.async_set_unique_id(unique_id_str)
            self._abort_if_unique_id_configured()

            # Arayüzde görünecek başlığı ayarla (İlçe girilmişse "İl - İlçe" şeklinde gösterir)
            title = f"{city} - {district}" if district else city

            # Başarılı ise kaydet ve entegrasyonu oluştur
            return self.async_create_entry(title=title, data=user_input)

        # Formu göster
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
