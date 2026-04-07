<h1 align="center">MGM Weather (FT) - Home Assistant Integration</h1>

<div align="center">
<img src="https://github.com/user-attachments/assets/ac0bd2e5-035c-4c47-a6c2-877c08a061b2" alt="mgm-weather-ft" width="100%">






<a href="https://github.com/hacs/integration">
<img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge" alt="HACS">
</a>
<a href="https://github.com/taskinfa/mgm-weather/releases">
<img src="https://img.shields.io/github/v/release/taskinfa/mgm-weather?style=for-the-badge&color=blue" alt="Release">
</a>
<a href="https://github.com/taskinfa">
<img src="https://img.shields.io/badge/maintainer-Fatih%20Taşkın-green?style=for-the-badge" alt="Maintainer">
</a>

<h3>
<a href="#english">🇬🇧 English</a> | <a href="#türkçe-kılavuz">🇹🇷 Türkçe</a>
</h3>
</div>

<hr>

<div id="english"></div>

<h2>🇬🇧 English</h2>

<p>
<strong>MGM Weather (FT)</strong> is a custom integration for Home Assistant that retrieves weather data from the Turkish State Meteorological Service (MGM) via a custom proxy API. It provides accurate, localized weather conditions and forecasts for cities in Turkey.
</p>

<h3>🌟 Features</h3>
<ul>
<li><strong>Real-time Data:</strong> Fetches current temperature, humidity, wind speed, pressure, and weather conditions.</li>
<li><strong>Daily Forecast:</strong> Provides a 5-day weather forecast.</li>
<li><strong>Easy Configuration:</strong> Setup directly via the Home Assistant UI (Config Flow).</li>
<li><strong>Multi-City Support:</strong> Add as many provinces and districts as you like.</li>
<li><strong>Localized:</strong> Fully compatible with Turkish locations and weather codes.</li>
</ul>

<h3>🚀 Installation</h3>

<h4>Method 1: HACS (Recommended)</h4>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=taskinfa&repository=mgm-weather&category=integration" target="_blank">
<img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.">
</a>

<ol>
<li>Open <strong>HACS</strong> in Home Assistant.</li>
<li>Go to <strong>Integrations</strong> > click the 3 dots in the top right corner > <strong>Custom repositories</strong>.</li>
<li>Paste the URL of this repository: <code>https://github.com/mutlutekir/mgm-weather</code></li>
<li>Select <strong>Integration</strong> as the category and click <strong>Add</strong>.</li>
<li>Search for <strong>"MGM Hava Durumu (FT)"</strong> and install it.</li>
<li><strong>Restart</strong> Home Assistant.</li>
</ol>

<h4>Method 2: Manual</h4>
<ol>
<li>Download the <a href="https://github.com/mutlutekir/mgm-weather/releases">latest release</a>.</li>
<li>Copy the <code>custom_components/mgm_weather</code> folder to your Home Assistant's <code>custom_components</code> directory.</li>
<li><strong>Restart</strong> Home Assistant.</li>
</ol>

<h3>⚙️ Configuration</h3>

<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=mgm_weather" target="_blank">
<img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Open your Home Assistant instance and start setting up a new integration.">
</a>

<ol>
<li>Go to <strong>Settings</strong> > <strong>Devices & Services</strong>.</li>
<li>Click <strong>+ ADD INTEGRATION</strong> in the bottom right corner.</li>
<li>Search for <strong>"MGM Hava Durumu (FT)"</strong>.</li>
<li>Enter your city name (e.g., <code>Istanbul</code>, <code>Afyonkarahisar</code>, <code>Ankara</code>) in the popup box.</li>
<li>Enter your district name if you want (e.g., <code>Kadıköy</code>, <code>Şebinkarahisar</code>, <code>Çankaya</code>) in the popup box.</li>
<li>Click <strong>Submit</strong>.</li>
</ol>

<h3>📊 Dashboard Card Example</h3>
<p>You can use the standard weather card or a custom card like Mushroom.</p>

<pre lang="yaml"><code>type: weather-forecast
entity: weather.mgm_weather_mgm_afyonkarahisar
show_current: true
show_forecast: true
forecast_type: daily
name: Afyonkarahisar
forecast_slots: 6
grid_options:
rows: 4
columns: full</code></pre>

<h3>❤️ Credits & Disclaimer</h3>
<ul>
<li><strong>Developer:</strong> Fatih Taşkın</li>
<li><strong>Data Source:</strong> Turkish State Meteorological Service (MGM) via proxy API.</li>
<li><em>This is a custom integration and is not officially affiliated with MGM.</em></li>
</ul>

