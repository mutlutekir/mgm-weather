"""MGM Weather entegrasyonu için sabitler."""

DOMAIN = "mgm_weather"
CONF_CITY = "city"
# Senin sunucundaki API adresi (İl ismini dinamik ekleyeceğiz)
CONF_DISTRICT = "district"
# Veri güncelleme sıklığı (Saniye cinsinden - 20 Dakika)
SCAN_INTERVAL_SECONDS = 1200
