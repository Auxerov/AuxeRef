# Blender Web Image Search & Browser Bridge (Blender 5.0 & 5.2 LTS)

Blender 5.0 ve 5.2 LTS için doğrudan Türkçe klavye kısayolu (`< / "`) ile Blender içinden arama çubuğunu açan, Google Görseller'de arama yapan ve tarayıcınızda (Chrome, Thorium, Firefox) herhangi bir görsele **Sağ Tık > Add to Blender** diyerek anında 3D sahnenize eklemenizi sağlayan komple köprü sistemi.

---

## ⚡ Otomatik Tarayıcı Algılama ve Hızlı Kurulum

Eklenti Blender'a kurulup ilk kez etkinleştirildiğinde:
1. İşletim sisteminizin varsayılan tarayıcısını otomatik olarak tespit eder (örn. **Thorium Browser**, **Google Chrome**, **Chromium**, **Mozilla Firefox**).
2. Ekrana bir bildirim penceresi açarak eklentiyi varsayılan tarayıcınıza eklemek isteyip istemediğinizi sorar:
   - **`[Install Extension to <Tarayıcınız>]`**
3. **Tek Tıkla Kurulum:**
   - **Chromium / Thorium / Chrome için:** Eklenti paketini doğrudan `~/.config/<tarayıcı>/External Extensions/` dizinine otomatik olarak kaydeder, eklenti klasör yolunu panonuza (clipboard) kopyalar ve tarayıcınızda rehber kurulum sayfasını açar.
   - **Firefox için:** Tek tıkla indirip kurabileceğiniz `.xpi` paketini hazırlar ve kurulum sayfasını açar.
   - Eklenti tercihleri (`Edit > Preferences > Add-ons > Web Image Search`) içinden istediğiniz zaman tarayıcıyı değiştirebilir veya kurulumu yenileyebilirsiniz.

---

## 🚀 Hızlı Bakış ve İş Akışı

1. **Blender'da Kısayola Basın:**
   - Türkçe Q klavyede **`ESC` tuşunun hemen altındaki `< / "`** tuşuna (veya Sol Shift yanındaki `< / >` tuşuna) basın.
   - Blender içinde arama kutusu açılır.
   - Aramak istediğiniz kelimeyi yazıp **Enter**'a basın.
   - Varsayılan tarayıcınızda doğrudan **Google Görseller** açılır.

2. **Tarayıcıda Sağ Tıklayıp Sahneye Ekleyin:**
   - Google Görseller'de istediğiniz resmi bulun.
   - Resme sağ tıklayın:
     - **Add to Blender ➔ As Reference Image (Empty):** 3D İmlecin konumuna referans görsel ekler.
     - **Add to Blender ➔ As Image Plane (Mesh):** Resmin orijinal en-boy oranına göre UV haritalı, Principled BSDF materyalli bir 3D Plane oluşturur.
     - **Add to Blender ➔ Apply to Active Material:** Seçili olan aktif objenin materyaline doku (Base Color) olarak atar.

---

## 📂 Dosya ve Paket Konumları

- **Blender Eklenti Paketi:** [`blender_web_search.zip`](file:///home/auxerov/blender-image-search/blender_web_search.zip)
- **Chrome / Thorium / Chromium Eklentisi:** [`add_to_blender_chrome.zip`](file:///home/auxerov/blender-image-search/add_to_blender_chrome.zip)
- **Mozilla Firefox Eklentisi (.xpi):** [`add_to_blender_firefox.xpi`](file:///home/auxerov/blender-image-search/add_to_blender_firefox.xpi)
- **Yerel Köprü Sunucusu:** `http://127.0.0.1:9981` (veya `9982..9985`)

---

## 🧪 Test ve Doğrulama

Otomatik test paketi (`tests/test_bridge_addon.py`) ile hem Blender 5.0.1 hem de Blender 5.2.2 LTS üzerinde doğrulandı:
- Otomatik tarayıcı tespiti (`Thorium Browser / Chromium / Firefox`).
- Çoklu port desteği ve çakışmasız çalışma (`9981` meşgulse otomatik `9982`ye geçiş).
- Tarayıcı eklentisinin Blender'ı otomatik keşfetmesi (dinamik port tarama).
- Referans Görsel, Image Plane ve Materyal Doku oluşturma operasyonları.