<hr>

<div id="türkçe-kılavuz"></div>

<h2>🇹🇷 Türkçe Kılavuz</h2>

<p>
<strong>MGM Weather (FT)</strong>, Türkiye Meteoroloji Genel Müdürlüğü (MGM) verilerini özel bir proxy API üzerinden Home Assistant'a aktaran özel bir entegrasyondur. Türkiye'deki şehirler için en doğru anlık hava durumu ve tahmin verilerini sağlar.
</p>

<h3>🌟 Özellikler</h3>
<ul>
<li><strong>Anlık Veri:</strong> Sıcaklık, nem, rüzgar hızı, basınç ve hava durumu ikonunu anlık çeker.</li>
<li><strong>Günlük Tahmin:</strong> 5 günlük hava tahmini sunar.</li>
<li><strong>Kolay Kurulum:</strong> Home Assistant arayüzü üzerinden (Config Flow) saniyeler içinde kurulur.</li>
<li><strong>Çoklu Şehir:</strong> İstediğiniz kadar farklı şehir ekleyebilirsiniz.</li>
<li><strong>Yerelleştirilmiş:</strong> Türkiye lokasyonları ve MGM hava durumu kodlarıyla tam uyumludur.</li>
</ul>

<h3>🚀 Kurulum</h3>

<h4>Yöntem 1: HACS (Önerilen)</h4>

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=taskinfa&repository=mgm-weather&category=integration" target="_blank">
<img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Home Assistant örneğinizi açın ve Home Assistant Topluluk Mağazası içinde bir depo açın.">
</a>

<ol>
<li>Home Assistant'ta <strong>HACS</strong> menüsünü açın.</li>
<li><strong>Integrations</strong> (Entegrasyonlar) kısmına gidin > sağ üstteki üç noktaya tıklayın > <strong>Custom repositories</strong> (Özel depolar).</li>
<li>Bu reponun adresini yapıştırın: <code>https://github.com/taskinfa/mgm-weather</code></li>
<li>Kategori olarak <strong>Integration</strong> seçin ve <strong>Ekle</strong> deyin.</li>
<li>Listeden <strong>"MGM Hava Durumu (FT)"</strong> entegrasyonunu bulup indirin.</li>
<li>Home Assistant'ı <strong>Yeniden Başlatın</strong>.</li>
</ol>

<h4>Yöntem 2: Manuel</h4>
<ol>
<li><a href="https://github.com/taskinfa/mgm-weather/releases">En son sürümü</a> indirin.</li>
<li><code>custom_components/mgm_weather</code> klasörünü Home Assistant dizininizdeki <code>custom_components</code> klasörünün içine kopyalayın.</li>
<li>Home Assistant'ı <strong>Yeniden Başlatın</strong>.</li>
</ol>

<h3>⚙️ Yapılandırma</h3>

<a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=mgm_weather" target="_blank">
<img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Home Assistant örneğinizi açın ve yeni bir entegrasyon ayarlamaya başlayın.">
</a>

<ol>
<li><strong>Ayarlar</strong> > <strong>Cihazlar ve Hizmetler</strong> menüsüne gidin.</li>
<li>Sağ alttaki <strong>+ ENTEGRASYON EKLE</strong> butonuna tıklayın.</li>
<li>Arama kutusuna <strong>"MGM Hava Durumu (FT)"</strong> yazın.</li>
<li>Açılan pencereye şehir adını yazın (Örn: <code>Istanbul</code>, <code>Afyonkarahisar</code>, <code>Ankara</code>).</li>
<li><strong>Gönder</strong> butonuna tıklayın.</li>
</ol>

<h3>📊 Kart Örneği</h3>
<p>Standart hava durumu kartını veya Mushroom gibi özel kartları kullanabilirsiniz.</p>

<pre lang="yaml"><code>type: weather-forecast
entity: weather.mgm_weather_mgm_afyonkarahisar
show_current: true
show_forecast: true
forecast_type: daily
name: Afyonkarahisar
forecast_slots: 6
grid_options:
rows: 4
columns: full</code></pre>

<h3>❤️ Emeği Geçenler & Yasal Uyarı</h3>
<ul>
<li><strong>Geliştirici:</strong> Fatih Taşkın</li>
<li><strong>Veri Kaynağı:</strong> Türkiye Meteoroloji Genel Müdürlüğü (MGM).</li>
<li><em>Bu özel bir entegrasyondur ve MGM ile resmi bir bağlantısı yoktur.</em></li>
</ul>
