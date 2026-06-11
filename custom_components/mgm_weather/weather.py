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
from homeassistant.const import (
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, SCAN_INTERVAL_SECONDS, CONF_CITY, CONF_DISTRICT

_LOGGER = logging.getLogger(__name__)

def clear_tr_characters(text):
    if not text: return ""
    replacements = {"ı": "i", "ü": "u", "ğ": "g", "ş": "s", "ö": "o", "ç": "c", "İ": "i", "Ü": "u", "Ğ": "g", "Ş": "s", "Ö": "o", "Ç": "c", "I": "i"}
    for tr, eng in replacements.items(): text = text.replace(tr, eng)
    return text.lower()

def map_mgm_condition(mgm_code, is_day=True):
    mapping = {
        "A": "sunny", "SCK": "sunny", "SGK": "sunny", 
        "AB": "partlycloudy", "PB": "partlycloudy",
        "CB": "cloudy", 
        "HY": "rainy", "HSY": "rainy", "YYSY": "rainy", "MSY": "rainy", "Y": "rainy", "SY": "rainy",
        "KY": "pouring", "KSY": "pouring", "KKY": "snowy-rainy", 
        "HK": "snowy", "HKY": "snowy", "K": "snowy", "YK": "snowy", "YKY": "snowy",
        "SIS": "fog", "PUS": "fog", "DMN": "fog", "DUMAN": "fog", "KF": "fog",
        "D": "hail", "DY": "hail",
        "GSY": "lightning-rainy", "KGY": "lightning-rainy", "KGSY": "lightning-rainy", 
        "R": "windy", "GKR": "windy", "KKR": "windy", "FIRT": "windy"
    }
    cond = mapping.get(mgm_code, "partlycloudy")
    if not is_day and cond == "sunny":
        return "clear-night"
    return cond

def get_mgm_icon(mgm_code, is_day=True):
    mapping = {
        "A": "mdi:weather-sunny", "SCK": "mdi:weather-sunny", "SGK": "mdi:weather-sunny", 
        "AB": "mdi:weather-partly-cloudy", "PB": "mdi:weather-partly-cloudy",
        "CB": "mdi:weather-cloudy", 
        "HY": "mdi:weather-partly-rainy", 
        "HSY": "mdi:weather-rainy", "YYSY": "mdi:weather-rainy", "MSY": "mdi:weather-rainy",
        "Y": "mdi:weather-rainy", "SY": "mdi:weather-rainy", 
        "KY": "mdi:weather-pouring", "KSY": "mdi:weather-pouring", 
        "KKY": "mdi:weather-partly-snowy-rainy", "HKY": "mdi:weather-partly-snowy-rainy",
        "YKY": "mdi:weather-snowy-rainy",
        "HK": "mdi:weather-partly-snowy", "K": "mdi:weather-snowy", "YK": "mdi:weather-snowy-heavy",
        "SIS": "mdi:weather-fog", 
        "PUS": "mdi:weather-hazy", "DMN": "mdi:weather-hazy", "DUMAN": "mdi:weather-hazy", 
        "KF": "mdi:weather-dust",
        "D": "mdi:weather-hail", "DY": "mdi:weather-hail",
        "GSY": "mdi:weather-lightning-rainy", "KGY": "mdi:weather-lightning-rainy", "KGSY": "mdi:weather-lightning-rainy",
        "R": "mdi:weather-windy-variant", 
        "GKR": "mdi:weather-windy", "KKR": "mdi:weather-windy", "FIRT": "mdi:weather-hurricane-outline"
    }
    icon = mapping.get(mgm_code, "mdi:weather-partly-cloudy")
    if not is_day:
        if icon == "mdi:weather-sunny": return "mdi:weather-night"
        if icon == "mdi:weather-partly-cloudy": return "mdi:weather-night-partly-cloudy"
    return icon

def get_mgm_text(mgm_code):
    mapping = {
        "A": "Açık", "SCK": "Sıcak", "SGK": "Soğuk",
        "AB": "Az Bulutlu", "PB": "Parçalı Bulutlu", "CB": "Çok Bulutlu",
        "HY": "Hafif Yağmurlu", "HSY": "Hafif Sağanak Yağışlı", "YYSY": "Yer Yer Sağanak Yağışlı", "MSY": "Mevzi Sağanak Yağışlı",
        "Y": "Yağmurlu", "SY": "Sağanak Yağışlı", "KY": "Kuvvetli Yağmurlu", "KSY": "Kuvvetli Sağanak Yağışlı",
        "GSY": "Gökgürültülü Sağanak Yağışlı", "KGY": "Kuvvetli Gökgürültülü Sağanak Yağışlı", "KGSY": "Kuvvetli Gökgürültülü Sağanak Yağışlı",
        "KKY": "Karla Karışık Yağmurlu", "HKY": "Hafif Karla Karışık Yağmurlu", "YKY": "Yoğun Karla Karışık Yağmurlu",
        "HK": "Hafif Kar Yağışlı", "K": "Kar Yağışlı", "YK": "Yoğun Kar Yağışlı",
        "SIS": "Sisli", "PUS": "Puslu", "DMN": "Dumanlı", "DUMAN": "Dumanlı",
        "KF": "Kum Taşınımı",
        "D": "Dolu", "DY": "Dolu Yağışlı",
        "R": "Rüzgarlı", "GKR": "Kuvvetli Rüzgarlı", "KKR": "Kuvvetli Rüzgarlı", "FIRT": "Fırtına"
    }
    return mapping.get(mgm_code, "Bilinmiyor")

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    city = entry.data.get(CONF_CITY, "Istanbul")
    district = entry.data.get(CONF_DISTRICT, "")
    async_add_entities([
        MGMWeatherEntity(coordinator, city, district, "daily"),
        MGMWeatherEntity(coordinator, city, district, "hourly"),
    ])

class MGMDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, city, district):
        super().__init__(hass, _LOGGER, name=f"MGM Weather {city} {district}", update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS))
        self.city, self.district = city, district
        self._station_cache = None 
        self._last_success_time = None # 6 Saatlik hafıza için eklendi

    async def _async_update_data(self):
        headers = {
            "Host": "servis.mgm.gov.tr",
            "Origin": "https://www.mgm.gov.tr",
            "Referer": "https://www.mgm.gov.tr/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }
        try:
            async with async_timeout.timeout(25):
                session = async_get_clientsession(self.hass)
                from urllib.parse import quote

                if not self._station_cache:
                    async with session.get(f"https://servis.mgm.gov.tr/web/merkezler/ililcesi?il={quote(self.city)}", headers=headers) as r:
                        il_istasyonlari = await r.json()

                    ilce_istasyon = None
                    if self.district:
                        hedef_ilce = clear_tr_characters(self.district)
                        for ist in il_istasyonlari:
                            if clear_tr_characters(ist.get("ilce", "")) == hedef_ilce:
                                ilce_istasyon = ist
                                break

                    il_merkezi = next((i for i in il_istasyonlari if i.get("oncelik") == 1), il_istasyonlari[0] if il_istasyonlari else None)
                    if not il_merkezi:
                        raise ValueError("Il merkezi bulunamadi.")

                    self._station_cache = {
                        "birincil": ilce_istasyon or il_merkezi,
                        "il_merkezi": il_merkezi
                    }

                birincil = self._station_cache["birincil"]
                il_merkezi = self._station_cache["il_merkezi"]

                async def fetch_json(url):
                    async with session.get(url, headers=headers) as r:
                        return await r.json()

                async def get_with_fallback(url_fn, id_birincil, id_fallback):
                    if id_birincil:
                        data = await fetch_json(url_fn(id_birincil))
                        if data: return data, id_birincil
                    if id_fallback and id_fallback != id_birincil:
                        data = await fetch_json(url_fn(id_fallback))
                        if data: return data, id_fallback
                    return None, None

                birincil_sd_ids = list(dict.fromkeys(filter(None, [birincil.get("sondurumIstNo"), birincil.get("merkezId")])))
                fallback_sd_ids = list(dict.fromkeys(filter(None, [il_merkezi.get("sondurumIstNo"), il_merkezi.get("merkezId")])))

                sd = None
                for try_id in birincil_sd_ids + [fid for fid in fallback_sd_ids if fid not in birincil_sd_ids]:
                    raw = await fetch_json(f"https://servis.mgm.gov.tr/web/sondurumlar?merkezid={try_id}")
                    if raw:
                        sd = raw[0]
                        break

                if not sd: raise ValueError("sondurumlar alinamadi.")

                td_list, _ = await get_with_fallback(lambda m: f"https://servis.mgm.gov.tr/web/tahminler/gunluk?istno={m}", birincil.get("merkezId"), il_merkezi.get("merkezId"))
                s_raw, _ = await get_with_fallback(lambda s: f"https://servis.mgm.gov.tr/web/tahminler/saatlik?istno={s}", birincil.get("saatlikTahminIstNo"), il_merkezi.get("saatlikTahminIstNo"))

                res = {
                    "condition": map_mgm_condition(sd.get("hadiseKodu")),
                    "mgm_code": sd.get("hadiseKodu"),
                    "temperature": sd.get("sicaklik"),
                    "pressure": sd.get("aktuelBasinc"),
                    "humidity": sd.get("nem"),
                    "wind_speed": sd.get("ruzgarHiz"),
                    "forecast": [],
                    "forecast_hourly": [],
                }

                if td_list:
                    td = td_list[0]
                    for i in range(1, 6):
                        res["forecast"].append({
                            "datetime": (
                                datetime.now() + timedelta(days=i - 1)
                            ).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
                            "temperature": td.get(f"enYuksekGun{i}"),
                            "templow": td.get(f"enDusukGun{i}"),
                            "condition": map_mgm_condition(td.get(f"hadiseGun{i}"), True),
                            "precipitation": 0,
                        })

                if s_raw and "tahmin" in s_raw[0]:
                    for st in s_raw[0]["tahmin"]:
                        tarih_str = st.get("tarih").replace(".000Z", "+00:00")
                        try:
                            hour = int(tarih_str[11:13])
                            is_day_forecast = 6 <= hour < 19
                        except Exception:
                            is_day_forecast = True
                            
                        res["forecast_hourly"].append({
                            "datetime": tarih_str,
                            "temperature": st.get("sicaklik"),
                            "condition": map_mgm_condition(st.get("hadise"), is_day_forecast),
                            "humidity": st.get("nem"),
                            "wind_speed": st.get("ruzgarHizi"),
                            "precipitation": 0,
                        })

                # Veri başarıyla çekildiyse saati kaydet
                self._last_success_time = datetime.now()
                return res

        except Exception as e:
            # HATA DURUMU MANTIĞI: Eğer hafızada veri varsa ve 6 saat geçmediyse, eski veriyi kullan ve çökme!
            if self.data and self._last_success_time:
                time_since_last_success = datetime.now() - self._last_success_time
                if time_since_last_success < timedelta(hours=6):
                    _LOGGER.debug("MGM baglantisi kurulamadi (%s). 6 saat dolmadigi icin eski veri gosteriliyor.", e)
                    return self.data
                    
            # 6 saati geçtiyse veya sistem daha hiç veri alamadan kilitlendiyse, o zaman hatayı bas
            raise UpdateFailed(f"MGM Hatasi (En az 6 saattir guncel veri alinamiyor): {e}")


class MGMWeatherEntity(CoordinatorEntity, WeatherEntity):
    _attr_has_entity_name = True
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator, city, district, mode):
        super().__init__(coordinator)
        self._mode = mode
        u_id = clear_tr_characters(f"{city}_{district}" if district else city)
        if mode == "daily":
            self._attr_unique_id = f"mgm_{u_id}"
            self._attr_name = f"{city} {district} Hava Durumu".strip()
            self._attr_supported_features = WeatherEntityFeature.FORECAST_DAILY
        else:
            self._attr_unique_id = f"mgm_{u_id}_saatlik"
            self._attr_name = f"{city} {district} Saatlik".strip()
            self._attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY

    @property
    def is_daytime(self) -> bool:
        sun_state = self.hass.states.get("sun.sun")
        if sun_state:
            return sun_state.state == "above_horizon"
        return 6 <= datetime.now().hour < 19

    @property
    def icon(self): 
        if not self.coordinator.data: return None
        mgm_code = self.coordinator.data.get("mgm_code")
        return get_mgm_icon(mgm_code, self.is_daytime) if mgm_code else None

    @property
    def condition(self): 
        if not self.coordinator.data: return None
        mgm_code = self.coordinator.data.get("mgm_code")
        return map_mgm_condition(mgm_code, self.is_daytime) if mgm_code else None

    @property
    def native_temperature(self): 
        return self.coordinator.data.get("temperature") if self.coordinator.data else None
    
    @property
    def native_pressure(self): 
        return self.coordinator.data.get("pressure") if self.coordinator.data else None
    
    @property
    def humidity(self): 
        return self.coordinator.data.get("humidity") if self.coordinator.data else None
    
    @property
    def native_wind_speed(self): 
        return self.coordinator.data.get("wind_speed") if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        if not self.coordinator.data: return None
        mgm_code = self.coordinator.data.get("mgm_code")
        return {
            "detayli_hadise": get_mgm_text(mgm_code) if mgm_code else "Bilinmiyor",
            "mgm_hadise_kodu": mgm_code,
        }

    async def async_forecast_daily(self) -> list[Forecast] | None:
        if not self.coordinator.data: return None
        return self.coordinator.data.get("forecast") if self._mode == "daily" else None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        if not self.coordinator.data: return None
        return self.coordinator.data.get("forecast_hourly") if self._mode == "hourly" else None

    @property
    def forecast(self) -> list[Forecast] | None:
        if not self.coordinator.data: return None
        if self._mode == "daily": return self.coordinator.data.get("forecast")
        return self.coordinator.data.get("forecast_hourly")
