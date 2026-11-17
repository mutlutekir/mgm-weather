<h1 align="center">MGM Hava Durumu for Home Assistant</h1>

<p align="center">
Current conditions and forecasts from the Turkish State Meteorological Service (MGM), for any province or district in Türkiye.
</p>

<p align="center">
<a href="https://hacs.xyz"><img src="https://img.shields.io/badge/HACS-Integration-41BDF5.svg?style=for-the-badge" alt="HACS"></a>
<a href="https://github.com/mutlutekir/mgm-weather/releases"><img src="https://img.shields.io/github/v/release/mutlutekir/mgm-weather?style=for-the-badge&color=blue" alt="Latest release"></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/mutlutekir/mgm-weather?style=for-the-badge" alt="License"></a>
</p>

<p align="center"><a href="#english">English</a> · <a href="#turkce">Türkçe</a></p>

---

<a id="english"></a>

## English

This integration reads the same data that powers [mgm.gov.tr](https://www.mgm.gov.tr) and turns it into Home Assistant weather entities. No account or API key is needed.

### What you get

- **Any province or district.** Pick a province, and optionally a district. If MGM has no station for that district, the province centre is used instead.
- **Two weather entities per location:** one with a 5-day forecast and one with MGM's 3-hourly forecast.
- **Forecasts that line up with mgm.gov.tr.** Days and hours are taken from MGM's own timestamps, in Turkish time.
- **MGM's own descriptions.** MGM's weather codes are translated into Home Assistant conditions and matching icons, and the original Turkish description is available as an attribute.
- **Resilient to outages.** If MGM can't be reached, the last values stay on screen for up to 6 hours before the entities become unavailable.
- **English and Turkish setup screens.**

### Installation

**HACS**

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=mutlutekir&repository=mgm-weather&category=integration" target="_blank"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open this repository in HACS"></a>

1. Click the button above, or search for **MGM Hava Durumu** in HACS. If it doesn't show up, add `https://github.com/mutlutekir/mgm-weather` under HACS → ⋮ → *Custom repositories*, type *Integration*.
2. Download it, then restart Home Assistant.

**Manual**

Copy `custom_components/mgm_weather` from the [latest release](https://github.com/mutlutekir/mgm-weather/releases) into the `custom_components` folder of your Home Assistant configuration, then restart.

### Setup

<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=mgm_weather" target="_blank"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add MGM Hava Durumu to Home Assistant"></a>

Or go to **Settings → Devices & services → Add integration** and choose **MGM Hava Durumu**.

| Field | |
|---|---|
| **Province** | Required, e.g. `Ankara`, `İstanbul`, `Afyonkarahisar`. |
| **District** | Optional, e.g. `Çankaya`, `Kadıköy`. Turkish letters are optional: `kadikoy` works too. Leave it empty for the province centre. |

Add the integration again for each extra location.

### Entities

For *İstanbul / Kadıköy*, for example:

| Entity | Forecast |
|---|---|
| `weather.istanbul_kadikoy_hava_durumu` | 5 days |
| `weather.istanbul_kadikoy_saatlik` | every 3 hours |

Both show the current temperature, humidity, pressure and wind speed, and refresh every 20 minutes. Extra attributes:

- `detayli_hadise`: MGM's description of the current weather, e.g. *Parçalı Bulutlu*
- `mgm_hadise_kodu`: MGM's code for it, e.g. `PB`

### Dashboard examples

3-hourly forecast with the built-in weather card:

```yaml
type: weather-forecast
entity: weather.karabuk_merkez_saatlik
show_current: false
show_forecast: true
forecast_type: hourly
forecast_slots: 24
grid_options:
  rows: auto
```

Current conditions and a 5-day chart with [weather-forecast-card](https://community.home-assistant.io/t/slightly-improved-weather-forecast-card-for-home-assistant/966687) and [card-mod](https://github.com/thomasloven/lovelace-card-mod). The `temperature_entity` and `humidity_entity` lines are optional and use your own outdoor sensors:

```yaml
type: custom:weather-forecast-card
entity: weather.karabuk_safranbolu_hava_durumu
name: Detaylı Hava Durumu
show_current: true
show_forecast: true
show_condition_effects: true
default_forecast: daily
current:
  temperature_entity: sensor.dis_termometre_sicaklik
  humidity_entity: sensor.dis_termometre_nem
  temperature_precision: 1
  show_attributes:
    - pressure
    - wind_speed
forecast:
  mode: chart
  show_attribute_selector: true
  use_color_thresholds: true
  show_sun_times: true
  temperature_precision: 0
card_mod:
  style: |
    ha-card {
      min-height: 480px;
      --ha-font-size-3xl: 52px;
      --ha-font-size-xl: 28px;
      --ha-font-size-m: 16px;
      border-radius: 28px;
      background: rgba(0, 0, 0, 0.3) !important;
      box-shadow: 0px 10px 25px rgba(0,0,0,0.5);
    }
```

### Credits

- Developed and maintained by **Mutlu Tekir**.
- Inspired by **Fatih Taşkın**'s mgm-weather integration.
- Weather data: Turkish State Meteorological Service (MGM). This project is independent and not affiliated with or endorsed by MGM.
- Licensed under GPL-3.0, see [LICENSE](LICENSE).

---

<a id="turkce"></a>

## Türkçe

Bu entegrasyon, [mgm.gov.tr](https://www.mgm.gov.tr) sitesinin kullandığı verileri alıp Home Assistant'ta hava durumu varlıklarına dönüştürür. Hesap ya da API anahtarı gerekmez.

### Neler sunar

- **Her il ve ilçe.** Bir il, isterseniz bir de ilçe seçersiniz. MGM'nin o ilçede istasyonu yoksa il merkezinin verileri kullanılır.
- **Her konum için iki hava durumu varlığı:** biri 5 günlük, diğeri MGM'nin 3 saatlik tahminiyle.
- **mgm.gov.tr ile birebir aynı günler ve saatler.** Tarihler ve saatler MGM'nin kendi verisinden, Türkiye saatiyle alınır.
- **MGM'nin kendi ifadeleri.** MGM hadise kodları Home Assistant durumlarına ve uygun simgelere çevrilir; MGM'nin Türkçe açıklaması da bir öznitelik olarak gelir.
- **Kesintilere dayanıklı.** MGM'ye ulaşılamazsa son değerler 6 saate kadar ekranda kalır, ancak sonra varlıklar kullanılamaz duruma geçer.
- **Türkçe ve İngilizce kurulum ekranı.**

### Kurulum

**HACS**

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=mutlutekir&repository=mgm-weather&category=integration" target="_blank"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Bu depoyu HACS'ta aç"></a>

1. Yukarıdaki düğmeye tıklayın ya da HACS'ta **MGM Hava Durumu** diye aratın. Listede çıkmazsa HACS → ⋮ → *Custom repositories* bölümüne `https://github.com/mutlutekir/mgm-weather` adresini *Integration* türüyle ekleyin.
2. İndirin ve Home Assistant'ı yeniden başlatın.

**Elle kurulum**

[Son sürümdeki](https://github.com/mutlutekir/mgm-weather/releases) `custom_components/mgm_weather` klasörünü Home Assistant yapılandırmanızdaki `custom_components` klasörüne kopyalayın ve yeniden başlatın.

### Ayarlama

<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=mgm_weather" target="_blank"><img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="MGM Hava Durumu'nu Home Assistant'a ekle"></a>

Ya da **Ayarlar → Cihazlar ve hizmetler → Entegrasyon ekle** yolunu izleyip **MGM Hava Durumu**'nu seçin.

| Alan | |
|---|---|
| **İl** | Zorunlu. Örnek: `Ankara`, `İstanbul`, `Afyonkarahisar`. |
| **İlçe** | İsteğe bağlı. Örnek: `Çankaya`, `Kadıköy`. Türkçe harf şart değil, `kadikoy` da olur. Boş bırakırsanız il merkezi kullanılır. |

Başka bir konum için entegrasyonu tekrar ekleyin.

### Varlıklar

Örneğin *İstanbul / Kadıköy* için:

| Varlık | Tahmin |
|---|---|
| `weather.istanbul_kadikoy_hava_durumu` | 5 günlük |
| `weather.istanbul_kadikoy_saatlik` | 3 saatte bir |

İkisi de anlık sıcaklık, nem, basınç ve rüzgar hızını gösterir, 20 dakikada bir güncellenir. Ek öznitelikler:

- `detayli_hadise`: MGM'nin o anki hava için açıklaması, örneğin *Parçalı Bulutlu*
- `mgm_hadise_kodu`: MGM'nin bu durum için kodu, örneğin `PB`

### Kart örnekleri

Örnek YAML'lar İngilizce bölümdeki [Dashboard examples](#dashboard-examples) başlığında. İlki Home Assistant'ın kendi hava durumu kartıyla 3 saatlik tahmini gösterir. İkincisi [weather-forecast-card](https://community.home-assistant.io/t/slightly-improved-weather-forecast-card-for-home-assistant/966687) ve [card-mod](https://github.com/thomasloven/lovelace-card-mod) ile anlık durumu ve 5 günlük grafiği gösterir; `temperature_entity` ve `humidity_entity` satırları isteğe bağlıdır, kendi dış ortam sensörlerinizi kullanır.

### Teşekkür ve yasal not

- Geliştiren ve sürdüren: **Mutlu Tekir**.
- **Fatih Taşkın**'ın mgm-weather entegrasyonundan esinlenilmiştir.
- Hava durumu verisi: Meteoroloji Genel Müdürlüğü (MGM). Bu proje bağımsızdır; MGM ile bir bağlantısı yoktur ve MGM tarafından onaylanmamıştır.
- GPL-3.0 lisansıyla dağıtılır, bkz. [LICENSE](LICENSE).
