"""Fetches current conditions and forecasts from the MGM web service."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any
from urllib.parse import quote

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CITY,
    CONF_DISTRICT,
    DOMAIN,
    MGM_API_BASE,
    MGM_HEADERS,
    MGM_TIME_ZONE,
    REQUEST_TIMEOUT_SECONDS,
    STALE_DATA_GRACE,
    UPDATE_INTERVAL,
)
from .hadise import condition_for, fold_name

_LOGGER = logging.getLogger(__name__)

type MgmConfigEntry = ConfigEntry[MgmCoordinator]


class MgmCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls MGM for one province/district."""

    config_entry: MgmConfigEntry

    def __init__(self, hass: HomeAssistant, entry: MgmConfigEntry) -> None:
        """Set up the coordinator for a config entry."""
        self.city: str = entry.data.get(CONF_CITY, "")
        self.district: str = entry.data.get(CONF_DISTRICT, "")
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {self.city} {self.district}".strip(),
            update_interval=UPDATE_INTERVAL,
        )
        self._session = async_get_clientsession(hass)
        # (station used for this location, province centre station)
        self._stations: tuple[dict[str, Any], dict[str, Any]] | None = None
        self._last_good_fetch: datetime | None = None
        self._mgm_tz: tzinfo | None = None

    async def _get(self, path: str) -> Any:
        async with self._session.get(f"{MGM_API_BASE}/{path}", headers=MGM_HEADERS) as resp:
            return await resp.json()

    async def _resolve_stations(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Find the district station (if any) and the province centre station."""
        if self._stations is None:
            stations = await self._get(f"merkezler/ililcesi?il={quote(self.city)}")

            centre = next(
                (s for s in stations if s.get("oncelik") == 1),
                stations[0] if stations else None,
            )
            if not centre:
                raise ValueError("Il merkezi bulunamadi.")

            district_station = None
            if self.district:
                wanted = fold_name(self.district)
                district_station = next(
                    (s for s in stations if fold_name(s.get("ilce", "")) == wanted),
                    None,
                )
            self._stations = (district_station or centre, centre)
        return self._stations

    async def _first_with_data(self, path_for: Callable[[Any], str], *ids: Any) -> Any:
        """Return the first non-empty response, trying each distinct station id in order."""
        tried: list[Any] = []
        for station_id in ids:
            if not station_id or station_id in tried:
                continue
            tried.append(station_id)
            if data := await self._get(path_for(station_id)):
                return data
        return None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
                data = await self._fetch()
        except Exception as err:  # noqa: BLE001 - any failure falls back to cached data
            if (
                self.data
                and self._last_good_fetch
                and datetime.now() - self._last_good_fetch < STALE_DATA_GRACE
            ):
                _LOGGER.debug("MGM baglantisi kurulamadi (%s), son veri gosteriliyor", err)
                return self.data
            raise UpdateFailed(
                f"MGM Hatasi (En az 6 saattir guncel veri alinamiyor): {err}"
            ) from err
        self._last_good_fetch = datetime.now()
        return data

    async def _fetch(self) -> dict[str, Any]:
        primary, centre = await self._resolve_stations()

        current = await self._first_with_data(
            lambda station_id: f"sondurumlar?merkezid={station_id}",
            primary.get("sondurumIstNo"),
            primary.get("merkezId"),
            centre.get("sondurumIstNo"),
            centre.get("merkezId"),
        )
        if not current:
            raise ValueError("sondurumlar alinamadi.")
        now_obs = current[0]

        daily = await self._first_with_data(
            lambda station_id: f"tahminler/gunluk?istno={station_id}",
            primary.get("merkezId"),
            centre.get("merkezId"),
        )
        hourly = await self._first_with_data(
            lambda station_id: f"tahminler/saatlik?istno={station_id}",
            primary.get("saatlikTahminIstNo"),
            centre.get("saatlikTahminIstNo"),
        )

        if self._mgm_tz is None:
            self._mgm_tz = await dt_util.async_get_time_zone(MGM_TIME_ZONE) or timezone(
                timedelta(hours=3)
            )
        tz = self._mgm_tz

        code = now_obs.get("hadiseKodu")
        return {
            "condition": condition_for(code),
            "mgm_code": code,
            "temperature": now_obs.get("sicaklik"),
            "pressure": now_obs.get("aktuelBasinc"),
            "humidity": now_obs.get("nem"),
            "wind_speed": now_obs.get("ruzgarHiz"),
            "forecast": _daily_forecast(daily[0], tz) if daily else [],
            "forecast_hourly": _hourly_forecast(hourly[0].get("tahmin", []), tz) if hourly else [],
        }


def _mgm_time(value: Any, tz: tzinfo) -> datetime | None:
    """Parse an MGM timestamp. The trailing "Z" is wrong: the value is Turkish local time."""
    try:
        return datetime.fromisoformat(value).replace(tzinfo=tz)
    except (TypeError, ValueError):
        return None


def _daily_forecast(day: dict[str, Any], tz: tzinfo) -> list[dict[str, Any]]:
    """MGM's five forecast days (...Gun1 to ...Gun5), dated by MGM's own tarihGunN.

    Day 1 is today until MGM issues the next forecast, then tomorrow, so the
    dates must come from the response rather than from the clock.
    """
    today = dt_util.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    forecast = []
    for n in range(1, 6):
        date = _mgm_time(day.get(f"tarihGun{n}"), tz) or today + timedelta(days=n)
        forecast.append(
            {
                "datetime": date.isoformat(),
                "native_temperature": day.get(f"enYuksekGun{n}"),
                "native_templow": day.get(f"enDusukGun{n}"),
                "condition": condition_for(day.get(f"hadiseGun{n}")),
                "native_precipitation": 0,
            }
        )
    return forecast


def _hourly_forecast(slots: list[dict[str, Any]], tz: tzinfo) -> list[dict[str, Any]]:
    """MGM's 3-hourly forecast slots."""
    forecast = []
    for slot in slots:
        if (when := _mgm_time(slot.get("tarih"), tz)) is None:
            continue
        forecast.append(
            {
                "datetime": when.isoformat(),
                "native_temperature": slot.get("sicaklik"),
                "condition": condition_for(slot.get("hadise"), 6 <= when.hour < 19),
                "humidity": slot.get("nem"),
                "native_wind_speed": slot.get("ruzgarHizi"),
                "native_precipitation": 0,
            }
        )
    return forecast
