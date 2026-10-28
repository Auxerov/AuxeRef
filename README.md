# Blender Image Search Add-on (Blender 5.0 & 5.2 LTS)

Blender 5.0 ve 5.2 LTS için doğrudan 3D Viewport arayüzünden (N-Panel) internetten ve Google Görseller'den görsel arayıp tek tıkla sahneye eklemenizi sağlayan hafif ve güçlü eklenti.

---

## ✨ Özellikler

1. **Arayüzden Doğrudan Arama (3D Viewport > N-Paneli > `Image Search`):**
   - Blender'dan çıkmadan veya harici tarayıcı açmadan doğrudan anahtar kelimeyle arama yapın.
   - Sonuçlar küçük resim (thumbnail) önizlemeleriyle 3 sütunlu ızgara biçiminde listelenir.
   - Asenkron arama ve indirme: Blender arayüzü asla donmaz veya takılmaz.

2. **Çoklu Arama Motoru Desteği:**
   - **Web / Bing (Free):** Sıfır kurulum! Herhangi bir API anahtarı gerektirmeden anında çalışır.
   - **Wikimedia Commons:** Kamu malı (Public Domain) ve Creative Commons lisanslı yüksek çözünürlüklü referanslar ve dokular.
   - **Google Custom Search (API):** Kendi Google API anahtarınızı girerek resmi Google Görseller altyapısını kullanma imkanı.

3. **Görsel Ekleme Seçenekleri:**
   - **Add as Reference (Empty):** Seçilen görseli 3D İmlecin (3D Cursor) bulunduğu konuma en-boy oranı korunmuş Referans Görsel (Empty Image) olarak ekler.
   - **Add as Image Plane (Mesh):** Görselin orijinal en-boy oranına göre orantılanmış bir Plane mesh'i oluşturur, Principled BSDF materyali bağlar ve otomatik olarak Material Preview moduna geçer. Saydamlık (Alpha kanalı) varsa otomatik olarak transparan olarak ayarlar.
   - **Apply to Active Material:** Seçili nesnenin aktif materyalinin Base Color dokusu olarak atar.
   - **Open in Image Editor:** Görseli doğrudan Blender'ın Görsel Editörü (UV/Image Editor) içine yükler.

---

## 🚀 Kurulum

### Yöntem 1: Doğrudan Blender İçinden (.zip ile)
1. `blender_image_search.zip` dosyasını indirin.
2. Blender'ı açın: `Edit > Preferences > Add-ons` sekmesine gidin.
3. Sağ üstteki aşağı açılır menüden `Install from Disk...` seçeneğine tıklayın.
4. `blender_image_search.zip` dosyasını seçin ve etkinleştirin (kutucuğu işaretleyin).

### Yöntem 2: Manuel Klasör Kurulumu
Eklenti klasörünü Blender eklenti dizinine kopyalayın:
- **Linux:** `~/.config/blender/5.0/scripts/addons/blender_image_search/`
- **Windows:** `%APPDATA%\Blender Foundation\Blender\5.0\scripts\addons\blender_image_search\`
- **macOS:** `~/Library/Application Support/Blender/5.0/scripts/addons/blender_image_search/`

---

## 🛠️ Google Custom Search API Kurulumu (İsteğe Bağlı)
> **Not:** Eklenti **Web / Bing** ve **Wikimedia** modunda hiçbir anahtar gerektirmeden tamamen ücretsiz ve sınırsız çalışır. Ancak doğrudan Google motorunu kullanmak isterseniz:

1. [Google Cloud Console](https://console.cloud.google.com/) üzerinden ücretsiz bir proje açın ve **Custom Search API** servisini etkinleştirin.
2. Credentials bölümünden bir **API Key** oluşturun.
3. [Programmable Search Engine](https://programmablesearchengine.google.com/) adresine giderek yeni bir arama motoru oluşturun:
   - "Search the entire web" seçeneğini açın.
   - "Image search" seçeneğini **ON** yapın.
   - Motor Kimliğini (**CX ID**) kopyalayın.
4. Blender'da `Preferences > Add-ons > Image Search` ayarlarına gidip API Key ve Search Engine ID (CX) alanlarına yapıştırın.

---

## 🧪 Test ve Doğrulama
Eklenti, Blender 5.0.1 ve Blender 5.2.2 LTS sürümlerinde tam kapsamlı headless testlerle doğrulanmıştır:
- Operatör kayıtları ve unregister mekanizması sıfır bellek sızıntısıyla çalışır.
- Referans görsel ve materyal düğümleri (ShaderNodeTexImage) Blender 5.0 standartlarına tam uyumludur.
