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

from .const import DOMAIN, SCAN_INTERVAL_SECONDS, CONF_CITY, CONF_DISTRICT

_LOGGER = logging.getLogger(__name__)

def clear_tr_characters(text):
    if not text: return ""
    replacements = {"ı": "i", "ü": "u", "ğ": "g", "ş": "s", "ö": "o", "ç": "c", "İ": "i", "Ü": "u", "Ğ": "g", "Ş": "s", "Ö": "o", "Ç": "c", "I": "i"}
    for tr, eng in replacements.items(): text = text.replace(tr, eng)
    return text.lower()

def map_mgm_condition(mgm_code, is_day=True):
    """MGM hava durumu kodlarını Home Assistant STANDART durumlarına çevir."""
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
    # Gece modunda, hava güneşli (sunny) ise bunu açık geceye (clear-night) çevir.
    if not is_day and cond == "sunny":
        return "clear-night"
    return cond

def get_mgm_icon(mgm_code, is_day=True):
    """MGM kodlarını senin belirlediğin MDI ikonlarıyla eşleştirir (Gece/Gündüz duyarlı)."""
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
    
    # Gece ikon dönüşümleri
    if not is_day:
        if icon == "mdi:weather-sunny":
            return "mdi:weather-night"
        if icon == "mdi:weather-partly-cloudy":
            return "mdi:weather-night-partly-cloudy"
            
    return icon

