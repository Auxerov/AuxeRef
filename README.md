# Blender Web Image Search & Browser Bridge (Blender 5.0 & 5.2 LTS)

Blender 5.0 ve 5.2 LTS için doğrudan Türkçe klavye kısayolu (`< / "`) ile Blender içinden arama çubuğunu açan, Google Görseller'de arama yapan ve tarayıcınızda (Chrome, Thorium, Firefox) herhangi bir görsele **Sağ Tık > Add to Blender** diyerek anında 3D sahnenize eklemenizi sağlayan komple köprü sistemi.

---

## 🚀 Hızlı Bakış ve İş Akışı

1. **Blender'da Kısayola Basın:**
   - Türkçe Q klavyede **`ESC` tuşunun hemen altındaki `< / "`** tuşuna (veya Sol Shift yanındaki `< / >` tuşuna) basın.
   - Blender içinde arama kutusu açılır.
   - Aramak istediğiniz kelimeyi yazıp **Enter**'a basın.
   - Varsayılan tarayıcınızda (Thorium / Chrome / Firefox) doğrudan **Google Görseller** açılır.

2. **Tarayıcıda Sağ Tıklayıp Sahneye Ekleyin:**
   - Google Görseller'de istediğiniz resmi bulun.
   - Resme sağ tıklayın:
     - **Add to Blender ➔ As Reference Image (Empty):** 3D İmlecin konumuna referans görsel ekler.
     - **Add to Blender ➔ As Image Plane (Mesh):** Resmin orijinal en-boy oranına göre UV haritalı, Principled BSDF materyalli bir 3D Plane oluşturur.
     - **Add to Blender ➔ Apply to Active Material:** Seçili olan aktif objenin materyaline doku (Base Color) olarak atar.

---

## 🛠️ Kurulum Adımları

### 1. Blender Eklentisi (Zaten Yüklendi)
Eklenti dosyaları sisteminize kuruldu:
- `~/.config/blender/5.0/scripts/addons/blender_web_search/`
- `~/.config/blender/5.2/scripts/addons/blender_web_search/`

Blender'ı açıp `Edit > Preferences > Add-ons` bölümünden **Web Image Search & Bridge** eklentisinin kutucuğunu işaretlemeniz yeterlidir. Eklenti açıldığında `http://127.0.0.1:9981` üzerinden güvenli yerel köprü sunucusu otomatik olarak çalışmaya başlar.

---

### 2. Tarayıcı Eklentisi Kurulumu

#### A) Google Chrome / Thorium / Chromium / Brave:
1. Tarayıcınızın adres çubuğuna şunu yazıp Enter'a basın:
   `chrome://extensions`
2. Sağ üst köşedeki **"Geliştirici modu" (Developer mode)** anahtarını açın.
3. Sol üstte beliren **"Paketlenmemiş öğe yükle" (Load unpacked)** butonuna tıklayın.
4. Şu klasörü seçin:
   `/home/auxerov/blender-image-search/extension`
5. Eklenti hemen aktifleşir! Tarayıcı araç çubuğundaki Blender simgesine tıklayarak bağlantı durumunu (`🟢 Online`) görebilirsiniz.

#### B) Mozilla Firefox:
1. Firefox adres çubuğuna şunu yazıp Enter'a basın:
   `about:debugging#/runtime/this-firefox`
2. **"Geçici Eklenti Yükle..." (Load Temporary Add-on...)** butonuna tıklayın.
3. Şu dosyayı seçin:
   `/home/auxerov/blender-image-search/extension_firefox/manifest.json`
4. Eklenti yüklenir ve sağ tık menüsüne hemen eklenir!

---

## 📂 Hazır Paketler (.zip)

Proje klasöründe hazır arşivlenmiş dosyalar bulunmaktadır:
- **`blender_web_search.zip`**: Başka bir bilgisayara Blender eklentisi olarak yüklemek için.
- **`add_to_blender_chrome.zip`**: Chrome / Thorium / Chromium için paketlenmiş eklenti.
- **`add_to_blender_firefox.zip`**: Firefox için paketlenmiş eklenti.

---

## 🧪 Doğrulama ve Test Sonuçları

Otomatik test paketi (`tests/test_bridge_addon.py`) ile hem Blender 5.0.1 hem de Blender 5.2.2 LTS üzerinde şu adımlar test edilmiş ve onaylanmıştır:
1. Eklentinin hatasız yüklenmesi ve `ACCENT_GRAVE` / `GRLESS` kısayol haritalarının kaydı.
2. HTTP Bridge sunucusunun `9981` portunda ayağa kalkması ve CORS isteklerini karşılaması.
3. `POST /add_image` ile gönderilen görsellerin (URL veya Base64) arka planda indirilip Blender'ın ana iş parçacığında `Reference Empty`, `Image Plane` ve `Active Material` olarak hatasız oluşturulması.
4. Eklenti kapatıldığında sunucunun ve portun temiz bir şekilde serbest bırakılması.
