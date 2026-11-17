"""Constants for the MGM Hava Durumu integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "mgm_weather"

# Config entry data keys. Do not rename: existing entries store these.
CONF_CITY: Final = "city"
CONF_DISTRICT: Final = "district"

UPDATE_INTERVAL: Final = timedelta(minutes=20)
# How long the last good data is kept on screen while MGM is unreachable.
STALE_DATA_GRACE: Final = timedelta(hours=6)
REQUEST_TIMEOUT_SECONDS: Final = 25

MGM_API_BASE: Final = "https://servis.mgm.gov.tr/web"
# MGM's forecast timestamps end in "Z" but are Turkish local time
# (the 12:00Z slot is the one mgm.gov.tr shows as 12.00-15.00).
MGM_TIME_ZONE: Final = "Europe/Istanbul"
MGM_HEADERS: Final = {
    "Host": "servis.mgm.gov.tr",
    "Origin": "https://www.mgm.gov.tr",
    "Referer": "https://www.mgm.gov.tr/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9",
}
