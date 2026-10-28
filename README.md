# Open in Blender - Native Web Bridge (Blender 5.0 & 5.2 LTS)

Tamamen yerel (native messaging tabanlı), **sıfır port ve sıfır web sunucusu** ile çalışan; Google Görseller ve Pinterest'te arama yapıp beğendiğiniz herhangi bir resme **Sağ Tık ➔ Open in Blender** diyerek tek tıkla sahneye aktaran eklenti.

---

## ✨ Nasıl Çalışır?

1. **Blender İçi Arama Kısayolu (`< / "`):**
   - Türkçe Q klavyede `ESC` altındaki `< / "` tuşuna (veya Sol Shift yanındaki `< / >` tuşuna) basın.
   - Açılan arama kutusuna aramak istediğinizi yazın.
   - **Google Images** veya **Pinterest** seçeneğini işaretleyip **Enter**'a basın.
   - Tarayıcınızda doğrudan arama sonuçları açılır.

2. **Tarayıcıda Tek Tıkla Sahneye Ekleme:**
   - Google Görseller veya Pinterest'te herhangi bir resme sağ tıklayın.
   - Menüden **Open in Blender** seçeneğine tıklayın.
   - Resim anında Blender 3D sahnenize (Referans Görsel veya Image Plane) aktarılır!
   - *Pinterest özel desteği:* Pinterest'in düşük çözünürlüklü önizlemeleri otomatik olarak orijinal yüksek çözünürlüklü (`originals`) ana görsel boyutuna yükseltilir.

---

## 🚫 Sıfır Port, Sıfır Web Sunucusu

- Herhangi bir HTTP sunucusu, port veya adres çakışması (`[Errno 98]`) **yoktur**.
- Tarayıcı ve Blender arasındaki iletişim, işletim sisteminin yerel standart IPC (Native Messaging) kanalı üzerinden güvenli ve anlık olarak gerçekleşir.

---

## 🛠️ Kurulum

### 1. Blender Eklentisi (Hazır Yüklü)
Eklenti `~/.config/blender/5.0/scripts/addons/blender_web_search/` içine yüklendi. Blender'da `Edit > Preferences > Add-ons` sekmesinden **Web Image Search & Bridge** eklentisini açmanız yeterlidir.

### 2. Tarayıcı Eklentisi Kurulumu
* **Chrome / Thorium / Chromium:**
  1. `chrome://extensions` adresine gidin.
  2. Sağ üstten **Geliştirici modu**nu açın.
  3. **Paketlenmemiş öğe yükle** butonuna basıp `/home/auxerov/blender-image-search/extension` klasörünü seçin.
* **Mozilla Firefox:**
  1. `about:debugging#/runtime/this-firefox` adresine gidin.
  2. **Geçici Eklenti Yükle...** butonuna basıp `/home/auxerov/blender-image-search/extension_firefox/manifest.json` dosyasını seçin.

---

## 📂 Hazır Paketler
* **Blender Eklentisi:** [`blender_web_search.zip`](file:///home/auxerov/blender-image-search/blender_web_search.zip)
* **Chrome / Thorium Eklentisi:** [`add_to_blender_chrome.zip`](file:///home/auxerov/blender-image-search/add_to_blender_chrome.zip)
* **Firefox Eklentisi (.xpi):** [`add_to_blender_firefox.xpi`](file:///home/auxerov/blender-image-search/add_to_blender_firefox.xpi)
