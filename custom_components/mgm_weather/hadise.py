"""MGM weather phenomenon ("hadise") codes and their Home Assistant equivalents."""

from __future__ import annotations

# code: (Home Assistant condition, MDI icon, Turkish description)
HADISE: dict[str, tuple[str, str, str]] = {
    "A": ("sunny", "mdi:weather-sunny", "Açık"),
    "SCK": ("sunny", "mdi:weather-sunny", "Sıcak"),
    "SGK": ("sunny", "mdi:weather-sunny", "Soğuk"),
    "AB": ("partlycloudy", "mdi:weather-partly-cloudy", "Az Bulutlu"),
    "PB": ("partlycloudy", "mdi:weather-partly-cloudy", "Parçalı Bulutlu"),
    "CB": ("cloudy", "mdi:weather-cloudy", "Çok Bulutlu"),
    "HY": ("rainy", "mdi:weather-partly-rainy", "Hafif Yağmurlu"),
    "HSY": ("rainy", "mdi:weather-rainy", "Hafif Sağanak Yağışlı"),
    "YYSY": ("rainy", "mdi:weather-rainy", "Yer Yer Sağanak Yağışlı"),
    "MSY": ("rainy", "mdi:weather-rainy", "Mevzi Sağanak Yağışlı"),
    "Y": ("rainy", "mdi:weather-rainy", "Yağmurlu"),
    "SY": ("rainy", "mdi:weather-rainy", "Sağanak Yağışlı"),
    "KY": ("pouring", "mdi:weather-pouring", "Kuvvetli Yağmurlu"),
    "KSY": ("pouring", "mdi:weather-pouring", "Kuvvetli Sağanak Yağışlı"),
    "KKY": ("snowy-rainy", "mdi:weather-partly-snowy-rainy", "Karla Karışık Yağmurlu"),
    "HKY": ("snowy", "mdi:weather-partly-snowy-rainy", "Hafif Karla Karışık Yağmurlu"),
    "YKY": ("snowy", "mdi:weather-snowy-rainy", "Yoğun Karla Karışık Yağmurlu"),
    "HK": ("snowy", "mdi:weather-partly-snowy", "Hafif Kar Yağışlı"),
    "K": ("snowy", "mdi:weather-snowy", "Kar Yağışlı"),
    "YK": ("snowy", "mdi:weather-snowy-heavy", "Yoğun Kar Yağışlı"),
    "SIS": ("fog", "mdi:weather-fog", "Sisli"),
    "PUS": ("fog", "mdi:weather-hazy", "Puslu"),
    "DMN": ("fog", "mdi:weather-hazy", "Dumanlı"),
    "DUMAN": ("fog", "mdi:weather-hazy", "Dumanlı"),
    "KF": ("fog", "mdi:weather-dust", "Kum Taşınımı"),
    "D": ("hail", "mdi:weather-hail", "Dolu"),
    "DY": ("hail", "mdi:weather-hail", "Dolu Yağışlı"),
    "GSY": ("lightning-rainy", "mdi:weather-lightning-rainy", "Gökgürültülü Sağanak Yağışlı"),
    "KGY": ("lightning-rainy", "mdi:weather-lightning-rainy", "Kuvvetli Gökgürültülü Sağanak Yağışlı"),
    "KGSY": ("lightning-rainy", "mdi:weather-lightning-rainy", "Kuvvetli Gökgürültülü Sağanak Yağışlı"),
    "R": ("windy", "mdi:weather-windy-variant", "Rüzgarlı"),
    "GKR": ("windy", "mdi:weather-windy", "Kuvvetli Rüzgarlı"),
    "KKR": ("windy", "mdi:weather-windy", "Kuvvetli Rüzgarlı"),
    "FIRT": ("windy", "mdi:weather-hurricane-outline", "Fırtına"),
}

_FALLBACK = ("partlycloudy", "mdi:weather-partly-cloudy", "Bilinmiyor")
_NIGHT_ICONS = {
    "mdi:weather-sunny": "mdi:weather-night",
    "mdi:weather-partly-cloudy": "mdi:weather-night-partly-cloudy",
}

_ASCII_FOLD = str.maketrans(
    {
        "ı": "i", "İ": "i", "I": "i",
        "ğ": "g", "Ğ": "g",
        "ü": "u", "Ü": "u",
        "ş": "s", "Ş": "s",
        "ö": "o", "Ö": "o",
        "ç": "c", "Ç": "c",
    }
)


def condition_for(code: str | None, daytime: bool = True) -> str:
    """Home Assistant condition for an MGM code."""
    condition = HADISE.get(code, _FALLBACK)[0]
    if condition == "sunny" and not daytime:
        return "clear-night"
    return condition


def icon_for(code: str | None, daytime: bool = True) -> str:
    """MDI icon for an MGM code, with night variants where they exist."""
    icon = HADISE.get(code, _FALLBACK)[1]
    return icon if daytime else _NIGHT_ICONS.get(icon, icon)


def text_for(code: str | None) -> str:
    """Turkish description of an MGM code."""
    return HADISE.get(code, _FALLBACK)[2]


def fold_name(name: str | None) -> str:
    """Lower-case a Turkish place name and replace Turkish letters with ASCII.

    Used to match district names and to build entity unique IDs, so the
    output must stay stable between versions.
    """
    return (name or "").translate(_ASCII_FOLD).lower()