def get_mgm_text(mgm_code):
    """Arayüzde Kum Taşınımı vb. detayların Türkçe yazması için sözlük."""
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
    # DOKUNULMADI: Senin çalışan kurulum yöntemin korundu.
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

    async def _async_update_data(self):
        headers = {
            "Host": "servis.mgm.gov.tr",
            "Origin": "https://www.mgm.gov.tr",
            "Referer": "https://www.mgm.gov.tr/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "tr-TR,tr;q=0.9",
        }
        try:
            async with async_timeout.timeout(25):
                async with aiohttp.ClientSession() as session:
                    from urllib.parse import quote

                    # ── 1. İlin tüm istasyonlarını çek ──────────────────────────
                    async with session.get(
                        f"https://servis.mgm.gov.tr/web/merkezler/ililcesi?il={quote(self.city)}",
                        headers=headers,
                    ) as r:
                        il_istasyonlari = await r.json()

                    # ── 2. İlçe istasyonunu bul ──────────────────────────────────
                    ilce_istasyon = None
                    if self.district:
                        hedef_ilce = clear_tr_characters(self.district)
                        for ist in il_istasyonlari:
                            if clear_tr_characters(ist.get("ilce", "")) == hedef_ilce:
                                ilce_istasyon = ist
                                break
                        if not ilce_istasyon:
                            _LOGGER.warning(
                                "'%s' ilcesi bulunamadi, il merkezi fallback kullanilacak.",
                                self.district,
                            )

                    # ── 3. İl merkezi istasyonunu bul (oncelik=1) ────────────────
                    il_merkezi = next(
                        (i for i in il_istasyonlari if i.get("oncelik") == 1),
                        il_istasyonlari[0] if il_istasyonlari else None,
                    )

                    if not il_merkezi:
                        raise ValueError("Il merkezi bulunamadi.")

                    birincil = ilce_istasyon or il_merkezi

                    _LOGGER.debug(
                        "MGM DEBUG: birincil=%s/%s  il_merkezi=%s/%s",
                        birincil.get("il"), birincil.get("ilce"),
                        il_merkezi.get("il"), il_merkezi.get("ilce"),
                    )

                    # ── Yardımcı: fallback'li JSON çekici ───────────────────────
                    async def fetch_json(url):
                        async with session.get(url, headers=headers) as r:
                            return await r.json()

                    async def get_with_fallback(url_fn, id_birincil, id_fallback):
                        if id_birincil:
                            data = await fetch_json(url_fn(id_birincil))
                            if data:
                                return data, id_birincil
                        if id_fallback and id_fallback != id_birincil:
                            data = await fetch_json(url_fn(id_fallback))
                            if data:
                                _LOGGER.info(
                                    "Fallback kullanildi: %s -> %s", id_birincil, id_fallback
                                )
                                return data, id_fallback
                        return None, None

                    # ── 4. sondurumlar ───────────────────────────────────────────
                    def sd_url(mid): return f"https://servis.mgm.gov.tr/web/sondurumlar?merkezid={mid}"

                    birincil_sd_ids = list(dict.fromkeys(filter(None, [
                        birincil.get("sondurumIstNo"),
                        birincil.get("merkezId"),
                    ])))
                    fallback_sd_ids = list(dict.fromkeys(filter(None, [
                        il_merkezi.get("sondurumIstNo"),
                        il_merkezi.get("merkezId"),
                    ])))

                    sd = None
                    for try_id in birincil_sd_ids + [
                        fid for fid in fallback_sd_ids if fid not in birincil_sd_ids
                    ]:
                        raw = await fetch_json(sd_url(try_id))
                        if raw:
                            sd = raw[0]
                            _LOGGER.debug("sondurumlar OK: id=%s", try_id)
                            break
                        _LOGGER.warning("sondurumlar bos: id=%s", try_id)

                    if not sd:
                        raise ValueError("sondurumlar hic bir id ile alinamadi.")

                    # ── 5. Günlük tahmin ─────────────────────────────────────────
                    def gunluk_url(mid): return f"https://servis.mgm.gov.tr/web/tahminler/gunluk?istno={mid}"

                    td_list, _ = await get_with_fallback(
                        gunluk_url,
                        birincil.get("merkezId"),
                        il_merkezi.get("merkezId"),
                    )

                    # ── 6. Saatlik tahmin ────────────────────────────────────────
                    def saatlik_url(sid): return f"https://servis.mgm.gov.tr/web/tahminler/saatlik?istno={sid}"

                    s_raw, _ = await get_with_fallback(
                        saatlik_url,
                        birincil.get("saatlikTahminIstNo"),
                        il_merkezi.get("saatlikTahminIstNo"),
                    )

                    # ── 7. Sonuç nesnesini oluştur ───────────────────────────────
                    res = {
                        "condition": map_mgm_condition(sd.get("hadiseKodu")), # Geçici atanıyor, entity'de gece kontrolüyle ezilecek
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
                                "condition": map_mgm_condition(td.get(f"hadiseGun{i}"), True), # Günlük tahminler hep gündüz sayılır
                                "precipitation": 0,
                            })

                    if s_raw and "tahmin" in s_raw[0]:
                        for st in s_raw[0]["tahmin"]:
                            tarih_str = st.get("tarih").replace(".000Z", "+00:00")
                            try:
                                # Saatlik tahminde ilgili saati ayıklayıp gece/gündüz ayrımı yapıyoruz
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

                    return res

        except Exception as e:
            raise UpdateFailed(f"MGM Hatasi: {e}")


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
        """Home Assistant'ın yerel güneş takip sistemini kontrol eder."""
        sun_state = self.hass.states.get("sun.sun")
        if sun_state:
            return sun_state.state == "above_horizon"
        return 6 <= datetime.now().hour < 19

    @property
    def icon(self): 
        mgm_code = self.coordinator.data.get("mgm_code")
        return get_mgm_icon(mgm_code, self.is_daytime) if mgm_code else None

    @property
    def condition(self): 
        mgm_code = self.coordinator.data.get("mgm_code")
        return map_mgm_condition(mgm_code, self.is_daytime) if mgm_code else None

    @property
    def native_temperature(self): return self.coordinator.data.get("temperature")
    @property
    def native_pressure(self): return self.coordinator.data.get("pressure")
    @property
    def humidity(self): return self.coordinator.data.get("humidity")
    @property
    def native_wind_speed(self): return self.coordinator.data.get("wind_speed")

    @property
    def extra_state_attributes(self) -> dict[str, any] | None:
        """Karta detayli_hadise ve mgm_hadise_kodu özelliklerini ekler."""
        mgm_code = self.coordinator.data.get("mgm_code")
        return {
            "detayli_hadise": get_mgm_text(mgm_code) if mgm_code else "Bilinmiyor",
            "mgm_hadise_kodu": mgm_code,
        }

    async def async_forecast_daily(self) -> list[Forecast] | None:
        return self.coordinator.data.get("forecast") if self._mode == "daily" else None

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        return self.coordinator.data.get("forecast_hourly") if self._mode == "hourly" else None

    @property
    def forecast(self) -> list[Forecast] | None:
        if self._mode == "daily": return self.coordinator.data.get("forecast")
        return self.coordinator.data.get("forecast_hourly")
