# AuxeRef - Native Reference Image Bridge (Blender 5.0 & 5.2 LTS)

Tamamen yerel (native messaging IPC tabanlı), **sıfır port ve sıfır web sunucusu** ile çalışan; Google Görseller ve Pinterest'te arama yapıp beğendiğiniz herhangi bir resme sağ tıklayarak tek tıkla Blender'a aktarabileceğiniz referans görsel aracı: **AuxeRef**.

---

## ✨ Özellikler ve Kullanım

### 1. F8 Hızlı Arama & Hızlı Referanslar (Quicks)
- Blender'da **`F8`** tuşuna basın (ayrıca Türkçe klavyede `< / "` tuşları da desteklenir).
- Arama kutusu anında klavye odağıyla açılır; aramak istediğinizi yazıp **Enter**'a basarak tarayıcıda arama yapabilirsiniz.
- **Enter Basınca Bitirip Ekle:** Bir resim URL'si yapıştırdığınızda veya kutucuk işaretliyken Enter'a bastığınızda doğrudan sahneye indirip ekler.
- **X Ekseninde 90° Dik Açıyla Ekleme:** Eklenen tüm görseller (Reference Image ve Image Plane) varsayılan olarak X ekseninde 90 derece döndürülmüş (karşıdan bakışa dik) olarak oluşturulur.
- **Quicks İsim ve Link Düzenleme:** F8 penceresi altındaki veya N-Panel'deki Quicks listesinde her görselin yanındaki **Kalem (Edit)** butonuna tıklayarak isim ve web bağlantısını Blender arayüzünden doğrudan değiştirebilirsiniz. **Dünya (URL)** simgesiyle orijinal siteyi tarayıcıda yeniden açabilirsiniz.

### 2. Tarayıcı Sağ Tık Menüsü (`AuxeRef`)
Tarayıcınızda (Chrome, Thorium, Chromium, Brave, Firefox) herhangi bir resme sağ tıkladığınızda **AuxeRef** menüsü açılır:
- **`AuxeRef ➔ Open in Blender`**: Görseli doğrudan 3D imlecinizin bulunduğu yere referans görseli (90° dik açıyla) olarak ekler.
- **`AuxeRef ➔ Add to Quicks`**: Görseli sahneye hemen eklemeden doğrudan Blender'ın Quicks paletine kaydeder; dilediğiniz zaman tek tıkla kullanabilirsiniz.
- *Yüksek Çözünürlük Desteği:* Pinterest ve Google Görseller üzerindeki görseller otomatik olarak orijinal en yüksek çözünürlüklü kalitesine yükseltilerek indirilir.

### 3. Pembe Doku (Pink Image) Hatası Giderildi
- Google Görseller ve Pinterest'in sunduğu modern **AVIF** ve WebP formatları, yerleşik ffmpeg dönüştürücü motoru sayesinde anında PNG'ye dönüştürülür ve Blender veri bloğuna hatasız (`has_data: True`, tam çözünürlük) yüklenir.

### 4. Sıfır Port, Sıfır Web Sunucusu (Zero-Port Native IPC)
- Ağ portu, soket veya HTTP sunucusu açmaz; port çakışması (`[Errno 98] Address already in use`) veya güvenlik riski oluşturmaz.
- Tarayıcı ve Blender arasındaki veri aktarımı yerel OS Native Messaging kanalı ile milisaniyeler içinde gerçekleşir.

---

## 🛠️ Kurulum

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
2. X ekseninde 90° dik açı rotasyonunun (`rotation_euler.x = 90°`) doğrulanması.
3. Google Images ve Pinterest arama komutlarının çalışması.
4. Native host (`blender_image_receiver.py`) üzerinden `OPEN` ve `QUICK_ADD` veri akışı.
5. Quicks isim ve link düzenleme operatörünün (`wm.auxeref_edit_quick`) testi.
6. Enter ile doğrudan indirme ("Bitirip Ekle") özelliğinin testi.
7. AVIF/WebP evrensel PNG dönüştürmesi ve sıfır pembe doku garantisi.
