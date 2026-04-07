"""MGM Hava Durumu platformu."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
import aiohttp
import async_timeout

from homeassistant.components.weather import (
    WeatherEntity,
    WeatherEntityFeature,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

# CONF_DISTRICT eklendi
from .const import DOMAIN, SCAN_INTERVAL_SECONDS, CONF_CITY, CONF_DISTRICT

_LOGGER = logging.getLogger(__name__)

def clear_tr_characters(text):
    """Türkçe karakterleri hatasız temizle."""
    if not text:
        return ""
    replacements = {
        "ı": "i", "ü": "u", "ğ": "g", "ş": "s", "ö": "o", "ç": "c",
        "İ": "i", "Ü": "u", "Ğ": "g", "Ş": "s", "Ö": "o", "Ç": "c",
        "I": "i"
    }
    for tr, eng in replacements.items():
        text = text.replace(tr, eng)
    return text.lower()

def map_mgm_condition(mgm_code):
    """MGM hava durumu kodlarını Home Assistant ikonlarına çevir."""
    mapping = {
        "A": "sunny", "AB": "partlycloudy", "PB": "partlycloudy", "CB": "cloudy",
        "HY": "rainy", "SY": "rainy", "KSY": "pouring", "Y": "rainy", "KY": "pouring",
        "KKY": "snowy-rainy", "HKY": "snowy", "K": "snowy", "YKY": "snowy",
        "SIS": "fog", "PUS": "fog", "D": "fog", "GSY": "lightning-rainy",
        "KGY": "lightning-rainy", "DY": "hail", "R": "windy"
    }
    return mapping.get(mgm_code, "exceptional")

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Config entry kullanarak hava durumu entity'sini ekle."""
    city = entry.data.get(CONF_CITY, "Istanbul")
    district = entry.data.get(CONF_DISTRICT, "")
    
    coordinator = MGMDataUpdateCoordinator(hass, city, district)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([MGMWeatherEntity(coordinator, city, district)])


class MGMDataUpdateCoordinator(DataUpdateCoordinator):
    """MGM verilerini periyodik olarak çeken sınıf."""

    def __init__(self, hass: HomeAssistant, city: str, district: str) -> None:
        """Coordinator'ı başlat."""
        name = f"MGM Weather {city} {district}".strip()
        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.city = city
        self.district = district

    async def _async_update_data(self):
        """MGM API'dan doğrudan il/ilçe URL'si ile veriyi çek."""
        headers = {
            "Host": "servis.mgm.gov.tr",
            "Origin": "https://www.mgm.gov.tr",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        try:
            async with async_timeout.timeout(15):
                async with aiohttp.ClientSession() as session:
                    
                    # 1. İl ve İlçe isimlerini API standartlarına göre hazırla
                    il_adi = clear_tr_characters(self.city)
                    aranan_ilce = clear_tr_characters(self.district)
                    
                    # DOĞRUDAN API'DEN İLÇEYİ ÇAĞIRAN YENİ MANTIK
                    if aranan_ilce:
                        merkez_url = f"https://servis.mgm.gov.tr/web/merkezler?il={il_adi}&ilce={aranan_ilce}"
                    else:
                        merkez_url = f"https://servis.mgm.gov.tr/web/merkezler?il={il_adi}"

                    async with session.get(merkez_url, headers=headers) as resp:
                        if resp.status != 200:
                            raise UpdateFailed(f"API Hatası (Merkezler): {resp.status}")
                        merkezler = await resp.json()

                    # Artık döngüye gerek yok, API direkt istediğimiz tek istasyonu gönderiyor
                    merkez_id = None
                    if merkezler:
                        merkez_id = merkezler[0].get("merkezId")

                    if not merkez_id:
                        raise UpdateFailed(f"İstasyon bulunamadı. Lütfen MGM'de ilçe adının '{self.district}' olarak geçtiğinden emin olun.")

                    # 2. Son Durum Verisini Çek
                    sondurum_url = f"https://servis.mgm.gov.tr/web/sondurumlar?merkezid={merkez_id}"
                    async with session.get(sondurum_url, headers=headers) as resp:
                        sondurum = await resp.json()

                    if not sondurum:
                        raise UpdateFailed("Son durum verisi boş döndü (İstasyon anlık olarak çevrimdışı olabilir).")
                    sd = sondurum[0]

                    # 3. Günlük Tahminleri Çek
                    tahmin_url = f"https://servis.mgm.gov.tr/web/tahminler/gunluk?istno={merkez_id}"
                    async with session.get(tahmin_url, headers=headers) as resp:
                        tahminler = await resp.json()

                    # 4. Veriyi HA formatına çevir
                    result = {
                        "condition": map_mgm_condition(sd.get("hadiseKodu")),
                        "temperature": sd.get("sicaklik"),
                        "pressure": sd.get("aktuelBasinc"),
                        "humidity": sd.get("nem"),
                        "wind_speed": sd.get("ruzgarHiz"),
                        "forecast": []
                    }

                    if tahminler:
                        td = tahminler[0]
                        today = datetime.now()
                        for i in range(1, 6):
                            result["forecast"].append({
                                "datetime": (today + timedelta(days=i)).isoformat(),
                                "temperature": td.get(f"enYuksekGun{i}"),
                                "templow": td.get(f"enDusukGun{i}"),
                                "condition": map_mgm_condition(td.get(f"hadiseGun{i}")),
                                "humidity": td.get(f"enYuksekNemGun{i}")
                            })

                    return result

        except Exception as err:
            _LOGGER.error(f"MGM Veri Çekme Hatası: {err}")
            raise UpdateFailed(f"MGM bağlantı hatası: {err}")


class MGMWeatherEntity(CoordinatorEntity, WeatherEntity):
    """MGM Hava Durumu Entity'si."""

    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, coordinator: MGMDataUpdateCoordinator, city: str, district: str) -> None:
        """Entity'yi başlat."""
        super().__init__(coordinator)
        self._city = city
        self._district = district
        
        unique_id_base = f"{city}_{district}" if district else city
        self._attr_unique_id = f"mgm_{unique_id_base.lower()}"
        
        # Arayüzde kesin olarak görünmesi için isim atıyoruz
        isim = f"{city} {district}".strip()
        self._attr_name = f"{isim} Hava Durumu"

    @property
    def condition(self) -> str | None:
        return self.coordinator.data.get("condition")

    @property
    def native_temperature(self) -> float | None:
        return self.coordinator.data.get("temperature")

    @property
    def native_pressure(self) -> float | None:
        return self.coordinator.data.get("pressure")

    @property
    def humidity(self) -> float | None:
        return self.coordinator.data.get("humidity")

    @property
    def native_wind_speed(self) -> float | None:
        return self.coordinator.data.get("wind_speed")

    @property
    def forecast(self) -> list[Forecast] | None:
        return self.coordinator.data.get("forecast")

    async def async_forecast_daily(self) -> list[Forecast] | None:
        return self.coordinator.data.get("forecast")
