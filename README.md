# AuxeRef - Native Reference Image Bridge (Blender 5.0 & 5.2 LTS)

Tamamen yerel (native messaging IPC tabanlı), **sıfır port ve sıfır web sunucusu** ile çalışan; Google Görseller ve Pinterest'te arama yapıp beğendiğiniz herhangi bir resme sağ tıklayarak tek tıkla Blender'a aktarabileceğiniz referans görsel aracı: **AuxeRef**.

---

## ✨ Özellikler ve Kullanım

### 1. F8 Hızlı Arama & Hızlı Referanslar (Blender İçi)
- Blender'da **`F8`** tuşuna basın (ayrıca Türkçe klavyede `< / "` tuşları da desteklenir).
- Arama kutusu anında klavye odağıyla açılır; aramak istediğinizi yazıp **Enter**'a basmanız yeterlidir.
- **Tab** tuşuyla **Google Images** ile **Pinterest** arasında hızlıca geçiş yapabilirsiniz.
- Pencerenin altında ve 3D Viewport N-Panel'indeki (**AuxeRef** sekmesi) **Quick References (Hızlı Referanslar)** listesinden daha önce eklediğiniz görselleri tek tıkla sahneye çağırabilirsiniz.

### 2. Tarayıcı Sağ Tık Menüsü (`AuxeRef`)
Tarayıcınızda (Chrome, Thorium, Chromium, Brave, Firefox) herhangi bir resme sağ tıkladığınızda **AuxeRef** menüsü açılır:
- **`AuxeRef ➔ Open in Blender`**: Görseli doğrudan 3D imlecinizin bulunduğu yere referans görseli (veya tercihinize göre Image Plane / Material) olarak ekler.
- **`AuxeRef ➔ Add to Quick`**: Görseli sahneye hemen eklemeden doğrudan Blender'ın hızlı referans paletine kaydeder; dilediğiniz zaman tek tıkla kullanabilirsiniz.
- *Yüksek Çözünürlük Desteği:* Pinterest üzerindeki görseller otomatik olarak orijinal en yüksek çözünürlüklü (`originals`) kalitesine yükseltilerek indirilir.

### 3. Pembe Doku (Pink Image) Hatası Giderildi
- Google Görseller ve Pinterest'in sunduğu modern **AVIF** ve WebP formatları, yerleşik ffmpeg dönüştürücü motoru sayesinde anında PNG'ye dönüştürülür ve Blender veri bloğuna hatasız (`has_data: True`, tam çözünürlük) yüklenir.

### 4. Sıfır Port, Sıfır Web Sunucusu (Zero-Port Native IPC)
- Ağ portu, soket veya HTTP sunucusu açmaz; port çakışması (`[Errno 98] Address already in use`) veya güvenlik riski oluşturmaz.
- Tarayıcı ve Blender arasındaki veri aktarımı yerel OS Native Messaging kanalı ile milisaniyeler içinde gerçekleşir.

---

## 🛠️ Otomatik Kurulum

Blender'da eklenti etkinleştirildiğinde varsayılan tarayıcınızı otomatik tespit eder ve eklentiyi tarayıcı başlangıç bayraklarına ekler.

Manuel olarak tarayıcıya eklemek isterseniz:
* **Chrome / Thorium / Chromium:**
  1. `chrome://extensions` adresine gidin ve **Geliştirici modu**nu açın.
  2. **Paketlenmemiş öğe yükle** butonuna tıklayıp şu klasörü seçin:
     `/home/auxerov/blender-image-search/extension`
* **Mozilla Firefox:**
  1. `about:debugging#/runtime/this-firefox` adresine gidin.
  2. **Geçici Eklenti Yükle...** butonuna tıklayıp şu dosyayı seçin:
     `/home/auxerov/blender-image-search/extension_firefox/manifest.json`

---

## 📂 Hazır Paketler
* **Blender Eklentisi:** [`blender_web_search.zip`](file:///home/auxerov/blender-image-search/blender_web_search.zip)
* **Chrome / Thorium Eklentisi:** [`add_to_blender_chrome.zip`](file:///home/auxerov/blender-image-search/add_to_blender_chrome.zip)
* **Firefox Eklentisi (.xpi):** [`add_to_blender_firefox.xpi`](file:///home/auxerov/blender-image-search/add_to_blender_firefox.xpi)

---

## 🧪 Test ve Doğrulama
Otomatik test paketi (`tests/test_bridge_addon.py`) ile hem Blender 5.0.1 hem de Blender 5.2.2 LTS üzerinde şu adımlar test edilmiş ve onaylanmıştır:
1. `blender_web_search` (AuxeRef) eklentisinin yüklenmesi ve keymap (`F8`, `< / "`) doğrulaması.
2. Google Images ve Pinterest arama komutlarının çalışması.
3. Native host (`blender_image_receiver.py`) üzerinden `OPEN` ve `QUICK_ADD` veri akışı.
4. AVIF formatının otomatik PNG dönüştürülüp hatasız doku olarak sahneye yüklenmesi.
5. Quick References paletinden `wm.auxeref_spawn_quick` ile sahneye referans oluşturulması ve temizlenmesi.
