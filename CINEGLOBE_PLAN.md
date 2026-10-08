# 🎬 CineGlobe — Film & Dizi Keşif Platformu (Aşamalı Geliştirme Planı)

> **Bu dosya kodlama ajanı (Claude Code / Google Antigravity) için ana talimat dosyasıdır.**
> Çalışma adı: **CineGlobe** (istenirse değiştirilebilir).
> **Sürüm notu (v1.1):** Platform artık **film + dizi** destekler. Kodda "movie" yerine genel `Title` kavramı kullanılır (`media_type`: `movie` | `tv`).
> **Sürüm notu (v1.2):** Eklenenler: (a) **TR/EN çift dil** (arayüz + içerik + LLM çıktısı), (b) **Hazır Koleksiyonlar** (Sıkılmam Diyeceğiniz Filmler, Sürükleyici, Çerezlik, Kafanızı Dağıtacak, Başladığı Gibi Bitecek, Tersköşe…), (c) **Oyuncu filmografisi** (kronolojik + en güncel sıralama), (d) **Yakında Çıkacaklar** + **hatırlatıcı**. Yeni bölümler: §3.4–§3.7, Faz 4B, Faz 4C; Faz 2/5/7/10 güncellendi.
> **Sürüm notu (v1.3):** (a) **Yalnızca web:** Flutter/mobil uygulama kapsamdan çıkarıldı (mobil tarayıcıda responsive deneyim korunur). (b) **İsteğe bağlı giriş:** Arama, koleksiyonlar, oyuncu sayfaları ve Şans Globu hesapsız kullanılır; giriş yapanlar **Film Defterim** kazanır (izlediklerim, puanım, özel notlarım, istatistikler) → §3.8, **Faz 7B**. (c) **Gelir modeli:** reklam + affiliate + opsiyonel Premium → §3.9, **Faz 10**. Eski "Mobil Uygulama" fazı (Faz 10) kaldırıldı; Faz 10 artık Gelir Modeli'dir.
> **Sürüm notu (v1.4):** **Ürün şimdilik tamamen ücretsiz ve reklamsız/aboneliksiz** çalışır (TMDB'nin ücretsiz, ticari olmayan API kullanımına uymak için). **Faz 10 (Gelir Modeli) ERTELENDİ**; uygulama tutarsa yeniden değerlendirilir. Buna karşılık **LLM maliyet koruması** (önbellek, ucuz model, kota, günlük bütçe tavanı, ücretsiz yedek arama) artık **Faz 3'ün zorunlu parçasıdır** → §3.10.
> **Sürüm notu (v1.5):** **LLM katmanı sağlayıcı-bağımsızdır.** Başlangıç sağlayıcısı **Google Gemini ücretsiz katmanı** (Flash-Lite); sonuç kalitesi geçiş kriterini sağlamazsa **Claude Haiku 5.5**'e (ücretli, çok ucuz) tek ayarla geçilir. Zincir: `gemini → classic` (varsayılan); LLM erişilemezse veya kota dolarsa AI'sız **klasik arama**. Ücretsiz katmanda istekler sağlayıcı tarafından ürün geliştirmede kullanılabildiği için **gizlilik metninde belirtilir** ve LLM'e kişisel veri gönderilmez → §3.10.
> **Sürüm notu (v1.6):** **Sosyal katman eklendi (gizlilik-öncelikli):** herkese açık **profil** (isteğe bağlı), **kişisel listeler/sıralamalar** (örn. "Top 10 Nolan"), **defter paylaşımı** (salt-okunur, iptal edilebilir bağlantı), ve **"Birlikte Seç"** (iki kişinin izlenecek listesinden ortak film seçimi + Şans Globu). Her şey **varsayılan özel**dir; yorum, mesajlaşma ve fotoğraf yükleme **yoktur** (moderasyon yükü ve hukuki risk nedeniyle). Yeni bölüm: §3.11; yeni fazlar: **Faz 7C**, **Faz 7D (opsiyonel)**.
> **Sürüm notu (v1.8):** **Sıfır Ödeme Politikası.** Proje bir **deneme/prototip** ve gelirsizdir; hedef altyapıda **hiç para ödememek**. Barındırma: **Vercel Hobby** (web arayüzü + Django, Python fonksiyonu olarak) + **Neon ücretsiz PostgreSQL** + **Gemini ücretsiz katman**. DigitalOcean ve Redis planlardan çıkarıldı (Redis isteğe bağlı). Kart/fatura hesabı gerektiren hiçbir servis kullanılmaz; ücretli plana geçiş yalnızca kullanıcının açık onayıyla olur. Faz 0'a **barındırma denemesi (spike)** eklendi: Django'nun Vercel + Neon üzerinde gecikmesi ölçülür, kötü çıkarsa yedek plana geçilir → **Faz 0, Faz 9, ADR 0002**.

---

## 0. AJAN İÇİN ALTIN KURALLAR (Her fazdan önce oku)

1. **Faz faz ilerle.** Bir fazın "Kabul Kriterleri" tamamen sağlanmadan sonraki faza GEÇME.
2. **Her fazın sonunda dur** ve kullanıcıya kısa bir özet + çalıştırma/test komutlarını ver. Onay gelmeden yeni faza başlama.
3. **Küçük, sık commit.** Her mantıksal birim (bir endpoint, bir bileşen, bir test seti) ayrı commit olsun. Tek dev commit YASAK.
4. **Sırları asla commit'leme.** API anahtarları, DB şifreleri `.env` içinde kalır; repoda sadece `.env.example` bulunur.
5. **Test yazmadan özellik bitmiş sayılmaz.** Her faz kendi testlerini içerir.
6. **Emin olmadığın bir karar varsa varsayım yapma, sor.** Özellikle: veri lisansı, ücretli servis, deploy maliyeti.
7. **Hata olursa:** önce logu oku, kök nedeni bul, düzelt. Testi silerek/atlayarak "yeşile çevirme".
8. **Her faz sonunda** `README.md` ve `docs/` güncellenir.
9. **Sıfır Ödeme Politikası (v1.8).** Hiçbir servise ödeme yöntemi (kart) ekletme, hiçbir servisi ücretli plana geçirme, ücretli alan adı/sertifika/izleme/analitik servisi ekleme. Bir servis kart veya fatura hesabı isterse **dur ve kullanıcıya sor**. Yeni bir servis eklemeden önce ücretsiz planının güncel limitlerini resmi sayfadan doğrula ve `docs/cost.md`'ye yaz. Limit dolunca davranış **ücretsiz ve zarif** olmalı (klasik aramaya düşme, önbellekten sunma); asla fatura çıkarabilecek bir yola düşmemeli.

---

## 1. ÜRÜN TANIMI

### 1.1 Vizyon
Kullanıcı siteye girer, premium ve modern bir arayüzle karşılaşır. Doğal dille ne izlemek istediğini yazar; sistem anlar ve nedenleriyle birlikte **film veya dizi** önerir.

### 1.2 Çekirdek Özellikler

| # | Özellik | Örnek |
|---|---------|-------|
| F1 | **Doğal dille film/dizi arama** | "Silahlı çatışma var ama istihbarat da işin içinde olsun" |
| F2 | **Duygu/tür karması** | "Gerilim olsun ama korku içermesin, izlerken keyif alayım" |
| F3 | **Oyuncuya göre en iyi film & diziler** | "RDJ'yi seviyorum, en iyi filmlerini sırala" / "Bryan Cranston'ın en iyi dizileri" |
| F4 | **Şans Globu (eğlence)** | Butona bas → dünya döner → favori film veya dizilerinden biri çıkar |
| F5 | **Favoriler & izleme listesi** | Film/dizi kaydet, sonra Şans Globu'nda kullan |
| F5b | **Tür filtresi: Film / Dizi / Hepsi** | Aramada tek tıkla geçiş; sorguda "dizi olsun", "kısa film" gibi ifadeler otomatik algılanır |
| F5c | **Diziye özel bilgiler** | Sezon/bölüm sayısı, devam ediyor/bitti durumu, bölüm süresi, "maratona uygun mu?" etiketi |
| F6 | **Yalnızca Web (responsive)** | Vue.js web; telefon/tablet tarayıcılarında tam uyumlu. Native mobil uygulama yok (v1) |
| F7 | **Çift dil: Türkçe / English** | Dil değiştirici; arayüz, film/dizi başlık-özet verisi, arama sorguları ve "neden önerildi?" metinleri seçilen dilde |
| F8 | **Hazır Koleksiyonlar (kürasyonlu kategoriler)** | "Sıkılmam diyeceğiniz filmler", "Sürükleyici", "Çerezlik", "Kafanızı dağıtacak", "Başladığı gibi bitecek", "Tersköşe" |
| F9 | **Oyuncu filmografisi** | Her oyuncunun sayfasında tüm film/dizileri; **kronolojik** (eski→yeni / yeni→eski) ve **en güncel** sıralama |
| F10 | **Yakında Çıkacaklar & Hatırlatıcı** | Vizyona/yayına girecek film ve diziler listesi; "Hatırlat" ile bildirim/e-posta |
| F11 | **İsteğe bağlı giriş (misafir + üye)** | Giriş zorunlu değil: herkes hesapsız arar, keşfeder, Şans Globu'nu kullanır. Giriş yapan ek özellikler kazanır |
| F12 | **Film Defterim (kişisel not defteri)** | Giriş yapan kullanıcı film/diziyi *izlenecek / izleniyor / izledim / bıraktım* olarak işaretler, puan verir, özel not yazar, kendi istatistiklerini görür |
| F13 | **Gelir modeli — ⏸️ ERTELENDİ** | Şimdilik reklam, abonelik, affiliate veya bağış **yok**; ürün ücretsiz. Uygulama büyürse Faz 10 + TMDB ticari lisansı ile yeniden ele alınır |
| F14 | **Maliyet koruması (AI arama)** | Önbellek + ucuz model + kota + günlük bütçe tavanı; bütçe dolunca AI'sız klasik arama açık kalır (§3.10) |
| F15 | **Profil & kişisel listeler** | Üye kendine ait sayfa açar (`/u/kullanici`), kendi sıralamalarını ("En sevdiğim 10 gerilim") oluşturur, sürükle-bırak sıralar; görünürlük: özel / bağlantıyla / herkese açık |
| F16 | **Defter paylaşımı & topluluk puanı** | Defterini salt-okunur bağlantıyla birine gönderir (notlar ayrıca ve bilinçli seçilirse); yapım sayfasında anonim topluluk ortalaması + (herkese açık seçenlerin) puanları |
| F17 | **Birlikte Seç (opsiyonel, Faz 7D)** | İki kişi "izlenecek" listelerini birleştirir, ortak filmleri görür, Şans Globu ortak havuzdan seçer; "zevk uyumu" gösterilir |

### 1.3 Kapsam Dışı (v1)
Film/dizi izletme (streaming), **herkese açık yorum/tartışma, mesajlaşma (DM), fotoğraf/avatar yükleme, kullanıcı içeriğinin otomatik "trend" keşfi** (moderasyon hazır olana kadar), **native mobil uygulama**. (Profil, liste, paylaşım ve isteğe bağlı takip kapsam **içindedir**, bkz. §3.11.) **Reklam, abonelik, affiliate, bağış ve ödeme sistemi v1'de yoktur** (ürün ücretsizdir; Faz 10 ertelendi). (Şimdilik yok.)

---

## 2. TEKNOLOJİ KARARLARI (Gerekçeli)

| Katman | Seçim | Neden |
|--------|-------|-------|
| Backend | **Django 5 + Django REST Framework** | Olgun, güvenli varsayılanlar, admin paneli, PostgreSQL ile mükemmel uyum, ORM/migration |
| Veritabanı | **PostgreSQL 16** — barındırma: **Neon ücretsiz plan** (kart gerekmez; 1 GB/proje, 100 CU-saat/ay, 5 dk kullanılmazsa uyur) | İlişkisel veri. Serverless'a uygun bağlantı için Neon'un **pooled** bağlantı adresi kullanılır. Yerelde Docker PostgreSQL |
| Film & dizi verisi | **TMDB API** | Kapsamlı film, dizi, oyuncu ve anahtar kelime verisi (`/movie` ve `/tv` endpointleri) |
| Doğal dil anlama | **Sağlayıcı-bağımsız LLM katmanı (`LLMProvider` arayüzü)** — başlangıç: **Gemini ücretsiz katman (Flash-Lite)**; yedek/yükseltme: **Claude Haiku 5.5** | Kullanıcı cümlesini yapılandırılmış filtreye çevirir. Sağlayıcı `.env`'den seçilir; kodda sabit değildir (§3.10) |
| Web frontend | **Vue 3 + Vite + TypeScript + Pinia + Vue Router** | İstenen; hızlı ve modern |
| Stil | **Tailwind CSS** + özel tasarım tokenları | Premium görünüm için tutarlı sistem |
| Animasyon | **GSAP** (UI) + **three.js / globe.gl** (küre) | Şans Globu için |
| SEO / render | **SSR veya prerender (Nuxt 3 *ya da* Vite SSG/prerender — ajan ADR ile seçsin)** | Kullanıcıların çoğu arama motorundan gelir; koleksiyon, oyuncu, detay ve yakında çıkacaklar sayfalarının arama motoruna HTML olarak sunulması gerekir. Saf SPA bu açıdan zayıf |
| Gelir | **Şimdilik yok (ücretsiz ürün)** | TMDB'nin ücretsiz API'si ticari olmayan projeler içindir; gelir modeli ileride, TMDB lisansıyla birlikte değerlendirilir (§3.9, Faz 10 — ertelendi) |
| LLM modeli | **Gemini Flash-Lite (ücretsiz katman) → gerekirse Claude Haiku 5.5** | Ücretsiz katmanda maliyet $0 ama hız sınırlı, garantisiz ve istekler Google tarafından ürün geliştirmede kullanılabilir. Haiku 5.5 ücretli ama arama başına ≈ $0,0006 (§3.10). Model kimlikleri env'den okunur |
| Cache & sayaçlar | **Django veritabanı önbelleği + veritabanı sayaç tabloları** (Redis **yok**; ileride gerekirse isteğe bağlı) | Serverless fonksiyonlar arasında bellek paylaşılmaz; önbellek, kota ve bütçe sayaçları veritabanında tutulur. Ücretsiz ve ek servis gerektirmez. Redis'in ücretsiz planı (ör. aylık 500.000 komut) sayaçlar için yetmeyebilir |
| Deploy (web + API) | **Vercel Hobby** — Vue arayüzü ve Django (Vercel'in Python çalışma zamanı, WSGI) tek projede | Ücretsiz, kart gerekmez, uyku/soğuk başlangıç dakikalar değil saniyeler mertebesinde (**spike ile ölçülecek**). Hobby ticari olmayan kullanım içindir (bkz. TMDB notu); ek kullanım satın alınamaz → fatura çıkmaz |
| Yedek deploy planı | **Render ücretsiz web servisi** (15 dk sonra uyur, ~1 dk soğuk başlangıç) veya **Google Cloud Run** (ücretsiz kota ama fatura hesabı gerekir → **yalnızca kullanıcı onayıyla**) | Vercel denemesi kötü çıkarsa. Kod değişmez: `Dockerfile` korunur (taşınabilirlik) |
| CI/CD | **GitHub Actions** | Test + deploy otomasyonu |
| Test | pytest, Vitest, Playwright | Her katman için |

> **Not (lisans — v1.3'te kritik):** TMDB API'si **ticari olmayan** projeler için ücretsizdir ve **atıf (TMDB logosu + "This product uses the TMDB API but is not endorsed or certified by TMDB." metni) zorunludur**. TMDB API kullanım şartları, **reklam dahil gelir elde eden** bir sitede TMDB verisi kullanmayı, ücret alınan erişimi ve TMDB verisiyle AI/ML eğitimini açıkça **ticari kullanım** sayar; bunun için TMDB ile **yazılı ticari anlaşma** gerekir (ücret içerebilir). Şartlar ayrıca TMDB verisinin **en fazla 6 ay** önbellekte/depoda tutulmasına izin verir (Faz 2 ve Faz 7B'deki 6 ay kuralı). **Karar (v1.4): proje şimdilik ücretsiz ve ticari olmayan olarak yürür.** Ajan: (1) Faz 2'de atıfı footer/Hakkında bölümüne koysun, (2) **reklam, abonelik, affiliate, bağış butonu gibi gelir getiren hiçbir öğe eklemesin** (gelir getiren her şey TMDB'ye sorulmadan eklenmez), (3) gelir modeline geçilecekse önce kullanıcıdan TMDB ticari lisansını/yazılı onayını istesin.

---

## 3. MİMARİ

```
   ┌──────────────────────────────┐
   │ Vue Web (SSR/prerender, PWA* )│   * PWA opsiyonel, v2
   │ misafir + üye (isteğe bağlı) │
   └──────────────┬───────────────┘
                  ▼
      ┌──────────────────┐
      │ Django REST API  │──► LLM sağlayıcısı: Gemini (ücretsiz) / Haiku 5.5
      │  (/api/v1/...)   │──► TMDB API (film & dizi verisi)
      └───────┬──────────┘
              ▼
      PostgreSQL (Neon; önbellek ve kota sayaçları da burada)
```

### 3.1 Doğal Dil Arama Akışı (KRİTİK)

1. Kullanıcı yazar: *"Silahlı çatışma olsun ama istihbarat da olsun"*
2. Backend, seçili LLM sağlayıcısına (§3.10) sistem prompt'uyla gönderir; LLM **yalnızca JSON** döner (sağlayıcının yapılandırılmış çıktı/response schema özelliği kullanılır, yine de Pydantic ile doğrulanır):
```json
{
  "intent": "discover",
  "media_type": "both",
  "genres_include": ["Action", "Thriller"],
  "genres_exclude": [],
  "keywords": ["spy", "espionage", "intelligence agency", "shootout"],
  "moods": ["intense"],
  "people": [],
  "year_range": null,
  "min_rating": 6.5,
  "language_hint": "tr"
}
```
   - `media_type`: `movie` | `tv` | `both`. Kullanıcı belirtmezse `both`. "dizi olsun", "sezonluk", "bölüm bölüm" → `tv`; "film", "2 saatlik" → `movie`.
   - Dizi ek alanları (opsiyonel): `episode_runtime_max`, `max_seasons`, `status` (`ongoing`/`ended`), `binge_friendly`.
3. Backend JSON'u **Pydantic ile doğrular** (geçersizse fallback: basit anahtar kelime araması).
4. TMDB `discover/movie` ve/veya `discover/tv` + `keyword` + `person` endpointleri ile aday yapımlar çekilir.
   - **Dikkat:** TMDB'de film ve dizi tür ID'leri farklıdır (örn. dizide *Action & Adventure*, *Sci-Fi & Fantasy* birleşik türleri var). Ajan bir **genre mapping tablosu** yazsın: tek bir mantıksal tür → film ID'si + dizi ID'si.
   - `media_type=both` ise iki sorgu paralel atılır, sonuçlar tek listede birleştirilir.
5. Adaylar; puan, oy sayısı ve anahtar kelime eşleşmesine göre sıralanır. **Dizi ve film oy sayıları farklı ölçekte olduğu için güven eşikleri ayrı ayarlanır** (bkz. §3.2).
6. Her sonuç için **1 cümlelik "Neden önerildi?"** açıklaması üretilir (toplu tek LLM çağrısı, maliyet için).
7. Sonuçlar cache'lenir (sorgu hash'i ile).

**Güvenlik:** Kullanıcı girdisi LLM'e "veri" olarak verilir; sistem prompt'u talimat değiştirmeye karşı sağlamlaştırılır. LLM çıktısı asla doğrudan çalıştırılmaz, sadece doğrulanmış filtre olarak kullanılır. Rate limit zorunlu.

### 3.2 Oyuncu Araması & Sıralama Kuralları
- "RDJ", "Robert Downey Jr." gibi takma adları LLM çözer → TMDB `person/search` ile doğrulanır.
- `combined_credits` çekilir (film **ve** dizi birlikte gelir); sıralama: `vote_average` **ama** minimum oy eşiği ile (az oyla şişmiş puanları elemek için) ve oyuncu **başrol/ilk 5 oyuncu** içinde.
- **Oy eşikleri (başlangıç değeri, konfigüre edilebilir):** film `vote_count >= 1000`, dizi `vote_count >= 300`. Dizilerde oy sayısı genelde daha düşüktür; aynı eşik iyi dizileri haksız yere eler.
- Diziler için oyuncunun **bölüm sayısı** kontrol edilir (`episode_count >= 3`); tek bölümlük konuk oyunculuklar listeden çıkarılır.
- Kullanıcı sadece film ya da sadece dizi isterse filtrelenir; istemezse **iki ayrı bölüm** halinde döner: "En iyi filmleri" ve "En iyi dizileri".
- Sonuç: her bölümde en iyi 10'a kadar yapım + kısa gerekçe.

### 3.3 Şans Globu
- Kaynak: kullanıcının favori film ve dizileri (giriş yoksa tarayıcıda localStorage, giriş varsa DB). Üyeler ayrıca **"İzleme listemden (İzlenecekler)"** kaynağını seçebilir; "izlediklerimi hariç tut" varsayılan açıktır (bkz. §3.8).
- Kullanıcı isterse globe üzerinde **Film / Dizi / Hepsi** filtresi seçebilir.
- Boşsa: "Önce birkaç film veya dizi favorile" yönlendirmesi + popüler film/dizilerden demo modu.
- Animasyon: 3D dünya küresi, butona basınca ease-out ile hızlanıp yavaşlayarak döner; durunca seçilen yapımın afişi küreden "fırlar" (scale + glow) ve detay kartı açılır.
- Rastgelelik backend'de değil frontend'de yapılabilir; ama "aynısı tekrar çıkmasın" kuralı (son 3 seçimi hariç tut) uygulanır.
- `prefers-reduced-motion` açıksa animasyon sade fade'e düşer.

### 3.4 Çift Dil (TR / EN) — Uçtan Uca
Dil sadece buton etiketlerinden ibaret değildir; dört katmanda ele alınır:

1. **Arayüz metinleri:** Web `vue-i18n`. Çeviri anahtarları tek kaynaktan (`docs/i18n/keys.md`) yönetilir; metin kodun içine gömülmez.
2. **İçerik verisi:** Tüm API uçları `?lang=tr|en` (veya `Accept-Language`) kabul eder; TMDB'ye `language=tr-TR` / `en-US` olarak iletilir. **Fallback:** Türkçe özet/başlık boşsa İngilizceye düşülür (TMDB'de birçok yapımın TR özeti yoktur) ve arayüzde belli edilir.
3. **Arama & LLM:** Kullanıcı hangi dilde yazarsa yazsın sorgu anlaşılır (`language_hint` zaten var). "Neden önerildi?" açıklamaları **seçili arayüz diline** göre üretilir. Cache anahtarına `lang` eklenir (aksi halde TR cevabı EN kullanıcıya gider).
4. **Koleksiyon & etiket metinleri:** Koleksiyon adı/açıklaması, tür adları, rozetler iki dilli saklanır (`name_tr`, `name_en`).

**Kurallar**
- Varsayılan dil: tarayıcı diline (`Accept-Language`) göre, yoksa `tr`. Seçim kalıcı (localStorage / kullanıcı profili).
- URL stratejisi (web): `/tr/...` ve `/en/...` önekleri (SEO için `hreflang` etiketleri).
- Tarih, sayı, süre formatları locale'e göre (`Intl`).
- Yeni bir dil eklemek yalnızca çeviri dosyası eklemek anlamına gelmeli (ileride genişletilebilir).

### 3.5 Hazır Koleksiyonlar (Kürasyonlu Kategoriler)
Kullanıcı yazmadan, tek tıkla keşfetsin diye hazır "ruh hali / izleme niyeti" kategorileri. Her koleksiyon bir **filtre tarifi (recipe)**dir; liste elle değil, kuraldan üretilir ve istenirse editör tarafından ince ayar yapılır.

**Başlangıç koleksiyonları** (kullanıcı listesi + önerilen eklemeler)

| Slug | TR ad | EN ad | Fikir (tarif özeti) |
|------|-------|-------|---------------------|
| `never-boring` | Sıkılmam Diyeceğiniz Filmler | Films You Won't Get Bored Of | Yüksek tempo, kısa-orta süre (≤ 125 dk), yüksek puan + yüksek oy; Action/Thriller/Adventure ağırlıklı |
| `immersive` | Sürükleyici Filmler | Immersive Films | Atmosfer/dünya kurgusu güçlü; Sci-Fi/Drama/Mystery/Fantasy, keyword: `immersive`, `dystopia`, `survival`, `psychological` |
| `snack-watch` | Çerezlik Filmler | Easy Snack Watches | Hafif, düşündürmeyen; Comedy/Family/Animation/Romance, süre ≤ 110 dk, ağır temalar (Horror, War, Crime-dark) hariç |
| `switch-off` | Kafanızı Dağıtacak Filmler | Mind-Clearing Films | Rahatlatıcı/eğlenceli; Comedy, Adventure, Music, Feel-good keyword'leri, düşük gerilim |
| `start-to-finish` | Başladığı Gibi Bitecek Filmler | Starts Strong, Ends Strong | Başı sonu tutarlı, tempo düşmeyen, ≤ 110 dk, tek oturumluk; "tek seferde bitir" etiketi |
| `curveball` | Tersköşe Filmleri | Curveball Films | Beklenmedik son, **plot twist**, kafa karıştıran/beklentiyi tersine çeviren kurgu; keyword: `plot twist`, `twist ending`, `mind-bending`, `unreliable narrator` |
| *(öneri)* `date-night` | Randevu Gecesi | Date Night | Romance/Comedy/Drama, orta tempo |
| *(öneri)* `hidden-gems` | Gizli Hazineler | Hidden Gems | Yüksek puan (≥ 7.3) ama düşük/orta oy sayısı (örn. 300–5000) |
| *(öneri)* `true-story` | Gerçek Hikâyeler | Based on True Stories | keyword: `based on true story`, Drama/History/Biography |
| *(öneri)* `mind-benders` | Beyin Yakanlar | Mind Benders | Sci-Fi/Mystery + `time loop`, `dream`, `simulated reality` |
| *(öneri)* `cozy-rainy-day` | Yağmurlu Gün Filmleri | Rainy Day Watches | Sıcak, yavaş tempo, Drama/Romance/Animation |
| *(öneri)* `binge-worthy` | Maratonluk Diziler | Binge-Worthy Series | `media_type=tv`, kısa bölümler, bitmiş diziler, yüksek puan |
| *(öneri)* `one-sitting` | Tek Oturumluk | One Sitting | ≤ 95 dk filmler / ≤ 6 bölümlük mini diziler |

> Ajan notu: Bu liste **başlangıç taslağıdır**. Kullanıcıya listeyi onaylatmadan seed'leme. "(öneri)" satırları isteğe bağlıdır.

**Teknik tasarım**
- Model: `Collection` (`slug`, `name_tr`, `name_en`, `description_tr/en`, `icon`, `cover_title` (opsiyonel), `media_type` (`movie`/`tv`/`both`), `recipe` JSON, `is_active`, `sort_order`, `editor_pins`, `editor_blocklist`).
- `recipe` şeması **Pydantic ile doğrulanır** (türler, hariç türler, keyword'ler, `runtime_min/max`, `min_rating`, `min_votes`, `vote_count_max`, `sort_by`, `year_range`, `episode_runtime_max`, `status`).
- Üretim: `recipe` → TMDB discover → `Ranker` → cache (6–24 saat). Editör **sabitleme (pin)** ile bazı yapımları öne çıkarabilir, **blocklist** ile uygunsuzları çıkarabilir (Django admin üzerinden).
- Subjektif koleksiyonlar (Tersköşe, Sürükleyici…) için **LLM doğrulama adımı (opsiyonel, toplu & cache'li):** aday listesi LLM'e verilir, "bu yapım koleksiyon temasına uyuyor mu?" 0–1 skor + tek cümle gerekçe döner. Maliyet için günde bir kez ön-hesaplanır (cron/management command), istek anında LLM çağrılmaz.
- **Spoiler kuralı:** "Tersköşe" gerekçeleri asla sürprizi açık etmez ("beklenmedik bir final sunar" gibi).
- Koleksiyon sonuçları sayfalanır; Şans Globu "bu koleksiyondan rastgele seç" modunu da destekler.
- Endpointler: `GET /api/v1/collections/` (liste), `GET /api/v1/collections/{slug}/?media_type=&page=&lang=`.

### 3.6 Oyuncu Filmografisi (Kronolojik & Güncel)
Faz 4'teki "en iyi" sıralamasına **ek olarak** tam filmografi görünümü:

- Kaynak: TMDB `person/{id}/combined_credits` (film + dizi tek çağrıda).
- **Sıralama modları** (`sort` parametresi): `newest` (en güncel → varsayılan), `oldest` (kronolojik, eskiden yeniye), `rating` (en iyi), `popularity`.
- Tarih alanı: film için `release_date`, dizi için `first_air_date`. **Tarihi olmayan** kayıtlar listenin sonuna konur (hata vermez).
- **Henüz çıkmamış** yapımlar (gelecek tarihli) filmografide ayrı bir "Yakında" grubunda gösterilir ve Yakında Çıkacaklar özelliğine (bkz. §3.7) bağlanır (hatırlatıcı eklenebilir).
- Filtreler: Film / Dizi / Hepsi; rol türü (Oyuncu / Yönetmen / Yapımcı / Senarist – `crew` desteklenirse); "yalnızca başrol/ilk 5 oyuncu" anahtarı (varsayılan açık; kapatılırsa tüm krediler gelir).
- **Gürültü temizliği:** `character` alanı `Self`, `Himself/Herself`, `Archive Footage`, `Uncredited` olan kayıtlar ve talk-show/ödül töreni/haber programı türleri (`Talk`, `News`, `Reality` için ayar) varsayılan olarak gizlenir; "Tümünü göster" ile açılabilir.
- Dizilerde `episode_count` ile birlikte yıl aralığı gösterilir (örn. 2008–2013, 62 bölüm).
- Sayfalama / "daha fazla yükle"; tamamı cache'lenir (oyuncu kredisi 24 saat).
- Endpoint: `GET /api/v1/people/{tmdb_id}/filmography/?sort=newest|oldest|rating|popularity&media_type=&lead_only=&page=&lang=`
- Ek: oyuncu detay sayfası (biyografi kısa özet, doğum yılı, fotoğraf, bilinen yapımlar). Biyografi `lang`'e göre; yoksa EN fallback.

### 3.7 Yakında Çıkacaklar & Hatırlatıcı
**Liste**
- Kaynak: TMDB `discover/movie` (`primary_release_date.gte=bugün`), `movie/upcoming` ve diziler için `discover/tv` (`first_air_date.gte=bugün`) + yeni sezon bilgisi olan, `on_the_air`/`airing_today` devam eden diziler. Ülke bölgesi (`region=TR`) ile Türkiye vizyon tarihi tercih edilir; yoksa global tarih.
- Görünüm: tarihe göre gruplu (Bu hafta / Bu ay / Gelecek aylar), Film / Dizi / Hepsi filtresi, tür filtresi, "tarihi kesinleşmemiş" yapımlar ayrı grupta.
- **Veri güvenilirliği:** Çıkış tarihleri değişebilir. Liste cache süresi kısa (**3–6 saat**); kayıtlı hatırlatıcıların tarihi günlük bir job ile yeniden kontrol edilir, tarih değişirse kullanıcı bilgilendirilir.
- Gerekirse ayrı `UpcomingTitle` görünümü/materialized cache; "çıktı" olanlar otomatik listeden düşer.

**Hatırlatıcı (Reminder)**
- Model: `Reminder` (`user`, `media_type`, `tmdb_id`, `remind_on` (`release_day` | `one_day_before` | `one_week_before`), `channels` (`email`, `push`, `in_app`), `status` (`pending`/`sent`/`cancelled`), `last_known_release_date`).
- Zamanlayıcı: günlük çalışan job. Serverless'ta sürekli çalışan işçi (Celery) yok. Seçenek 1: **Vercel Cron** ile korumalı bir endpoint (`CRON_SECRET`) günde bir tetiklenir (ücretsiz planda izinli cron sıklığı ve sayısını **ajan resmi dokümandan doğrulasın**; günde bir yeterli). Seçenek 2 (yedek): **GitHub Actions zamanlanmış workflow** aynı korumalı endpoint'i çağırır (kota ücretsiz limit içinde kalmalı). İş **idempotent** ve kısa süreli olmalı (fonksiyon süre sınırı); büyük işler küçük gruplara bölünür. Ajan seçimi **ADR** ile kaydeder.
- Kanallar (öncelik sırasıyla): **uygulama içi bildirim** → **e-posta** → **web push** (VAPID, opsiyonel). Mobil push yok (native uygulama kapsam dışı).
- **Giriş zorunluluğu:** Hatırlatıcı hesaba bağlıdır (Faz 7'ye bağımlı). Misafir kullanıcı "Hatırlat"a basarsa giriş/kayıt'a yönlendirilir; seçim giriş sonrası otomatik tamamlanır.
- Kullanıcı hatırlatıcıları listeleyebilir/iptal edebilir. Aynı yapım için mükerrer hatırlatıcı engellenir (unique: `user + media_type + tmdb_id`).
- Bildirim dili kullanıcının dil tercihinde (TR/EN). Her e-postada tek tıkla abonelikten çıkma (KVKK/GDPR).
- Endpointler: `GET /api/v1/upcoming/?media_type=&genre=&month=&page=&lang=`, `POST/GET/DELETE /api/v1/reminders/`.

### 3.8 Erişim Modeli (Misafir / Üye) & Film Defterim
**Temel ilke: Giriş hiçbir zaman keşfin önünde bir duvar değildir.** Arama, koleksiyonlar, oyuncu sayfaları, yakında çıkacaklar ve Şans Globu **hesapsız** çalışır. Giriş, kişisel veriye ve cihazlar arası senkrona değer katar.

| Özellik | Misafir | Üye (ücretsiz) |
|---------|:------:|:--------------:|
| Doğal dille arama, koleksiyonlar, oyuncu sayfaları, yakında çıkacaklar | ✅ | ✅ |
| Şans Globu (kaynak: popüler / koleksiyon) | ✅ | ✅ |
| Favoriler | ✅ (yalnızca bu tarayıcıda, localStorage) | ✅ (hesapta, her cihazda) |
| Günlük AI arama kotası (LLM maliyet koruması) | Düşük | Daha yüksek |
| **Film Defterim** (durum, puan, not, istatistik) | ❌ (denemek isteyene "ücretsiz hesap aç" yönlendirmesi) | ✅ |
| Hatırlatıcılar (Yakında Çıkacaklar) | ❌ (giriş yönlendirmesi) | ✅ |
| Şans Globu kaynağı: "İzlenecek listem" | ❌ | ✅ |
| "İzlediklerimi hariç tut" filtresi (arama, koleksiyon, globe) | ❌ | ✅ |
| Reklam | Yok (ürün ücretsiz ve reklamsız; Faz 10 ertelendi) | Yok |

**Yumuşak kapı (soft gate):** Misafir "puan ver", "not ekle" veya "izledim" dediğinde sayfa kaybolmaz; küçük bir modal "Defterin için ücretsiz hesap aç" gösterir. Giriş/kayıt sonrası **bekleyen işlem otomatik tamamlanır** (hatırlatıcıdaki mantıkla aynı).

**Film Defterim — Veri Modeli**
Tek bir kayıt tipi tüm kişisel durumu taşır (Favori + İzleme listesi + Puan + Not ayrı tablolar olmaz):

`NotebookEntry` — `user`, `media_type`, `tmdb_id` (**birlikte unique** `user + media_type + tmdb_id`), `status` (`want_to_watch` | `watching` | `watched` | `dropped` | `null`), `is_favorite` (bool), `rating_x2` (1–10 arası tamsayı; arayüzde **0,5–5 yıldız**, 0,5'lik adımlar; kayan nokta hatası olmasın diye ×2 saklanır; `null` = puanlanmadı), `note` (özel metin, en çok 5000 karakter), `tags` (kullanıcı etiketleri, en çok 10), `watched_on` (tarih, opsiyonel), `rewatch_count`, `created_at`, `updated_at`, `title_snapshot` (başlık, poster yolu, tür, süre — TMDB kapalıyken bile defter açılsın ve istatistik hesaplansın diye; periyodik yenilenir, TMDB şartları gereği **hiçbir snapshot 6 aydan eski kalmaz**).
- Diziler için: `progress_season`, `progress_episode` (Faz 7'deki ilerleme takibi bu modelde birleşir). Bölüm bazlı puan v1'de yok.
- Notlar **varsayılan özeldir**; yalnızca sahibinin bilinçli olarak oluşturduğu paylaşım bağlantısında ve ayrı bir "notları dahil et" seçimiyle başkasına görünebilir (§3.11, Faz 7C). Not metni **düz metin** olarak render edilir (XSS koruması), LLM'e **asla** gönderilmez.

**Defter Ekranları**
- **Liste:** sekmeler *İzlenecekler / İzleniyor / İzlediklerim / Bıraktıklarım / Favoriler*; sıralama (son eklenen, puanım, izleme tarihi, yapım yılı); filtre (film/dizi, tür, puan aralığı, etiket); defter içi arama.
- **Hızlı işlem:** Her `TitleCard` ve detay sayfasında durum rozeti + yıldız seçici + "Not ekle"; sonuç kartlarında *"İzledin ✓ · Puanın 4,5★"* gösterimi.
- **İstatistikler** (`/defterim/istatistik`): toplam izlenen film/dizi, toplam izleme süresi (süreden hesaplanır), ortalama puan, puan dağılımı (histogram), tür dağılımı, aylık/yıllık izleme sayısı, en yüksek puanlıların listesi. "Yıl özeti" sayfası opsiyonel.
- **Dışa/İçe aktarma:** CSV/JSON dışa aktarma (KVKK taşınabilirlik); Letterboxd CSV içe aktarma **opsiyonel** (kullanıcıyla netleştir).
- **Kişiselleştirme (opsiyonel, kullanıcı açarsa):** "Zevkime göre öner" — LLM'e yalnızca **toplulaştırılmış** zevk özeti (en sevilen türler, ortalama puan) gönderilir; notlar ve tam liste gönderilmez. Varsayılan kapalı.

**Endpointler** (hepsi giriş ister, yalnızca kendi verisi)
- `GET /api/v1/me/notebook/?status=&media_type=&rating_min=&rating_max=&tag=&q=&sort=&page=`
- `GET|PUT|PATCH|DELETE /api/v1/me/notebook/{media_type}/{tmdb_id}/`
- `POST /api/v1/me/notebook/lookup/` — gövde: `[{media_type, tmdb_id}, …]`; sonuç listesindeki kartlar için **tek istekte** durum/puan döner (N+1 ve istek fırtınası yok)
- `GET /api/v1/me/notebook/stats/`
- `GET /api/v1/me/notebook/export/?format=csv|json`

### 3.9 Gelir Modeli (Para Kazanma) — ⏸️ ERTELENDİ
> **DURUM (v1.4): Bu bölüm şimdilik UYGULANMAZ.** Ürün ücretsiz ve reklamsızdır. Bölüm, ileride karar verilirse hazır bir yol haritası olarak saklanır. Ajan bu bölümdeki hiçbir maddeyi kullanıcı açıkça "gelir modeline geçelim" demeden uygulamaz.
>
> **Geçiş kontrol listesi (ileride):** (1) TMDB ticari lisansı/yazılı onay, (2) aylık ziyaretçi ve AI arama hacmi + gerçek LLM maliyeti ölçülmüş olmalı (§3.10 metrikleri), (3) SEO/trafik temeli oluşmuş olmalı, (4) karar: reklam mı, Premium mu, ikisi mi, (5) KVKK/CMP hazırlığı.

**Kısa değerlendirme:** Reklam mantıklı bir başlangıçtır ama tek başına yeterli olmayabilir; çünkü geliri **trafik** belirler, trafiği de **SEO** belirler, ve her AI aramasının bir **LLM maliyeti** vardır. Bu yüzden plan üç katmanlıdır; sırayla açılır, her biri bir "özellik bayrağı" (feature flag) arkasındadır.

**Önkoşullar (bunlar sağlanmadan reklam açılmaz)**
1. **TMDB ticari lisans / yazılı onay** (bkz. §2 lisans notu). Bu bir *engeldir*, ayrıntı değil.
2. **Çerez/izin yönetimi (CMP):** reklam ve analitik scriptleri **kullanıcı onayından önce yüklenmez**; KVKK ve (AB/UK ziyaretçileri için) GDPR uyumu. Reklam ağının zorunlu kıldığı sertifikalı CMP gerekiyorsa o kullanılır.
3. **SEO hazırlığı:** SSR/prerender (bkz. §2), `sitemap.xml`, canonical, `hreflang` (TR/EN), yapılandırılmış veri (`Movie`/`TVSeries`/`Person` schema.org), hızlı sayfalar. Reklam ağları ve arama motorları için sayfada **özgün değer** (kürasyon, gerekçeler, koleksiyon metinleri) olmalı; yalnızca TMDB verisini listeleyen "ince" sayfalar hem onay hem sıralama riski taşır.

**Katman 1 — Reklam**
- Başlangıçta onayı kolay ağlar (örn. AdSense/Ezoic benzeri) ile; trafik büyüyünce premium ağlara (Mediavine/Raptive türü) geçiş **sonradan değerlendirilir**. Trafik/gelir eşikleri sık değişir; **ajan karar vermeden önce güncel koşulları kontrol edip kullanıcıya sunsun**. Ağı **kullanıcı seçer**.
- Yerleşim kuralları: hero arama alanında ve Şans Globu animasyonu sırasında reklam **yok**; sonuç listelerinde 6–8 kartta bir doğal yerleşim; detay sayfasında kenar/alt alan; **sayfa kayması (CLS) önlemek için yer ayrılır**; reklamlar lazy-load; reklamlar "Reklam" diye etiketlenir.
- `AdSlot.vue` bileşeni + `ADS_ENABLED` bayrağı; bayrak kapalıyken ağ scriptleri hiç yüklenmez. `ads.txt` yayımlanır.
- Güvenli deneyim: agresif türler (pop-under, tam ekran, otomatik oynayan sesli video) **kullanılmaz** — marka ve Lighthouse için.

**Katman 2 — Affiliate ("Nerede izlenir?")**
- Detay sayfasında hangi yayın platformunda olduğu (TMDB watch providers; **veri sağlayıcısı atfı gerekir**) + uygun iş ortaklığı programı olan platformlara/mağazalara bağlantı. Bağlantılar `rel="sponsored nofollow noopener"` ve **"iş ortağı bağlantısı"** etiketli.
- Hangi programların Türkiye'de geçerli ve veri lisansıyla uyumlu olduğu **araştırılıp kullanıcıya sunulur**; varsayım yapılmaz.
- Sponsorlu koleksiyon (opsiyonel): açıkça **"Sponsorlu"** etiketi, editöryel bağımsızlık kuralı (sıralamayı satın almak yok).

**Katman 3 — Premium (opsiyonel, kullanıcı onaylarsa)**
- Reklamsız deneyim, daha yüksek AI arama kotası, gelişmiş istatistik/yıl özeti, öncelikli dışa aktarma.
- Bu katman **ödeme sistemi** gerektirir (v1 kapsam dışıydı): sağlayıcı (örn. iyzico/Stripe) seçimi, faturalama, KDV, iade, abonelik iptali **kullanıcıyla netleştirilmeden başlanmaz**.

**Ölçüm:** arama başına LLM maliyeti, cache hit oranı, misafir→üye dönüşümü, sayfa başı reklam geliri (RPM), Premium dönüşümü. Hedef: **ziyaretçi başına gelir > ziyaretçi başına (LLM + altyapı) maliyeti**. Bu eşik tutmuyorsa kota sıkılaştırılır veya AI araması üyeye/Premium'a kaydırılır.

### 3.10 Maliyet Modeli & LLM Maliyet Koruması (ücretsiz dönem için ZORUNLU)

**LLM Sağlayıcı Stratejisi (v1.5)**
- **Arayüz:** `LLMProvider` (örn. `parse_query(text, lang) → SearchFilters JSON`, `explain(results, lang) → metinler`). Uygulamalar: `GeminiProvider`, `AnthropicProvider`, `ClassicProvider` (LLM'siz klasik arama). Tüm çağrılar bu arayüzden geçer; iş mantığı hiçbir sağlayıcıya doğrudan bağlı olmaz.
- **Zincir (`LLM_PROVIDER_CHAIN`, env):** varsayılan `gemini,classic`. Sağlayıcı hata/zaman aşımı/429 (hız sınırı)/geçersiz JSON (1 yeniden deneme sonrası) verirse **bir sonrakine düşülür**; kısa süreli **devre kesici (circuit breaker)** aynı sağlayıcıyı bir süre denemez (boşuna bekleme yok); devre kesici durumu serverless'ta bellekte kalmaz, **veritabanında/önbellek tablosunda** tutulur. Haiku 5.5'e geçmek için `LLM_PROVIDER_CHAIN=anthropic,classic` (veya `gemini,anthropic,classic`) yazmak yeterlidir; **kod değişmez**.
- **Başlangıç modeli:** Gemini Flash-Lite (en ucuz/ücretsiz katman; model kimliği `GEMINI_MODEL`, ajan güncel kimliği resmi dokümandan doğrular). Ücretsiz katmanın **sayısal hız sınırları** resmi "rate limits" sayfasından okunur ve `docs/cost.md`'ye yazılır; günlük toplam arama kotası (misafir + üye) bu sınırı aşmayacak şekilde ayarlanır.
- **Geçiş kriteri (kalite kapısı):** Faz 3'te hazırlanan **değerlendirme seti** (9 zorunlu senaryo + en az 20 gerçek Türkçe/İngilizce sorgu) seçili sağlayıcıyla çalıştırılır. Aşağıdakiler sağlanıyorsa Gemini ücretsiz ile devam; sağlanmıyorsa kullanıcıya rapor edilir ve `anthropic`'e geçiş önerilir: (1) geçerli JSON oranı ≥ %95 (yeniden denemesiz ≥ %90), (2) `media_type` doğru ≥ %90, (3) `genres_exclude` ("korku içermesin") ihlali = 0 senaryoda, (4) prompt injection senaryosu geçiyor, (5) ortalama yanıt süresi hedef içinde. Sonuçlar `docs/llm-eval.md`'de tarihli raporlanır; **sağlayıcı değişikliğinden sonra set yeniden çalıştırılır**.
- **Gizlilik (ücretsiz katman):** Sağlayıcının ücretsiz katmanında istekler ürün geliştirmede kullanılabilir (ücretli katmanda kullanılmaz). Bu yüzden: (1) LLM'e **yalnızca arama sorgusu metni** ve gerekli film/dizi meta verisi gider; kullanıcı kimliği, e-posta, IP, **Film Defterim notları/puanları asla gitmez** (testle kanıtlı), (2) arama kutusunda küçük bir not: "Aramalar yapay zekâ sağlayıcısına gönderilir; kişisel bilgi yazmayın", (3) Gizlilik Politikası/KVKK aydınlatma metninde LLM sağlayıcısı ve bu durum açıkça yazılır (Faz 11), (4) "Zevkime göre öner" (opsiyonel kişiselleştirme) ücretsiz katmanla **etkinleştirilmez**; yalnızca ücretli/eğitimde kullanılmayan sağlayıcıyla açılabilir.
- **Ücretsiz katmanın doğası:** Garanti (SLA) yok, limitler ve model adları değişebilir. Bu nedenle sistem her zaman `classic` yedeğiyle çalışır; sağlayıcı çökse bile site açık kalır.

**Hangi çağrı para harcar?** TMDB ücretsiz API'si arama başına para istemez. Para yalnızca **ücretli LLM API** çağrılarından gider. **Başlangıçta Gemini ücretsiz katmanı kullanıldığı için fiilî LLM maliyeti $0'dır**; ücretli sağlayıcıya (Claude Haiku 5.5 vb.) geçilirse kullanıma göre faturalanır (API faturalaması, claude.ai Pro/Max aboneliğinden ayrıdır). **Altyapı hedefi $0'dır** (Vercel Hobby + Neon ücretsiz + ücretsiz alt alan adı); ücretsiz limitler ve dolunca davranış `docs/cost.md`'de belgelenir. Özel alan adı ücretlidir; kullanıcı istemedikçe alınmaz.

> **Not (v1.5):** Aşağıdaki tablo **ücretli** seçeneklerin maliyetidir. Varsayılan başlangıçta Gemini ücretsiz katmanı kullanıldığı için fiilî LLM maliyeti **$0**'dır; tablo, ücretsiz katman yetmezse veya kalite kapısı geçilmezse neyle karşılaşılacağını gösterir.

**Arama başına tahmini maliyet** (fiyatlar: Claude Haiku 5.5 → giriş $0,10 / çıkış $0,50; Claude Sonnet 5.5 → giriş $2 / çıkış $10, her ikisi 1 milyon token başına; **Ajan göstermeden önce güncel fiyatı resmi dokümandan yeniden doğrulasın**)

Varsayım (önbelleğe takılmayan bir "doğal dil arama"): 2 LLM çağrısı → (1) sorguyu filtreye çevirme ≈ 900 giriş + 200 çıkış token, (2) 10 sonuç için toplu "neden önerildi?" ≈ 1.500 giriş + 500 çıkış token. Toplam ≈ **2.400 giriş + 700 çıkış token**. Türkçe daha fazla token tüketir; gerçek değer **ölçülmeli**, aşağıdaki rakamlar tahmindir (gerçek maliyeti 1×–2× aralığında düşünün).

| Senaryo | 1 arama | 1.000 arama | 10.000 arama/ay | 100.000 arama/ay |
|---------|--------:|------------:|----------------:|-----------------:|
| Haiku 5.5, 2 çağrı (ayrıştırma + açıklama) | ≈ $0,0006 | ≈ $0,6 | ≈ $6 | ≈ $59 |
| Haiku 5.5, yalnızca ayrıştırma (açıklama şablonla) | ≈ $0,0002 | ≈ $0,2 | ≈ $2 | ≈ $19 |
| Sonnet 5.5, 2 çağrı | ≈ $0,012 | ≈ $12 | ≈ $117 | ≈ $1.170 |

Önbellekten dönen arama **0 LLM maliyetlidir**. Günlük $5'lık bütçe tavanıyla: Haiku 5.5'te günde ≈ 8.500, Sonnet 5.5'te ≈ 430 aramaya yeter.

**Maliyet kontrol merdiveni (hepsi Faz 3'te kurulur)**
1. **Sonuç önbelleği:** sorgu normalize edilir (küçük harf, noktalama/boşluk temizliği, `lang` + `media_type` anahtarda) → aynı sorgu LLM'e gitmez. Hazır sorgu çipleri ve koleksiyonlar ön-ısıtılır (cache warm). Koleksiyon sayfaları **LLM'siz** çalışır.
2. **Ücretsiz/ucuz model:** ayrıştırma ve açıklama varsayılan olarak **Gemini ücretsiz katmanı** ($0). Kalite kapısı (yukarıda) geçilemezse **Claude Haiku 5.5**'e geçilir (tablodaki maliyetler geçerli olur). Model kimlikleri `.env`'den okunur.
3. **Açıklamayı ucuzlat:** "Neden önerildi?" metni varsayılan olarak **şablonla** üretilir (eşleşen tür, anahtar kelime, puan/oy bilgisinden; LLM yok). LLM açıklaması yalnızca ilk 3–5 sonuç için veya kullanıcı "Neden?" düğmesine basınca (lazy) üretilir ve önbelleğe alınır.
4. **Kota:** misafir günlük `GUEST_DAILY_AI_SEARCHES`, üye `USER_DAILY_AI_SEARCHES` (IP/oturum bazlı hız sınırı ayrıca). Çıktı uzunluğu `max_tokens` ile sınırlanır; sorgu uzunluğu üst sınırı (örn. 300 karakter).
5. **Günlük bütçe tavanı (`LLM_DAILY_BUDGET_USD`):** harcama sayacı (veritabanı tablosu; serverless'ta bellek paylaşılmaz) her çağrıda token kullanımından hesaplanır. Tavan dolunca **site kapanmaz**: AI'sız **klasik arama** (tür + anahtar kelime + oyuncu adı + koleksiyonlar) açık kalır, arayüzde nazik bir not gösterilir ("AI arama bugünlük doldu, yarın yenilenir").
6. **Yedek (fallback) arama:** LLM hatası, kota veya bütçe aşımı → mevcut anahtar kelime/tür eşleştirme (zaten Faz 3 gereksinimi). Böylece kullanıcı her zaman bir sonuç görür.
7. **Kötüye kullanım koruması:** IP başına hız sınırı, bot koruması (ör. CAPTCHA/Turnstile benzeri, kullanıcıyla netleştirilir), anormal hacimde otomatik uyarı. Anthropic Console'da hesap/çalışma alanı düzeyinde **harcama limiti/uyarısı** varsa kurulur (Console ayarlarından doğrulanır).
8. **Toplu işlerde indirim:** gecelik koleksiyon doğrulaması gibi acil olmayan işler **Batch API** ile (yaklaşık %50 indirim) çalıştırılır.

**Ölçüm (her LLM çağrısı loglanır, kişisel veri olmadan):** çağrı türü, model, giriş/çıkış token, tahmini maliyet, cache hit/miss, kota/bütçe nedeniyle fallback sayısı. Günlük ve aylık toplam maliyet bir yönetici görünümünde (Django admin) izlenir. Bu veriler ileride gelir modeli kararının girdisidir.

### 3.11 Sosyal Katman: Profil, Listeler, Paylaşım, Birlikte Seç (v1.6)
**Konum:** Film Defterim'in (§3.8) üstüne kurulur. Amaç, Letterboxd benzeri bir "sosyal ağ" olmak değil; insanların zevklerini **tek bağlantıyla paylaşabildiği**, yapay zekâlı keşifle bütünleşen hafif bir katmandır. Fark yaratan kısım: doğal dil arama + Şans Globu + koleksiyonlar + **Birlikte Seç**.

**Gizlilik ilkeleri (pazarlık konusu değil)**
1. **Her şey varsayılan özel.** Profil, liste, puan ve defter başkasına ancak sahibinin bilinçli seçimiyle görünür.
2. Görünürlük 3 kademe: `private` (yalnızca ben) · `unlisted` (bağlantıyı bilen) · `public` (herkes; profil sayfasında listelenir).
3. **Notlar hiçbir koşulda otomatik görünmez.** Yalnızca defter paylaşım bağlantısında "notları dahil et" ayrıca işaretlenirse ve kayıt "kilitli not" değilse görünür.
4. Her paylaşım **iptal edilebilir** ve **süre sınırı** koyulabilir. Hesap silinince tüm herkese açık içerik ve paylaşım bağlantıları kalıcı silinir.
5. Kullanıcı yalnızca kullanıcı adının **tam eşleşmesiyle** aranır (toplu tarama/liste çıkarma yok); kullanıcı listesi dışa verilmez.
6. Herkese açık kullanıcı içeriği (liste, profil) başlangıçta arama motorlarına `noindex` verilir (moderasyon hazır olana kadar). Bu yalnızca **Google'da çıkmasını** engeller; bağlantıyı/kullanıcı adını bilen herkes görebilir.
7. **Görüntülemek için hesap gerekmez (v1.7).** Herkese açık profiller, herkese açık/bağlantılı listeler, paylaşılan defterler ve topluluk puanları **girişsiz** görüntülenir. Hesap yalnızca **oluşturmak/kaydetmek/paylaşmak** için gereklidir. Hiçbir okuma ekranı "giriş yap" duvarıyla kapatılmaz.

**Profil** (`/u/{username}`)
- `username`: 3–20 karakter, küçük harf/rakam/`_`, büyük-küçük harf duyarsız benzersiz; **yasaklı/rezerve kelime listesi** (`admin`, `api`, `cineglobe`, küfür vb.); değiştirme sınırlı (örn. 30 günde bir).
- `display_name` (≤ 40), `bio` (≤ 200; **bağlantı/URL temizlenir**), avatar: **yükleme yok**; baş harf veya kullanıcının seçtiği **favori yapım afişi** (TMDB görseli).
- Profil görünürlüğü: varsayılan `private`. Açıldığında sayfada yalnızca **sahibinin herkese açık seçtikleri** gösterilir: favoriler, herkese açık listeler, son puanlananlar (kayıt bazında `visibility=public`), isteğe bağlı özet istatistik (toplam izlenen, ortalama puan; `show_stats`).

**Kişisel Listeler / Sıralamalar** ("kendi sırasını oluşturma")
- `UserList`: `title` (≤ 80), `description` (≤ 500), `is_ranked` (numaralı sıralama mı, sırasız liste mi), `visibility`, `slug`, `created_at/updated_at`.
- `UserListItem`: `list`, `media_type` + `tmdb_id`, `position` (listede **benzersiz**), `comment` (opsiyonel, ≤ 280; düz metin).
- Sınırlar: kullanıcı başına en çok 50 liste, liste başına en çok 200 öğe; günlük liste oluşturma hız sınırı.
- Sürükle-bırak sıralama (**klavye ile de** erişilebilir), toplu sıralama endpoint'i; listeyi **kopyala ("kendi hesabıma ekle")**; liste Şans Globu kaynağı olabilir ("bu listeden şans").
- Başlık/açıklama/yorum **düz metin** render edilir (XSS yok), URL'ler temizlenir.

**Defter Paylaşımı** (`/s/{token}`)
- `NotebookShare`: `user`, `token_hash` (**en az 128 bit rastgele; yalnızca hash saklanır**, bağlantı tek seferde gösterilir), `scope` (`ratings` = durum + puan; `ratings_notes` = + notlar), `statuses` (hangi durumlar dahil), `expires_at`, `revoked_at`, `view_count`.
- Salt-okunur; alıcıya hesap gerekmez. Bağlantıyı alan kişi içeriği görür ama arama motoru görmez (`noindex`, `X-Robots-Tag`). Sahibi istediği an iptal eder (anında geçersiz).
- Notlar için açık uyarı: "Bu bağlantıyı alan herkes notlarını okuyabilir."

**Topluluk Puanı & "Kimler beğendi"** (yapım detay sayfasında)
- **Anonim topluluk ortalaması:** o yapımı puanlayan üyelerin ortalaması; **en az 5 oy** olmadan gösterilmez (tek kişiyi ifşa etmemek için). KVKK metninde "puanlar anonim toplulaştırılarak kullanılır" yazılır.
- **Herkese açık puanlar:** yalnızca profili ve ilgili kaydı `public` olan kullanıcılar, "Bu yapımı puanlayanlar" bölümünde (son 10, sayfalanır) görünür. Özel kayıtlar asla listelenmez.

**Takip (opsiyonel, Faz 7D):** `Follow` (tek yönlü, `public` profillerde). **Akış (feed) yalnızca yapılandırılmış olaylardan** oluşur ("X, Y filmini 4,5★ verdi", "X yeni liste oluşturdu"); **serbest metin/yorum akışa girmez**. Kullanıcı engelleyebilir (`Block`); engellenen kişi profili/listeleri göremez ve takip edemez.

**Birlikte Seç (opsiyonel, Faz 7D)** — "arkadaşla ne izleyeceğiz?" sorununa çözüm
1. Üye **oturum** başlatır, davet bağlantısı gönderir (varsayılan 24 saat geçerli, kullanıcı başına eş zamanlı sınırlı sayıda oturum).
2. Katılan kişi (hesap gerekir) hangi listesini (örn. "İzlenecek") **bilinçli onayla** ekler; kimse diğerinin tüm defterini görmez, yalnızca onaylanan havuzu.
3. Sistem **ortak filmleri** (kesişim) gösterir; yoksa birleşimden önerir; isteğe bağlı olarak sorgu ("ikimiz de korku sevmiyoruz, komedi olsun") ile filtrelenir.
4. **Şans Globu ortak havuzdan** döner ve sonucu iki tarafa gösterir.
5. **Zevk uyumu:** iki tarafın **ortak puanladığı** (en az 5) yapımlar üzerinden basit bir uyum yüzdesi ve "ikinizin de en sevdiği 3 film". Yetersiz ortak veri varsa gösterilmez.
6. Oturum bitince/süresi dolunca birleşik havuz **silinir**; kalıcı sosyal bağ oluşmaz.

**Kötüye kullanım, moderasyon ve hukuki çerçeve** (ücretsiz/tek kişilik bir proje için kritik)
- **Kullanıcı metni alanları** (kullanıcı adı, bio, liste başlığı/açıklaması/yorumu) tek riskli yüzeydir. Önlemler: uzunluk sınırları, TR+EN **yasaklı kelime filtresi**, URL temizleme, hız sınırları, **Raporla** düğmesi (profil/liste/yorum), Django admin'de **şikâyet kuyruğu**, N şikâyette içeriği **otomatik gizleme** + admin incelemesi, kullanıcıyı **engelleme**, kalıcı yasaklama.
- **Yok (bilinçli karar):** herkese açık yorum/tartışma, DM, görsel yükleme. Gerekirse sonra, moderasyon kapasitesiyle birlikte eklenir.
- Kullanıcı içeriği barındırmak yasal sorumluluk doğurabilir (ör. Türkiye'de içerik/yer sağlayıcı yükümlülükleri, KVKK, yaş sınırı). Kullanıcı bu konuda **"genel geçer, standart kararlar olsun"** dedi (v1.7): ajan aşağıdaki **Varsayılan Politika Kararları**'nı uygular ve metinleri **genel şablon** olarak yazar. Şablonlar hukuki danışmanlık yerine geçmez; geliştirmeyi **engellemez**, ancak site halka açılmadan önce bir kez gözden geçirilmesi `docs/legal-notes.md`'de önerilir.

**Varsayılan Politika Kararları (v1.7)**
- **Yaş:** Hesap açmak için **18+ beyanı** (onay kutusu; doğum tarihi **toplanmaz**). Hesapsız gezinme ve görüntüleme her yaşa açıktır. (Hukuki gözden geçirmede 18 aşağı çekilebilir; tek bir ayar: `MIN_ACCOUNT_AGE`.)
- **Topluluk Kuralları (kısa ve genel):** hakaret/küfür/nefret söylemi yok · taciz yok · spam/reklam/dış bağlantı yok · başkasının kimliğine bürünme yok · kişisel bilgi (telefon, adres, e-posta, kimlik no) paylaşma yok · yasa dışı içerik yok.
- **Raporla menüsü nedenleri:** *Küfür/hakaret/nefret* · *Spam/reklam* · *Taklit/sahte hesap* · *Kişisel bilgi paylaşımı* · *Diğer* (≤ 200 karakter, düz metin).
- **Süreç:** (1) kullanıcı raporlar → (2) **3 farklı** hesaptan rapor gelirse içerik **otomatik gizlenir** (aynı kişinin tekrarı sayılmaz; 24 saatten genç hesapların raporu sayılmaz; kötü niyetli toplu rapora karşı rapor hız sınırı) → (3) içerik sahibine uygulama içi/e-posta bildirim: "içeriğin gizlendi, itiraz için `SUPPORT_EMAIL`" → (4) yönetici Django admin'den **geri açar / siler / uyarır / hesabı askıya alır**. Hedef: raporlara **7 gün içinde** bakmak (hukuki taahhüt değil, iç hedef; `REPORT_REVIEW_TARGET_DAYS`).
- **Kaldırma/KVKK talepleri:** `SUPPORT_EMAIL` üzerinden alınır; hesap ve veri silme zaten self-servistir (Faz 7).
- **Uygunsuz yapımlar:** TMDB çağrılarında `include_adult=false`; yetişkin içerik arama, koleksiyon, liste ekleme ve globe'dan **çıkarılır**.
- **Metinler:** Kullanım Koşulları, Topluluk Kuralları, Gizlilik/KVKK Aydınlatma, Çerez bildirimi — sade Türkçe + İngilizce **şablonlar** (`web/src/content/legal/`); iletişim e-postası ve veri sorumlusu bilgisi kullanıcıdan alınan yer tutuculara yazılır.

**Endpointler** (özet; ayrıntı Faz 7C/7D)
- Profil: `GET /api/v1/users/{username}/` (yalnızca public kısım), `GET|PATCH /api/v1/me/profile/`
- Listeler: `GET|POST /api/v1/me/lists/`, `GET|PATCH|DELETE /api/v1/me/lists/{id}/`, `PUT /api/v1/me/lists/{id}/items/` (toplu sıralı güncelleme), `POST /api/v1/lists/{id}/clone/`, `GET /api/v1/lists/{slug_or_id}/` (görünürlük kuralına göre)
- Paylaşım: `POST|GET|DELETE /api/v1/me/shares/`, `GET /api/v1/shared/{token}/`
- Topluluk: `GET /api/v1/titles/{media_type}/{tmdb_id}/community/`
- Moderasyon: `POST /api/v1/reports/`, `POST|DELETE /api/v1/me/blocks/`
- (7D) Takip/akış: `POST|DELETE /api/v1/me/follow/{username}/`, `GET /api/v1/me/feed/`; Birlikte Seç: `POST /api/v1/together/`, `POST /api/v1/together/{id}/join/`, `GET /api/v1/together/{id}/`, `POST /api/v1/together/{id}/spin/`

---

## 4. REPO YAPISI

```
cineglobe/
├── backend/            # Django
│   ├── config/         # settings (base/dev/prod), urls, wsgi
│   ├── apps/
│   │   ├── catalog/    # TMDB istemcisi, Title (film+dizi) modelleri, cache
│   │   ├── search/     # NL arama, LLM, ranking
│   │   ├── people/     # oyuncu arama, filmografi
│   │   ├── collections/ # hazır koleksiyonlar (recipe, kürasyon)
│   │   ├── upcoming/   # yakında çıkacaklar
│   │   ├── reminders/  # hatırlatıcılar, bildirim kanalları, günlük job
│   │   ├── notebook/   # Film Defterim: NotebookEntry, istatistik, dışa aktarma
│   │   ├── social/     # profil, kişisel listeler, defter paylaşımı, topluluk puanı, şikâyet/engel, (7D) takip + Birlikte Seç
│   │   ├── (monetization/)  # ERTELENDİ — Faz 10 başlayana kadar oluşturulmaz
│   │   └── accounts/   # kullanıcı, oturum, tercihler
│   ├── tests/
│   ├── requirements/ (base.txt, dev.txt, prod.txt)
│   └── Dockerfile
├── web/                # Vue 3 (SSR/prerender), tek istemci
├── docs/               # mimari, API, karar kayıtları (ADR)
├── .github/workflows/  # ci-backend.yml, ci-web.yml, deploy.yml
├── docker-compose.yml
├── .env.example
├── CINEGLOBE_PLAN.md   # bu dosya
└── README.md
```

---

## 5. GIT & GITHUB KURALLARI

### 5.1 Branch Stratejisi
- `main` → her zaman çalışır, korumalı (doğrudan push yok)
- `develop` → entegrasyon
- `feature/<faz>-<kısa-ad>` → örn. `feature/p3-nl-search`
- `fix/<ad>`, `chore/<ad>`

### 5.2 Commit Formatı (Conventional Commits)
```
<tip>(<kapsam>): <kısa açıklama>
```
Tipler: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`, `ci`, `style`
Örnekler:
```
feat(search): add LLM query-to-filter parser
test(search): cover invalid JSON fallback
ci(backend): run pytest and ruff on PR
docs(readme): add local setup steps
```

### 5.3 İş Akışı (her faz için)
1. `git checkout develop && git pull`
2. `git checkout -b feature/pX-ad`
3. Küçük commitlerle ilerle
4. Testler + lint lokal yeşil olsun
5. `git push -u origin feature/pX-ad`
6. **Pull Request** aç (şablon: ne yapıldı / nasıl test edilir / ekran görüntüsü)
7. CI yeşilse `develop`'a **squash merge**
8. Faz bitince `develop → main` PR, sonra tag: `v0.X.0`

### 5.4 Repo Hijyeni
- `.gitignore` (Python, Node, `.env`, IDE)
- PR şablonu `.github/pull_request_template.md`
- Branch protection: PR + geçen CI zorunlu
- Secrets: GitHub → Settings → Secrets ve Vercel → Environment Variables (TMDB key, Gemini key, `DATABASE_URL`, `CRON_SECRET`; Anthropic key yalnızca Haiku'ya geçilirse). Hiçbiri repoya girmez

---

## 6. FAZLAR

---

### 🟦 FAZ 0 — Proje Kurulumu & Zemin
**Amaç:** Boş ama sağlam bir iskelet.

**Görevler**
- [ ] GitHub reposu, `main` + `develop`, branch protection
- [ ] Klasör yapısı (bkz. §4), `.gitignore`, `.env.example`, `README.md` iskeleti
- [ ] `docker-compose.yml`: `postgres`, `backend` (Redis eklenmez, bkz. v1.8)
- [ ] Lint/format: `ruff` + `black` (Python), `eslint` + `prettier` (Vue)
- [ ] `pre-commit` hook'ları
- [ ] PR şablonu, `docs/adr/0001-tech-stack.md` (bu dosyadaki kararların kaydı)
- [ ] **(v1.8) Barındırma denemesi (spike) — kodlamadan önce karar kapısı:**
  1. **Kullanıcıdan** şunları iste (kendisi açar, **kart eklemeden**): Vercel Hobby hesabı (GitHub ile giriş) ve Neon ücretsiz hesabı. Ajan bu hesapları kendisi açmaz, anahtarları sohbete yazdırmaz; kullanıcı değerleri yalnızca Vercel/Neon panelindeki ortam değişkenlerine girer.
  2. En küçük Django projesini (`/health/` + bir tablo okuma) **Vercel Python fonksiyonu** olarak, **Neon pooled bağlantısıyla** yayına al.
  3. Ölç ve `docs/deploy-spike.md`'ye yaz: (a) 10+ dk boşta kaldıktan sonraki **ilk istek süresi** (Vercel soğuk başlangıcı + Neon uyanması), (b) sıcak istek süresi (≥ 20 istek ortalaması/p95), (c) veritabanı bağlantı hataları, (d) Hobby limitleri (fonksiyon süre sınırı, paket boyutu) bu uygulamaya yeter mi.
  4. **Karar kapısı:** ilk istek ≲ 5 sn ve sıcak istek ≲ 800 ms ise Vercel + Neon ile devam (ADR `0002-hosting.md`). Değilse **kullanıcıya rapor ver** ve yedek planı öner (Render ücretsiz = ücretsiz ama ~1 dk soğuk başlangıç; Cloud Run = fatura hesabı gerektirir, **ancak kullanıcı onayıyla**). Eşikler başlangıç değeridir, ajan kullanıcıyla birlikte ayarlayabilir.
- [ ] `docs/cost.md` iskeleti: kullanılan her servisin ücretsiz limitleri, tarih ve resmi kaynak linki, limit dolunca davranış

**Kabul Kriterleri**
- `docker compose up` PostgreSQL'i sorunsuz ayağa kaldırır
- `pre-commit run --all-files` hatasız
- İlk commit'ler Conventional Commits formatında
- **(v1.8)** Spike raporu (`docs/deploy-spike.md`) var ve hosting kararı kullanıcıyla onaylanmış; hiçbir serviste ödeme yöntemi tanımlı değil

**Commit örnekleri:** `chore: initialize monorepo structure`, `chore(ci): add pre-commit config`

---

### 🟦 FAZ 1 — Backend Temeli (Django + PostgreSQL)
**Görevler**
- [ ] Django projesi, settings ayrımı (`base/dev/prod`), env okuma (`django-environ`)
- [ ] PostgreSQL bağlantısı, DRF, `django-cors-headers`, `drf-spectacular` (OpenAPI)
- [ ] `GET /api/v1/health/` endpoint'i (DB kontrolü dahil)
- [ ] Global hata formatı (tutarlı JSON hata yapısı)
- [ ] Rate limiting (DRF throttling)
- [ ] Dockerfile (multi-stage, non-root kullanıcı) — **taşınabilirlik için korunur** (Vercel bu dosyayı kullanmaz; yedek barındırma planı için)
- [ ] **(v1.8) Serverless uyumluluğu:** (a) uygulama **durumsuz**: yerel dosyaya yazma yok, süreç belleğine güvenen sayaç/önbellek/oturum yok; (b) önbellek `DatabaseCache`, sayaçlar `DailyCounter` tablosu; (c) veritabanı bağlantısı Neon **pooled** adresiyle, kısa ömürlü (`CONN_MAX_AGE` serverless'a göre ayarlı, bağlantı sızıntısı yok); (d) Django statik dosyaları (admin) **WhiteNoise** ile; (e) `ALLOWED_HOSTS` ve `CSRF_TRUSTED_ORIGINS` `*.vercel.app` ile uyumlu; (f) `vercel.json`/`pyproject.toml` giriş noktası (`application`), gereksiz dosyalar paket dışı (500 MB sınırının çok altında); (g) soğuk başlangıcı azaltmak için ağır içe aktarmalar (ör. LLM SDK'ları) tembel (lazy) yüklenir
- [ ] **(v1.8)** Yerel geliştirme `docker compose up` ile PostgreSQL; **Redis zorunlu değil** (`docker-compose.yml`'de yok veya yorum satırı)

**Testler:** health endpoint testi, settings yükleme testi; **(v1.8)** önbelleğin/sayaçların iki ayrı süreçte tutarlı çalıştığı test (aynı veritabanı), `DailyCounter` atomik artırma testi

**Kabul Kriterleri**
- `/api/v1/health/` → 200 ve `{"status":"ok","db":"ok"}`
- `/api/schema/swagger-ui/` açılıyor
- `pytest` yeşil, kapsam ≥ %80 (bu fazın kodu için)

---

### 🟦 FAZ 2 — TMDB Entegrasyonu & Veri Katmanı
**Görevler**
- [ ] `TMDBClient` sınıfı: retry, timeout, hata yönetimi, rate-limit saygısı
- [ ] Endpoint'ler: **film detayı, dizi detayı**, `discover/movie`, `discover/tv`, person search, combined credits, keyword search, popüler (film + dizi ayrı)
- [ ] Genre mapping tablosu (mantıksal tür → film ID + dizi ID), birim testli
- [ ] Modeller: `Title` (`media_type`, `tmdb_id` birlikte **unique**; çünkü film ve dizi ID'leri çakışabilir), `Genre`, `Person`, `TVDetails` (sezon sayısı, bölüm sayısı, durum, bölüm süresi, yayıncı/network, ilk/son yayın tarihi), `Season` (opsiyonel)
- [ ] **Önemli:** TMDB'de film ve dizinin `id` değeri aynı olabilir. Tüm tablolar, cache anahtarları ve URL'ler `media_type + id` ikilisiyle çalışmalı.
- [ ] Cache stratejisi (film/dizi detayı: 24 saat; **devam eden dizi detayı: 6 saat**, çünkü yeni bölüm/sezon bilgisi değişir; discover: 1 saat)
- [ ] **(v1.3) TMDB 6 ay kuralı:** DB'de saklanan TMDB verisi (`Title`, `Person`, `TVDetails` vb.) için `updated_at` takibi + günlük/haftalık `purge_stale_tmdb_data` komutu: 6 aydan eski kayıtlar yenilenir, yenilenemeyenler silinir (testle kanıtlı)
- [ ] Görsel URL yardımcıları (poster/backdrop boyutları)
- [ ] Footer için TMDB atıf metni hazırla; kullanıcıya lisans uyarısı ver
- [ ] **(v1.2) Dil desteği:** `TMDBClient` tüm çağrılarda `lang` (`tr-TR`/`en-US`) alır; boş TR alanlarda EN fallback; cache anahtarına `lang` eklenir
- [ ] **(v1.2)** Ek endpoint'ler: `person/{id}` detayı, `movie/upcoming`, `discover` için tarih/süre/oy aralığı parametreleri (koleksiyon ve yakında çıkacaklar için gerekli), `tv/on_the_air`
- [ ] **(v1.7)** Tüm `discover`/`search` çağrılarında `include_adult=false`; yetişkin işaretli yapımlar yanıtlardan ve detaydan ayıklanır

**Testler:** TMDB yanıtları **mock'lanır** (gerçek API'ye test çağrısı yok), hata/timeout senaryoları; TR boş → EN fallback testi; `include_adult=false` her çağrıda

**Kabul Kriterleri**
- `GET /api/v1/titles/{media_type}/{tmdb_id}/` (`movie` veya `tv`) çalışıyor ve cache'liyor
- Aynı `tmdb_id`'li bir film ve bir dizi birbirini ezmiyor (testle kanıtlı)
- TMDB kapalıyken API 500 değil, anlamlı 503 döner
- Anahtarlar sadece env'den okunuyor

---

### 🟦 FAZ 3 — Doğal Dil Film & Dizi Arama (Projenin Kalbi)
**Görevler**
- [ ] **(v1.5) `LLMProvider` arayüzü + `GeminiProvider`, `AnthropicProvider`, `ClassicProvider`** ve `LLM_PROVIDER_CHAIN` ile zincir/devre kesici (§3.10). Varsayılan zincir `gemini,classic`; `AnthropicProvider` kodda hazır ama anahtar yoksa devre dışı
- [ ] **(v1.5) Değerlendirme seti + `docs/llm-eval.md`:** 9 zorunlu senaryo + en az 20 gerçek Türkçe/İngilizce sorgu; komutla çalıştırılan betik (canlı API anahtarı gerektirir, **CI'da değil**, elle çalışır); geçiş kriteri sonuçları raporlanır. **Faz sonunda kullanıcıya sonucu sun: Gemini ücretsiz katman yeterli mi, Haiku 5.5'e geçmeli mi?**
- [ ] `QueryParser` servisi: sağlayıcı arayüzü üzerinden çağrı + sistem prompt'u (bkz. §3.1)
- [ ] Pydantic şemaları: `SearchFilters` (doğrulama, güvenli varsayılanlar)
- [ ] Fallback: LLM başarısızsa basit tür/anahtar kelime eşleştirme
- [ ] `Retriever`: filtreden TMDB adayları üretme (discover + keyword); `media_type`'a göre film, dizi veya ikisi paralel
- [ ] `Ranker`: puan × oy güveni × anahtar kelime eşleşmesi; `genres_exclude` kesin eleme
- [ ] `Explainer`: her film/dizi için tek cümlelik "neden bu film?" (toplu çağrı)
- [ ] `POST /api/v1/search/` → `{ "query": "...", "media_type": "both" }` → yapımlar (her birinde `media_type`) + açıklamalar + uygulanan filtreler
- [ ] Sorgu cache'i + kullanıcı/IP başına rate limit
- [ ] Türkçe ve İngilizce sorgu desteği; "neden önerildi?" metni `lang` parametresine göre üretilir, cache anahtarında `lang` bulunur
- [ ] **(v1.4) Maliyet koruması (§3.10):** sorgu normalizasyonu + sonuç önbelleği; model kimlikleri env'den (`GEMINI_MODEL`, `ANTHROPIC_MODEL_PARSER/EXPLAIN`); `max_tokens` ve sorgu uzunluğu sınırı
- [ ] **(v1.4)** "Neden önerildi?" için **şablon tabanlı (LLM'siz) açıklama** + isteğe bağlı/lazy LLM açıklaması (ilk 3–5 sonuç veya "Neden?" tıklaması, önbellekli)
- [ ] **(v1.4)** `LLMUsageLog` (çağrı türü, model, token, tahmini maliyet, cache hit/miss; kişisel veri yok) + veritabanında günlük harcama/kota sayacı (`DailyCounter`; atomik artırma, `Europe/Istanbul` günü) + `LLM_DAILY_BUDGET_USD` tavanı
- [ ] **(v1.4)** Kota ve degrade: misafir/üye günlük kotası, bütçe/kota dolunca **AI'sız klasik aramaya otomatik geçiş** (500/blok yok), arayüze iletilecek `ai_status` alanı (`ok` | `quota_exceeded` | `budget_exceeded` | `fallback`)
- [ ] **(v1.4)** Django admin'de günlük/aylık LLM maliyet görünümü

**Test senaryoları (zorunlu — ajan bunları birebir yazsın)**
1. "silahlı çatışma ama istihbarat da olsun" → Action/Thriller + spy/espionage anahtar kelimeleri
2. "gerilim olsun ama korku içermesin, keyifli olsun" → Thriller dahil, **Horror hariç**
3. Anlamsız/boş sorgu → 400 ve yardımcı mesaj
4. LLM geçersiz JSON döndürürse → fallback çalışır, 500 dönmez
5. Prompt injection denemesi ("önceki talimatları unut...") → normal arama gibi işlenir, sistem davranışı değişmez
6. "kısa bölümlü, hafif, komik bir dizi" → `media_type=tv`, Comedy, `episode_runtime_max` ≈ 30
7. "casusluk temalı bir dizi, çok uzun olmasın" → `media_type=tv`, spy/espionage, `max_seasons` düşük
8. "bu akşam bir şey izleyeceğim, gerilim olsun" (tür belirtilmemiş) → `media_type=both`, sonuçlarda film ve dizi karışık
9. Aynı `tmdb_id`'ye sahip film ve dizi sonuç listesinde birbirini silmiyor
10. **(v1.4)** Aynı sorgu (büyük/küçük harf, noktalama farkıyla) ikinci kez geldiğinde LLM **çağrılmaz** (mock çağrı sayısı = 0), sonuç aynı
11. **(v1.4)** Günlük bütçe tavanı dolduğunda arama **200 + `ai_status=budget_exceeded`** ile klasik aramadan sonuç döner; LLM mock'u çağrılmaz
12. **(v1.4)** Misafir kota aşımında nazik yanıt + klasik arama; üye kotası ayrı sayılır; kota gece yarısı (`Europe/Istanbul`) sıfırlanır
13. **(v1.4)** Her LLM çağrısı `LLMUsageLog`'a token/maliyetle yazılır; sayaç kayıtlarla tutarlı
14. **(v1.4)** Çok uzun sorgu (> sınır) reddedilir/kısaltılır; `max_tokens` aşılmaz
15. **(v1.5)** Zincir: birinci sağlayıcı 429/zaman aşımı/5xx verirse ikinciye düşer; ikinci de yoksa `classic` ile 200 döner; devre kesici açıkken aynı sağlayıcıya istek atılmaz (mock çağrı sayısı)
16. **(v1.5)** Sağlayıcı değiştirme yalnızca env ile yapılır (`gemini,classic` ↔ `anthropic,classic`); iş mantığı testleri sağlayıcıdan bağımsız geçer
17. **(v1.5)** LLM'e giden istek gövdesinde kullanıcı kimliği, e-posta, IP ve defter notu/puanı **bulunmaz** (mock yakalama ile kanıtlı)

**Kabul Kriterleri**
- Yukarıdaki 5 senaryo geçiyor (LLM mock'lu birim testler + 1 opsiyonel canlı smoke test)
- Ortalama yanıt süresi hedefi: cache'siz < 6 sn, cache'li < 300 ms
- Kullanıcıya dönen her sonuçta gerekçe ve doğru `media_type` var
- **(v1.4)** Arama başına ortalama LLM maliyeti ölçülüyor ve `docs/cost.md`'de raporlanıyor (hedef: Haiku 5.5 ile cache'siz arama başına ≲ $0,001)
- **(v1.4)** Bütçe/kota dolsa bile kullanıcı hiçbir zaman boş ekran veya hata görmüyor (klasik arama devrede)

---

### 🟦 FAZ 4 — Oyuncu Bazlı Öneriler
**Görevler**
- [ ] `POST /api/v1/people/top-titles/` veya arama içinde `intent: "person_filmography"` (film + dizi)
- [ ] Takma ad çözümleme ("RDJ" → Robert Downey Jr.) + TMDB ile doğrulama
- [ ] Belirsiz isimde (birden çok eşleşme) kullanıcıya seçenek dön
- [ ] Sıralama kuralı §3.2 (min oy sayısı, başrol filtresi)
- [ ] Film / Dizi / Hepsi filtresi; varsayılan olarak iki ayrı bölüm (en iyi filmler + en iyi diziler)
- [ ] Dizide oyuncunun rolü kontrolü (tek bölümlük konuk rolleri ele, bkz. §3.2)
- [ ] **(v1.2) Filmografi:** `GET /api/v1/people/{tmdb_id}/filmography/` (bkz. §3.6) — `newest` / `oldest` / `rating` / `popularity` sıralamaları, Film/Dizi/Hepsi filtresi, `lead_only` anahtarı
- [ ] **(v1.2)** Tarihi olmayan kayıtlar sona; gelecek tarihli kayıtlar "Yakında" grubuna; `Self`/`Archive Footage`/talk-show gürültüsü varsayılan gizli
- [ ] **(v1.2)** Oyuncu detay verisi (kısa biyografi, fotoğraf, doğum yılı) `lang`'e göre, EN fallback

**Testler:** RDJ, tek isimli oyuncu, yazım hatalı isim, bulunamayan isim, aynı isimli iki oyuncu; **filmografi:** kronolojik sıra doğru (eski→yeni ve yeni→eski), tarihsiz kayıt sonda, gelecek tarihli kayıt "Yakında"da, `Self` kayıtları elenmiş, aynı `tmdb_id`'li film+dizi çakışmıyor

**Kabul Kriterleri**
- "RDJ'nin en iyi filmleri" → doğru oyuncu, 10 film, oy eşiği uygulanmış
- "Bryan Cranston'ın en iyi dizileri" → sadece dizi, konuk rolleri elenmiş
- Bulunamazsa nazik hata + öneri
- Bir oyuncunun filmografisi `sort=oldest` ile kronolojik, `sort=newest` ile en güncelden başlıyor (testle kanıtlı)

---

### 🟦 FAZ 4B — Hazır Koleksiyonlar (v1.2)
**Amaç:** Kullanıcı hiçbir şey yazmadan tek tıkla ruh haline uygun film/dizi bulsun (bkz. §3.5).

**Görevler**
- [ ] `collections` uygulaması: `Collection` modeli, `recipe` için Pydantic şeması, Django admin (pin/blocklist, aktif/pasif, sıralama)
- [ ] Başlangıç koleksiyonlarını seed eden data migration / fixture (**önce kullanıcıdan liste onayı al**, bkz. §3.5)
- [ ] `RecipeEngine`: recipe → TMDB discover parametreleri (film/dizi genre mapping tablosunu kullanır) → Ranker
- [ ] (Opsiyonel) Günlük ön-hesaplama komutu: subjektif koleksiyonlar için toplu LLM doğrulama skoru (istek anında LLM çağrısı YOK)
- [ ] `GET /api/v1/collections/` ve `GET /api/v1/collections/{slug}/` (sayfalama, `media_type`, `lang`)
- [ ] Koleksiyon adı/açıklaması TR/EN
- [ ] Spoiler içermeyen gerekçe kuralı (özellikle Tersköşe)
- [ ] Şans Globu entegrasyonu için "koleksiyondan rastgele" endpoint'i veya liste dönüşü hazır olsun

**Testler:** recipe doğrulama (geçersiz recipe reddedilir), recipe → discover parametre eşlemesi (mock TMDB), `genres_exclude` kesin eleme (örn. Çerezlik'te Horror yok), pin/blocklist davranışı, sayfalama, TR/EN adlar, boş sonuç durumu

**Kabul Kriterleri**
- En az 6 koleksiyon (§3.5'teki ilk 6) çalışıyor ve her biri en az 20 sonuç döndürüyor
- Koleksiyon sonuçları cache'li (cache'li < 300 ms)
- Editör, admin panelinden kod değiştirmeden koleksiyon ekleyip düzenleyebiliyor

---

### 🟦 FAZ 4C — Yakında Çıkacaklar (v1.2)
**Amaç:** Yaklaşan film/dizileri listelemek (hatırlatıcı arayüzü Faz 7'de hesaplarla tamamlanır).

**Görevler**
- [ ] `upcoming` uygulaması: TMDB'den yaklaşan film (`primary_release_date.gte`, `region=TR`) ve diziler (`first_air_date.gte`, yeni sezon bilgisi) çekimi
- [ ] `GET /api/v1/upcoming/` (tarih gruplama: bu hafta / bu ay / sonrası; tarihsiz grup; Film/Dizi/Hepsi; tür filtresi; sayfalama; `lang`)
- [ ] Kısa cache (3–6 saat); çıkmış yapımlar otomatik düşer
- [ ] Çıkış tarihi alanları: `release_date`, `date_precision` (`day`/`month`/`year`/`unknown`), `region`
- [ ] Hatırlatıcı veri modeli (`Reminder`) ve servis katmanı **hazırlanır** ama bildirim gönderimi Faz 7'de tamamlanır

**Testler:** tarih gruplama sınır durumları (bugün, yarın, ay sonu), tarihsiz kayıt, geçmişe düşen kayıt listeden çıkıyor, TR bölgesi tarihi yoksa global fallback, film+dizi aynı `tmdb_id` çakışması

**Kabul Kriterleri**
- Liste yalnızca bugünden sonrasını gösteriyor (testle kanıtlı, saat dilimi: `Europe/Istanbul`)
- Çıkış tarihi belirsiz yapımlar hata vermeden ayrı grupta görünüyor

---

### 🟦 FAZ 5 — Web Arayüzü (Vue 3) — Premium Tasarım
**Tasarım Yönü**
- Koyu tema öncelikli, sinematik his: derin siyah/lacivert zemin, tek vurgu rengi (örn. amber/altın), cam efekti (glassmorphism) ölçülü
- Tipografi: başlıkta karakterli bir serif/display, gövdede temiz sans (örn. *Fraunces* + *Inter*)
- Büyük backdrop görselleri, yumuşak parallax, yavaş ve zarif geçişler
- Arama kutusunun altında **Film · Dizi · Hepsi** segmentli anahtar (yumuşak geçişli)
- Arama kutusu hero'nun merkezi: büyük, "ne izlemek istersin?" placeholder'ı, örnek sorgu çipleri
- Yükleme durumu: iskelet (skeleton) kartlar, "düşünüyorum…" mikro animasyonu

> Ajan `frontend-design` prensiplerine uysun: şablon gibi görünen jenerik tasarımdan kaçın.

**Görevler**
- [ ] Vite + Vue 3 + TS + Pinia + Router + Tailwind kurulumu
- [ ] Tasarım tokenları (`tokens.css`): renk, boşluk, radius, gölge, motion süreleri
- [ ] Sayfalar: **Ana Sayfa (Hero+Arama + koleksiyon şeridi)**, **Sonuçlar**, **Detay (film ve dizi için ortak şablon; dizide sezon/bölüm bilgisi paneli)**, **Oyuncu Sonuçları (Filmler / Diziler sekmeleri)**, **Oyuncu Sayfası (filmografi: Kronolojik / En Güncel / En İyi sıralama anahtarı)**, **Koleksiyonlar (liste) + Koleksiyon Detay**, **Yakında Çıkacaklar**, **Favoriler**, **Profil (`/u/kullanici`)**, **Listeler (detay + düzenleme)**, **Paylaşılan Defter (`/s/…`)** *(Faz 7C ile bağlanır)*, **404**
- [ ] Bileşenler: `SearchBox`, `TitleCard` (film/dizi rozeti ile), `TitleGrid`, `MediaTypeToggle`, `SeasonInfo`, `ReasonBadge`, `SkeletonCard`, `Navbar`, `Footer` (TMDB atıf), **`LanguageSwitcher` (TR | EN)**, **`CollectionCard` / `CollectionRail` (yatay kaydırmalı koleksiyon şeridi)**, **`FilmographyList` + `SortToggle` (en güncel / kronolojik / en iyi)**, **`UpcomingList` (tarih gruplu) + `RemindButton`**
- [ ] **(v1.2) i18n:** `vue-i18n`, `/tr` ve `/en` URL önekleri, `hreflang`, dil seçimi kalıcı, tüm API çağrılarına `lang`, TR içerik boşsa EN fallback göstergesi, tarih/sayı `Intl`
- [ ] **(v1.2) Koleksiyon deneyimi:** ana sayfada 6 koleksiyon kartı (ikon + ad + kısa açıklama), her kart `Koleksiyon Detay`'a gider; "Bu koleksiyondan şansımı dene" butonu (Şans Globu ile bağlantı Faz 6'da)
- [ ] **(v1.2) Yakında Çıkacaklar sayfası:** aylık/haftalık gruplama, Film/Dizi/Hepsi filtresi, "Hatırlat" butonu (misafir ise giriş istemi; gerçek hatırlatma Faz 7'de bağlanır)
- [ ] **(v1.3) SSR/prerender:** koleksiyon, oyuncu, detay, yakında çıkacaklar ve ana sayfa arama motoruna HTML olarak sunulur (Nuxt 3 veya Vite SSG/prerender — ajan gerekçesiyle seçsin, **ADR**). Defter/hesap sayfaları `noindex`. **(v1.8)** Vercel Hobby fonksiyon kotasını (ayda 1 milyon çağrı, 4 saat aktif işlemci) korumak için sayfalar mümkün olduğunca **statik/prerender (+ yenileme)** ile sunulur; SSR yalnızca gerçekten gereken yerlerde kullanılır. Statik sayfa çıktısı `Cache-Control` ile CDN'de önbelleklenir.
- [ ] **(v1.3) Giriş yapmadan kullanım:** tüm keşif sayfaları misafire açık; Navbar'da "Giriş yap" ikincil bir eylem (zorlayıcı modal/duvar yok)
- [ ] **(v1.3) Defter UI (Faz 7B ile bağlanır):** `StatusPicker` (izlenecek/izleniyor/izledim/bıraktım), `StarRating` (0,5 adım, klavye ile erişilebilir), `NoteDrawer` (özel not), `WatchedBadge` (kartlarda "İzledin ✓ · 4,5★"), `AuthSoftGateModal` (misafir için "ücretsiz hesap aç")
- [ ] **(v1.4) Yapay zeka durum bildirimi:** `ai_status` değerine göre arama sonuçlarında nazik bilgi şeridi ("AI arama bugünlük doldu, klasik arama açık" vb.); reklam alanı/`AdSlot` **eklenmez** (Faz 10 ertelendi)
- [ ] API katmanı (tipli, hata yönetimi, iptal edilebilir istekler)
- [ ] Erişilebilirlik: klavye gezinme, odak halkaları, alt metinler, kontrast AA
- [ ] Responsive: 360px → 1920px (**tek istemci olduğu için mobil tarayıcı birinci sınıf**: dokunma hedefleri ≥ 44px, alt navigasyon seçeneği)
- [ ] SEO: meta etiketleri, OG görselleri, `sitemap.xml`, `robots.txt`, canonical, `hreflang`, schema.org (`Movie`/`TVSeries`/`Person`)
- [ ] i18n: TR/EN

**Testler**
- Vitest: bileşen + store testleri
- Playwright: "ara → sonuç gör → detaya git" akışı (API mock'lu)

**Kabul Kriterleri**
- Lighthouse: Performance ≥ 85, Accessibility ≥ 95
- Mobil tarayıcıda (360px) görünüm ve dokunma deneyimi bozulmuyor
- Kaynak kodu görüntülenince/JS kapalıyken koleksiyon ve oyuncu sayfalarının içeriği HTML'de mevcut (SSR/prerender kanıtı)
- Boş sonuç, hata ve yükleme durumları tasarlanmış
- Film ve dizi kartları tek bakışta ayırt edilebiliyor (rozet + dizide sezon sayısı)
- Dil değiştirici TR↔EN arayüz ve içeriği sayfayı kaybetmeden değiştiriyor; hiçbir ekranda çevrilmemiş (ham anahtar) metin kalmıyor
- Oyuncu sayfasında sıralama anahtarı çalışıyor, tarihsiz/yakında kayıtlar doğru gruplanıyor
- Koleksiyon ve Yakında Çıkacaklar sayfaları boş/hata/yükleme durumlarıyla tasarlanmış

---

### 🟦 FAZ 6 — Şans Globu & Favoriler
**Görevler**
- [ ] Film ve dizi favori ekle/çıkar (`media_type + id` ile saklanır; önce localStorage, Faz 7'de DB'ye bağlanacak arayüzle)
- [ ] `LuckyGlobe.vue`: three.js/globe.gl ile 3D küre, ışıklandırma, hafif atmosfer parlaması
- [ ] "Çevir" butonu: ease-out dönüş (2.5–4 sn), dönerken hafif titreşim/ses (ses opsiyonel, varsayılan kapalı)
- [ ] Globe'da Film/Dizi/Hepsi filtresi
- [ ] Durunca: seçilen yapımın afişi küreden çıkıp ekrana gelir → detay kartı + "Tekrar çevir" + "İzleme listesine ekle"
- [ ] Tekrar önleme (son 3 seçim hariç), tek favori varsa özel mesaj
- [ ] **(v1.2)** Kaynak seçimi: "Favorilerim" veya "Bir koleksiyondan" (örn. Tersköşe Filmleri'nden rastgele)
- [ ] Boş favori durumu: onboarding
- [ ] **(v1.3)** Üye kaynakları: "İzlenecek listem" seçeneği; "İzlediklerimi hariç tut" anahtarı (varsayılan açık, yalnızca girişli)
- [ ] Performans: mobil tarayıcıda düşük güçlü cihaz için düşük poligon/pixel ratio sınırı, `prefers-reduced-motion` desteği
- [ ] Küre için lazy-load (ana sayfa bundle'ını şişirmesin)

**Testler:** rastgele seçim mantığı (deterministik seed ile), boş liste, tek eleman, tekrar önleme

**Kabul Kriterleri**
- Orta seviye telefonda ≥ 45 FPS
- Animasyon bitince her zaman geçerli bir film/dizi gösteriliyor (edge-case'lerde takılma yok)

---

### 🟦 FAZ 7 — Kullanıcı Hesapları (İsteğe Bağlı Giriş) & Kalıcı Favoriler
> **İlke (v1.3):** Hesap **isteğe bağlıdır**. Bu fazdaki hiçbir değişiklik misafir deneyimini bozmamalı veya bir arama/keşif ekranını girişe bağlamamalıdır (bkz. §3.8).

**Görevler**
- [ ] Kayıt/giriş: e-posta + şifre (Argon2) ve **Google ile giriş** (opsiyonel)
- [ ] JWT (kısa ömürlü access + refresh) veya güvenli cookie tabanlı oturum — ajan gerekçesiyle seçsin, ADR yazsın (SSR kullanıldığı için cookie tabanlı oturum + CSRF koruması değerlendirilsin)
- [ ] `SearchHistory` modeli (`media_type` + `tmdb_id` ile). **Favori / izleme listesi / puan / not `NotebookEntry` altında birleşir → Faz 7B** (ayrı `Favorite` ve `WatchlistItem` tabloları açılmaz)
- [ ] Misafir ve üye için ayrı **günlük AI arama kotası** (kota aşımında anlaşılır mesaj + "ücretsiz hesap aç" önerisi; Faz 8 maliyet korumasıyla uyumlu)
- [ ] Endpoint'ler: arama geçmişi listeleme/silme
- [ ] localStorage favorilerini girişte hesaba **birleştirme (merge)** (favoriler `NotebookEntry.is_favorite=true` olarak aktarılır; çakışmada hesaptaki veri korunur)
- [ ] Hesap silme + veri dışa aktarma (KVKK/GDPR uyumu için temel)
- [ ] E-posta doğrulama / şifre sıfırlama (opsiyonel, faz sonunda)
- [ ] **(v1.2) Dil tercihi:** kullanıcı profiline `preferred_language` (`tr`/`en`); girişte tarayıcı seçimiyle birleştirilir
- [ ] **(v1.2) Hatırlatıcılar:** `Reminder` CRUD (`/api/v1/reminders/`), kanal tercihleri (uygulama içi / e-posta / web push), mükerrer engeli
- [ ] **(v1.2)** Günlük zamanlanmış job (`send_due_reminders`): zamanı gelen hatırlatıcıları gönderir, çıkış tarihi değişenleri günceller ve kullanıcıyı bilgilendirir, gönderilenleri `sent` yapar (idempotent: aynı bildirim iki kez gitmez)
- [ ] **(v1.2)** E-posta sağlayıcısı (SMTP/Resend/SES vb.) için **kullanıcıya sor**, anahtarlar yalnızca env'de; e-postalarda tek tıkla abonelikten çıkma
- [ ] **(v1.2)** Web push (VAPID) opsiyonel; kapalıysa e-posta + uygulama içi yeterli
- [ ] **(v1.2)** Misafir "Hatırlat"a bastığında giriş sonrası seçimin otomatik tamamlanması (localStorage'daki bekleyen hatırlatıcı → hesaba aktarım)

**Testler:** yetkisiz erişim (401/403), başka kullanıcının verisine erişememe (IDOR testi), merge mantığı; **hatırlatıcı:** doğru gün gönderim, çift gönderim yok, iptal edilen gönderilmiyor, çıkış tarihi değişince güncelleniyor, başka kullanıcının hatırlatıcısına erişilemiyor, bildirim dili kullanıcı tercihinde

**Kabul Kriterleri**
- Kullanıcı yalnızca kendi verisini görebiliyor (test kanıtlı)
- Şifreler asla düz metin/loglarda yok
- Giriş yapmamış kullanıcı arama, koleksiyon, oyuncu, yakında çıkacaklar ve Şans Globu'nu eksiksiz kullanabiliyor (E2E testle kanıtlı)

---

### 🟦 FAZ 7B — Film Defterim (Kişisel Not Defteri) (v1.3)
**Amaç:** Giriş yapan kullanıcı neyi izlediğini, neye kaç puan verdiğini ve ne düşündüğünü tek yerde görsün (bkz. §3.8).

**Görevler**
- [ ] `notebook` uygulaması: `NotebookEntry` modeli (`user + media_type + tmdb_id` unique; `status`, `is_favorite`, `rating_x2` 1–10, `note` ≤ 5000, `tags` ≤ 10, `watched_on`, `rewatch_count`, dizi `progress_season/episode`, `title_snapshot`)
- [ ] Doğrulama: puan yalnızca 1–10 tamsayı (`null` serbest), durum enum, not uzunluğu, etiket sayısı/uzunluğu; geçersizse 400
- [ ] Endpointler (§3.8): liste (filtre/sıralama/sayfalama/arama), tek kayıt GET/PUT/PATCH/DELETE, **toplu `lookup`**, `stats`, `export` (CSV/JSON)
- [ ] `stats` hesapları: toplam izlenen, toplam süre (`title_snapshot` süresinden), ortalama puan, puan dağılımı, tür dağılımı, aylık/yıllık sayılar, en yüksek puanlılar — N+1'siz, tek/az sorgu
- [ ] `title_snapshot` yenileme job'u (haftalık, yalnızca eksik/eski kayıtlar; TMDB kapalıyken defter yine açılır; **6 ayı aşan snapshot'lar yenilenir, yenilenemiyorsa TMDB'den gelen alanlar temizlenir** — kullanıcının kendi verisi (durum, puan, not) korunur)
- [ ] Web arayüzü: Defterim sayfası (sekmeler, filtre, arama), İstatistik sayfası, kartlarda/detayda hızlı eylemler, `AuthSoftGateModal` akışı (bekleyen işlem giriş sonrası tamamlanır)
- [ ] Entegrasyon: sonuç kartlarında `lookup` ile "İzledin ✓ · puanın"; arama/koleksiyon/globe'da **"izlediklerimi hariç tut"** filtresi (sunucu tarafı, `exclude_watched=true`)
- [ ] Şans Globu kaynağı: "İzlenecek listem"
- [ ] Hesap silme: tüm defter kayıtları kalıcı silinir; dışa aktarma kayıtların tamamını içerir
- [ ] (Opsiyonel, kullanıcı onaylarsa) Letterboxd CSV içe aktarma; "Zevkime göre öner" (yalnızca toplulaştırılmış özet LLM'e gider, varsayılan kapalı)
- [ ] Defter ve hesap sayfaları `noindex`; reklam yok

**Testler**
- **IDOR:** başka kullanıcının kaydını okuma/değiştirme/silme/dışa aktarma 403/404 (liste, tek kayıt, lookup, stats, export hepsi için)
- Unique kısıtı: aynı kullanıcı + aynı `media_type + tmdb_id` ikinci kayıt oluşturmaz (upsert); **aynı `tmdb_id`'li film ve dizi ayrı kayıt olur**
- Puan sınırları (0, 11, 5.5, "abc" reddedilir; 1 ve 10 kabul), not uzunluk sınırı, etiket sınırı
- `stats` doğruluğu: bilinen fixture ile toplam süre, ortalama, dağılım, aylık sayılar birebir
- `lookup` tek sorguda çalışır (sorgu sayısı testi), bilinmeyen kimlik hata vermez
- `exclude_watched` filtresi yalnızca `watched` durumunu eler; `want_to_watch` sonuçta kalır
- Not metninde `<script>` düz metin olarak saklanır/render edilir; not hiçbir LLM çağrısına girmez (mock ile kanıtlı)
- Misafir → üye akışı: bekleyen "puan ver" eylemi giriş sonrası kaydedilir; localStorage favorileri birleşir
- Hesap silme sonrası kayıt kalmaz

**Kabul Kriterleri**
- Üye bir yapımı tek tıkla "izledim" yapıp yıldız verebiliyor, not ekleyebiliyor; sayfa yenilenince ve başka cihazda görünüyor
- İstatistik sayfası gerçek veriyle doğru değerleri gösteriyor
- Başka kullanıcının verisine erişim imkânsız (test kanıtlı); notlar loglarda ve LLM isteklerinde yok
- Misafir hiçbir ekranda duvara çarpmıyor; yalnızca defter eylemlerinde nazik giriş daveti görüyor

---

### 🟦 FAZ 7C — Profil, Listeler, Paylaşım & Moderasyon Temeli (v1.6)
**Amaç:** Üyeler zevklerini kontrollü biçimde paylaşabilsin (bkz. §3.11). **Önce gizlilik ve moderasyon, sonra özellik.**

**Kararlar (v1.7):** Kullanıcı yaş sınırı, metinler, şikâyet süreci ve `noindex` için **genel geçer standart kararları** onayladı → §3.11 "Varsayılan Politika Kararları" uygulanır; ajan bu başlıklarda ayrıca soru sormaz. Yalnızca **`SUPPORT_EMAIL`** (iletişim adresi) ve veri sorumlusu adı/ünvanı kullanıcıdan istenir.

**Görevler**
- [ ] `social` uygulaması; `Profile` (`username` büyük-küçük harf duyarsız unique, `display_name`, `bio`, `avatar_kind`, `profile_visibility`, `show_stats`), rezerve/yasaklı kullanıcı adı listesi, değiştirme sınırı
- [ ] `NotebookEntry`'ye `visibility` (`private` varsayılan | `public`) ve `note_locked` alanları (migration; **mevcut kayıtlar `private` kalır**)
- [ ] `UserList` + `UserListItem` (`position` listede unique), sınırlar (50 liste / 200 öğe), toplu sıralama endpoint'i, kopyalama, görünürlük kuralı tek yerde (**merkezi izin fonksiyonu**: tüm okuma yolları buradan geçer)
- [ ] `NotebookShare` (token hash, scope, statuses, expires_at, revoked_at, view_count), oluşturma/iptal/listeleme, `GET /api/v1/shared/{token}/`; `X-Robots-Tag: noindex`
- [ ] Topluluk puanı: `community` endpoint'i (en az 5 oy eşiği), "bu yapımı puanlayanlar" (yalnızca profil + kayıt `public`)
- [ ] Moderasyon: `Report`, `Block`, yasaklı kelime filtresi (TR+EN), URL temizleme, hız sınırları, N şikâyette otomatik gizleme, Django admin şikâyet kuyruğu, kullanıcı askıya alma
- [ ] Web arayüzü: Profil sayfası, Profil/Gizlilik ayarları, Liste oluşturma/düzenleme (sürükle-bırak + **klavye ile sıralama**), Liste detay, "Defterimi paylaş" akışı (kapsam seçimi + not uyarısı + süre + iptal), Paylaşılan defter görünümü, Raporla/Engelle menüsü, topluluk puanı bileşeni
- [ ] Şans Globu kaynağı: "Bir listemden" ve "Herkese açık/bağlantılı bir listeden"
- [ ] Sayfalar `noindex` (kullanıcı içeriği); Kullanım Koşulları, Topluluk Kuralları, Şikâyet/Kaldırma sayfaları (kullanıcıyla netleşen metinlerle)
- [ ] Hesap silme: profil, listeler, paylaşımlar, şikâyet geçmişi (kişisel veri kısmı), engeller kalıcı silinir

**Testler (kritik: gizlilik sızıntısı)**
- **Görünürlük matrisi:** `private` içerik hiçbir yoldan sızmaz — profil sayfası, liste detayı, liste öğeleri, "bu yapımı puanlayanlar", topluluk ortalaması (eşik), arama sonuçları, paylaşılan defter, Şans Globu kaynakları, `sitemap.xml`, dışa aktarma (yalnızca sahibine), hata mesajları (varlık ifşası yok: 404 ile 403 ayırt edilemez)
- `unlisted` yalnızca bağlantıyla, `public` yalnızca profil açıksa profilde listelenir; profili `private` olan kullanıcının `public` kayıtları profil dışında da listelenmez
- Paylaşım: iptal edilen/süresi dolan token 404; yanlış token timing farkı yok (sabit-süre karşılaştırma); `ratings` kapsamında **not alanı yanıtta yok**; `note_locked` kayıt `ratings_notes` ile bile notsuz döner
- IDOR: başkasının listesini/öğesini/paylaşımını okuma, sıralama, silme, kopyalama (görünmeyen listeyi kopyalayamaz)
- Liste: `position` benzersizliği, toplu sıralama atomik (yarım sıralama yok), limitler (51. liste, 201. öğe reddedilir), aynı yapım iki kez eklenemez, aynı `tmdb_id`'li film+dizi ayrı öğe
- Kullanıcı adı: büyük-küçük harf çakışması, rezerve kelime, Unicode benzer karakter hilesi, değiştirme sınırı
- Metin alanları: `<script>`/HTML düz metin kalır, URL temizlenir, yasaklı kelime reddedilir, uzunluk sınırı
- Moderasyon: N şikâyette içerik otomatik gizlenir, admin geri açabilir; engellenen kullanıcı profili/listeyi göremez
- Hesap silme sonrası hiçbir herkese açık iz kalmaz (profil URL'si 404, paylaşım tokenları geçersiz)
- Topluluk ortalaması 4 oyda gösterilmez, 5 oyda gösterilir; ortalama özel puanları da içerir ama kimliği ifşa etmez
- **Girişsiz görüntüleme (v1.7):** oturumsuz istemci `public` profili, `public`/`unlisted` listeyi, paylaşılan defteri ve topluluk puanını **200 ile** görür; aynı istemci `private` olanı göremez, oluşturma/düzenleme/rapor uçlarında 401 alır
- Raporlama: aynı kullanıcının tekrar raporu sayılmaz; 24 saatten genç hesap raporu eşiğe sayılmaz; 3 farklı geçerli rapor → otomatik gizleme + sahibe bildirim; yönetici geri açınca görünür olur
- `include_adult=false` her TMDB çağrısında (mock ile kanıtlı); yetişkin içerik listeye eklenemez
- 18+ beyanı olmadan kayıt tamamlanmaz; doğum tarihi saklanmaz

**Kabul Kriterleri**
- Üye bir liste oluşturup sürükle-bırak (ve klavye) ile sıralayıp, `unlisted` bağlantıyla birine gönderebiliyor; alıcı hesapsız görebiliyor
- Defter paylaşım bağlantısı iptal edilince anında çalışmıyor; notlar yalnızca bilinçli seçimle görünüyor
- Görünürlük matrisi testleri tamamen yeşil; varsayılan her şey özel
- Şikâyet/engel akışı çalışıyor, admin kuyruğunda görülüyor
- Giriş yapmamış biri herkese açık profil/liste/paylaşılan defteri görüntüleyebiliyor (kayıt gerekmiyor); oluşturma için nazikçe giriş isteniyor
- Kullanım Koşulları, Topluluk Kuralları, Gizlilik/KVKK sayfaları TR/EN şablonlarla yayında; kayıtta 18+ beyanı zorunlu

---

### 🟦 FAZ 7D — Takip, Akış, Zevk Uyumu & Birlikte Seç (OPSİYONEL — kullanıcı onayı gerekir) (v1.6)
> **Ajan: Faz 7C canlıda stabil çalışmadan ve kullanıcı açıkça onaylamadan bu fazı başlatmaz.** Moderasyon kapasitesi kanıtlanmadan sosyal yüzeyi büyütmek bir riskdir.

**Görevler**
- [ ] **Birlikte Seç** (öncelikli, farkı yaratan özellik): oturum oluştur/katıl/süresi dolsun, havuz onayı, kesişim/birleşim, ortak Şans Globu, sorgu ile filtre, oturum bitince veri silme (§3.11)
- [ ] **Zevk uyumu:** ortak puanlanan ≥ 5 yapım üzerinden uyum yüzdesi (basit, açıklanabilir yöntem; ajan seçip `docs/`'ta açıklasın), "ikinizin de en sevdiği 3 film"; yetersiz veride gösterilmez
- [ ] **Takip + yapılandırılmış akış:** yalnızca `public` profillerde, serbest metin yok; engelleme ile uyumlu; akış sayfalı ve önbellekli
- [ ] Kullanıcı adı ile **tam eşleşme araması**; toplu kullanıcı listeleme yok

**Testler:** oturum süresi dolunca havuz silinir; katılımcı yalnızca onayladığı listeyi paylaşır, diğerinin defterini göremez; kesişimin doğruluğu (aynı `tmdb_id`'li film/dizi karışmaz); uyum yüzdesi bilinen fixture ile doğru; engellenen kullanıcı takip/oturum davet edemez; feed'de özel kayıt yok; 3. kişi oturuma sızamaz (token); oturum sayısı sınırı

**Kabul Kriterleri**
- İki üye bir bağlantıyla Birlikte Seç yapıp ortak havuzdan Şans Globu çevirebiliyor
- Oturum bittikten sonra birleşik veri tamamen silinmiş (testle kanıtlı)
- Feed'de yalnızca `public` ve yapılandırılmış olaylar var

---

### 🟦 FAZ 8 — Kalite, Güvenlik, Performans
**Görevler**
- [ ] Backend kapsam ≥ %85, Web kapsam ≥ %75
- [ ] E2E (Playwright): arama, oyuncu araması, globe, giriş, favori, **misafir akışı (girişsiz tüm keşif), defter (izledim → puan → not → istatistik)**, hesap silme, **sosyal: liste oluştur → sırala → bağlantıyla paylaş → alıcı hesapsız görür → iptal et → artık görünmez; özel içerik hiçbir ekranda sızmaz**
- [ ] Güvenlik: `bandit`, `pip-audit`, `npm audit`; CSP (Faz 10'da reklam/CMP alan adları **yalnızca bayrak açıkken** whitelist'e eklenir), HSTS, güvenli cookie, CORS whitelist
- [ ] **(v1.3)** Kişisel veri: defter notları loglarda, Sentry olaylarında ve LLM isteklerinde yok (testle kanıtlı); not/puan alanları için hız sınırı ve boyut sınırı
- [ ] Django `check --deploy` temiz
- [ ] Yük testi (k6/locust) — arama endpoint'i için temel senaryo. **(v1.8) Yalnızca yerelde veya çok küçük hacimle**; canlı Vercel/Neon/Gemini üzerinde yoğun yük testi **yapılmaz** (ücretsiz kotayı tüketir, servis şartlarına aykırı olabilir)
- [ ] N+1 sorgu kontrolü, gerekli DB indexleri
- [ ] LLM maliyet koruması: **temeli Faz 3'te atıldı (§3.10)**; burada yük testi altında kota/bütçe davranışı, cache hit oranı raporu, anormal hacim uyarısı doğrulanır
- [ ] Hata takibi: **ücretsiz seçenek** (Vercel'in kendi çalışma zamanı logları + yapılandırılmış hata kaydı). Sentry gibi harici servis yalnızca **ücretsiz planı doğrulanır ve kullanıcı onaylarsa** eklenir; aksi halde eklenmez
- [ ] Yapısal loglama (kişisel veri sızdırmadan)

**Kabul Kriterleri**
- Tüm CI adımları yeşil, kritik/yüksek güvenlik bulgusu yok
- p95 API gecikmesi hedefleri dokümante ve ölçülmüş

---

### 🟦 FAZ 9 — CI/CD & Ücretsiz Deploy (Vercel Hobby + Neon) (v1.8)
> DigitalOcean planı bırakıldı (yönetilen PostgreSQL en az ≈ $15/ay + App Platform ≈ $5/ay; hedef $0). **Hedef: aylık $0.** Bu faz, Faz 0'daki spike sonucuna ve ADR `0002-hosting.md` kararına bağlıdır.

**Altyapı ($0)**
- **Web + API:** Vercel Hobby (Vue arayüzü ve Django, Python fonksiyonu). Git bağlantısı: `main` → production, `develop` ve PR'lar → önizleme (preview) dağıtımı (Vercel'in Git entegrasyonu; ajan ayarı doğrular).
- **Veritabanı:** Neon ücretsiz PostgreSQL. **Üretim ve test için ayrı Neon projeleri** (ayrı DB, ayrı anahtarlar); ücretsiz plan proje sayısı ve toplam depolama sınırı `docs/cost.md`'de.
- **Alan adı / SSL:** Vercel'in ücretsiz `*.vercel.app` adresi ve otomatik SSL. **Özel alan adı ücretlidir; kullanıcı istemedikçe alınmaz.**
- **Zamanlayıcı:** Vercel Cron veya GitHub Actions zamanlanmış workflow (bkz. §3.7).
- **Yedek barındırma (spike kötü çıkarsa):** Render ücretsiz web servisi (uykulu) veya Cloud Run (fatura hesabı → yalnızca kullanıcı onayıyla). `Dockerfile` bunun için korunur.

**Görevler**
- [ ] GitHub Actions (yalnızca ücretsiz dakika kotası içinde):
  - `ci-backend.yml` → ruff, pytest (Postgres servisiyle), bandit
  - `ci-web.yml` → lint, type-check, vitest, build
  - (deploy Vercel'in Git entegrasyonuyla yapılır; ayrı `deploy.yml` gerekirse yalnızca zamanlanmış görev tetikleyici için)
- [ ] Migration'lar: yayına çıkmadan önce **güvenli ve geri alınabilir**; Neon'a uygulama adımı ve geri alma prosedürü `docs/runbook.md`'de (serverless fonksiyonlar çoklu çalıştığı için migration deploy içinde değil, **kontrollü ayrı adım**)
- [ ] Sağlık kontrolü: `/api/v1/health/`; DB uyku/uyanma durumu hata değil "uyanıyor" olarak ele alınır
- [ ] **Soğuk başlangıç UX'i:** ilk istek yavaşsa arayüzde anlaşılır yükleme durumu; sayfa açılışında arka planda hafif bir "ısıtma" isteği (`/health/`); statik sayfalar backend uyanmadan açılır
- [ ] **Yedekleme:** Neon ücretsiz planın yedek/geri yükleme olanaklarını **ajan resmi dokümandan doğrulasın**; her halükârda `pg_dump` ile dışa aktarma prosedürü (manuel veya zamanlanmış) ve **bir kez denenmiş geri yükleme** `docs/runbook.md`'de
- [ ] Ortam değişkenleri dokümantasyonu (Vercel panelinden girilir; sohbete/depoya yazılmaz)
- [ ] Gözlem: Vercel çalışma zamanı logları; ücretli izleme servisi **yok** (ücretsiz uptime servisi yalnızca planı doğrulanıp kullanıcı onaylarsa)
- [ ] `docs/cost.md` güncel: Vercel Hobby, Neon, Gemini, GitHub Actions limitleri + her birinde limit dolunca ne olacağı + **hiçbir serviste ödeme yöntemi tanımlı olmadığının** onayı
- [ ] **Limit izleme:** Vercel kullanımı (çağrı, aktif işlemci), Neon CU-saat ve depolama, Gemini kotası haftalık kontrol listesi; %80'de kullanıcıya haber verilir (arayüzde veya `docs/cost.md` kontrol listesinde)

**Kabul Kriterleri**
- `main`'e birleşince Vercel production'a çıkıyor; PR'lar önizleme alıyor
- Yayındaki sistemde hiçbir servis ücretli plana veya kart tanımına bağlı değil (kullanıcı panellerde doğruladı)
- Bir `pg_dump` yedeğinden geri yükleme başarıyla denenmiş; migration geri alma adımları yazılı
- Soğuk başlangıç ölçümü (`docs/deploy-spike.md`) yayındaki ortamda tekrarlanmış ve kabul eşiği içinde
- Limit dolduğunda sistem kapanmak yerine zarifçe düşüyor (klasik arama, önbellekten sunum), fatura riski yok

> **Ajan notu:** Vercel, Neon ve Google (Gemini) hesaplarını kullanıcı kendisi açar; ajan hiçbir anahtarı/şifreyi kod, commit veya sohbete **yazmaz**. Bir panel kart veya ücretli plan önerirse **kabul etme**, kullanıcıya sor.

---

### 🟦 FAZ 10 — Gelir Modeli: Reklam, Affiliate, (Opsiyonel) Premium — ⏸️ ERTELENDİ (v1.4)
> **DURUM: ERTELENDİ — AJAN BU FAZI UYGULAMAZ.** Ürün şimdilik ücretsiz ve ticari olmayandır (TMDB ücretsiz API şartı). Faz, yalnızca kullanıcı "gelir modeline geçelim" dediğinde ve §3.9'daki geçiş kontrol listesi tamamlandığında etkinleşir. Aşağıdaki içerik o gün için taslak olarak saklanır.
> Eski "Mobil Uygulama" fazı kaldırıldı (proje yalnızca web). Bu faz §3.9'u uygular.

**BAŞLAMADAN ÖNCE kullanıcıdan 4 karar al (varsayım yapma):**
1. **TMDB ticari lisansı / yazılı onay** alındı mı? (Alınmadıysa reklam ve Premium **açılmaz**; yalnızca hazırlık işleri yapılır.)
2. Hangi **reklam ağı** ile başlanacak? (Ajan güncel başvuru koşullarını kontrol edip 2–3 seçenek + artı/eksi sunsun.)
3. **Premium abonelik** istiyor mu? İstiyorsa ödeme sağlayıcısı (iyzico/Stripe vb.) ve fiyatlandırma.
4. **SSR/prerender** yaklaşımı (Faz 5 ADR'si) uygulanmış ve doğrulanmış mı?

**Görevler**
- [ ] ADR: `docs/adr/00XX-monetization.md` (kararlar, riskler, vazgeçme ölçütleri)
- [ ] **CMP / çerez onayı:** reklam ve analitik scriptleri onaydan önce yüklenmez; reddedilen/verilmeyen onayda yalnızca zorunlu çerezler; onay tercihini değiştirme bağlantısı footer'da
- [ ] Gizlilik politikası ve KVKK aydınlatma metni reklam/affiliate/ödeme için güncellenir
- [ ] `monetization` uygulaması: özellik bayrakları (`ADS_ENABLED`, `AFFILIATE_ENABLED`, `PREMIUM_ENABLED`), sunucudan istemciye **konfigürasyon endpoint'i** (`GET /api/v1/config/public/`)
- [ ] `AdSlot.vue`: ağ scriptini yalnızca (bayrak açık + onay var + kullanıcı Premium değil + izinli sayfa) koşulunda yükler; yer önceden ayrılır (CLS); lazy-load; "Reklam" etiketi; `ads.txt` yayımı
- [ ] Reklam **yasak bölgeleri:** hero arama alanı, Şans Globu animasyonu, Defterim/hesap/ayarlar sayfaları, hata sayfaları, boş sonuç sayfaları
- [ ] Affiliate: "Nerede izlenir?" bölümü (TMDB watch providers + gerekli veri atfı), uygun programlara `rel="sponsored nofollow noopener"` ve "iş ortağı bağlantısı" etiketi; program/lisans uygunluğu kullanıcıya sunulup onaylatılır
- [ ] (Opsiyonel) Sponsorlu koleksiyon rozeti ve editöryel bağımsızlık notu
- [ ] (Opsiyonel — yalnızca karar 3 "evet" ise) Premium: abonelik modeli, ödeme akışı, webhook doğrulama, fatura/makbuz, iptal/iade, plan durumu `accounts` ile ilişkilendirme, reklamsız mod, yüksek AI kotası
- [ ] **Maliyet/gelir ölçümü:** arama başına LLM maliyeti, cache hit oranı, misafir→üye dönüşümü, sayfa başına gelir (RPM); gizlilik dostu analitikte olay olarak (kişisel veri yok)
- [ ] Maliyet koruması: gelir < maliyet ise kota/AI özelliği sıkılaştırma planı `docs/runbook.md`'de

**Testler**
- `ADS_ENABLED=false` → hiçbir reklam scripti/isteği yok (Playwright ağ izleme ile kanıtlı)
- Onay yok/reddedildi → reklam scripti **yüklenmez**
- Premium kullanıcıda reklam yok; Defterim ve Şans Globu animasyonunda reklam yok
- `AdSlot` yer ayırma: CLS < 0.1 (Lighthouse/Playwright)
- Affiliate bağlantılarında `rel="sponsored nofollow noopener"` ve etiket var
- (Premium varsa) ödeme webhook imza doğrulaması, çift işleme yok (idempotent), iptal sonrası yetki düşüşü, test kartlarıyla uçtan uca akış (yalnızca sağlayıcının test modu)
- Kota davranışı: misafir/üye/Premium sınırları doğru

**Kabul Kriterleri**
- TMDB onayı/lisansı **belgelenmiş** (yoksa reklamlar prod'da kapalı)
- Reklam yalnızca onaydan sonra ve izinli bölgelerde görünüyor; Lighthouse Performance reklam açıkken ≥ 75, kapalıyken ≥ 85 (ölçüm kayıtlı)
- Reklam/affiliate/sponsorlu içerik açıkça etiketli
- Gelir ve maliyet metrikleri görülebiliyor

---

### 🟦 FAZ 11 — Lansman & Sonrası
- [ ] Gizlilik politikası, KVKK aydınlatma metni, çerez tercihleri; **kullanılan LLM sağlayıcısı ve ücretsiz katmanda sorguların sağlayıcı tarafından ürün geliştirmede kullanılabileceği açıkça yazılır** (sağlayıcı değişirse metin güncellenir)
- [ ] **(v1.6) Kullanıcı içeriği hukuki hazırlık:** Kullanım Koşulları, Topluluk Kuralları, şikâyet/kaldırma süreci, 18+ yaş beyanı, iletişim bilgisi: §3.11 "Varsayılan Politika Kararları" ile uygulanmış ve yayında olduğu doğrulanır; `docs/legal-notes.md`'de "halka açılmadan önce bir kez gözden geçirme" önerisi bulunur (geliştirmeyi engellemez)
- [ ] Analitik: **ücretsiz ve gizlilik dostu** seçenek (ör. Vercel Web Analytics — Hobby'de ayda 50.000 olay; ajan limiti doğrular) veya analitik yok. Ücretli analitik servisi eklenmez (Sıfır Ödeme Politikası)
- [ ] Search Console/sitemap gönderimi, indekslenme takibi (trafik reklam gelirinin ön koşulu)
- [ ] Geri bildirim butonu ("bu öneri iyi miydi?" 👍/👎 → ranking iyileştirme verisi)
- [ ] Sürüm notları, `CHANGELOG.md`, `v1.0.0` tag'i
- [ ] Koleksiyon kalitesi için geri bildirim: koleksiyon sayfalarında da 👍/👎, düşük skorlu yapımlar editör incelemesine düşer
- [ ] Fikir havuzu (v2): **PWA (ana ekrana eklenebilir web uygulaması)**, herkese açık liste keşfi/trend sayfası (moderasyon hazırsa), herkese açık yorumlar (moderasyon hazırsa), anlamsal arama (pgvector), arkadaşla ortak film seçme, "ruh haline göre" hızlı modlar, izleme platformu bilgisi (TMDB watch providers, film ve dizi için), yeni bölüm bildirimleri (devam eden dizi favorileri için)

---

## 7. TEST PİRAMİDİ ÖZETİ

| Katman | Araç | Ne test edilir |
|--------|------|----------------|
| Backend birim | pytest, pytest-django, responses/httpx-mock | Servisler, parser, ranker |
| Backend API | DRF APIClient | Endpoint, yetki, hata formatı |
| Web birim | Vitest + Vue Test Utils | Bileşen, store |
| Web E2E | Playwright | Uçtan uca kullanıcı akışı |
| Güvenlik | bandit, pip-audit, npm audit | Bağımlılık & kod taraması |
| Yük | k6/locust | Arama endpoint'i |

**Kural:** Dış servisler (TMDB, LLM sağlayıcıları) testlerde **mock'lanır**. Canlı çağrı sadece manuel/opsiyonel smoke testlerde.

---

## 8. ORTAM DEĞİŞKENLERİ (`.env.example`)

```
# Django
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Database
DATABASE_URL=postgres://cineglobe:cineglobe@localhost:5432/cineglobe
# Üretimde: Neon'un "pooled" bağlantı adresi (sslmode=require). Yalnızca Vercel panelinden girilir, depoya/sohbete yazılmaz.

# External APIs
TMDB_API_KEY=
LLM_PROVIDER_CHAIN=gemini,classic          # gemini,classic | anthropic,classic | gemini,anthropic,classic
GEMINI_API_KEY=                            # ücretsiz katman anahtarı (Google AI Studio); GİZLİ
GEMINI_MODEL=gemini-3.1-flash-lite         # güncel model kimliğini resmi dokümandan doğrula
ANTHROPIC_API_KEY=                         # opsiyonel; yalnızca Haiku 5.5'e geçilirse (ücretli)
ANTHROPIC_MODEL_PARSER=claude-haiku-5-5    # sorgu → filtre
ANTHROPIC_MODEL_EXPLAIN=claude-haiku-5-5   # "neden önerildi?" (isteğe bağlı/lazy)
LLM_PROVIDER_COOLDOWN_SECONDS=120          # devre kesici bekleme süresi
LLM_DAILY_BUDGET_USD=5       # tavan dolunca AI'sız klasik arama devreye girer (§3.10)
LLM_MAX_OUTPUT_TOKENS=700
SEARCH_QUERY_MAX_CHARS=300

# Cache & sayaçlar (v1.8): varsayılan veritabanı önbelleği; Redis YOK
CACHE_BACKEND=db            # db | locmem (testlerde). Redis eklenirse ayrıca belgelenir ve kullanıcı onayı gerekir
# REDIS_URL=                # kullanılmıyor (isteğe bağlı, şimdilik kapalı)

# Cron (v1.8): zamanlanmış görev endpoint'ini korur
CRON_SECRET=                # GİZLİ — yalnızca Vercel/GitHub secrets'ta

# i18n
DEFAULT_LANGUAGE=tr
SUPPORTED_LANGUAGES=tr,en

# Reminders / Notifications (Faz 7 & 10)
EMAIL_BACKEND_URL=          # SMTP/Resend/SES — sağlayıcı kullanıcıyla netleştirilecek
EMAIL_FROM=
VAPID_PUBLIC_KEY=           # web push (opsiyonel)
VAPID_PRIVATE_KEY=
UPCOMING_REGION=TR

# Access & quotas (Faz 7)
GUEST_DAILY_AI_SEARCHES=10  # başlangıç değeri; maliyete göre ayarlanır
USER_DAILY_AI_SEARCHES=40

# Social (Faz 7C/7D)
MAX_LISTS_PER_USER=50
MAX_ITEMS_PER_LIST=200
MAX_LISTS_CREATED_PER_DAY=10
REPORTS_AUTO_HIDE_THRESHOLD=3        # bu kadar FARKLI hesaptan şikâyette içerik otomatik gizlenir (admin inceler)
REPORT_REVIEW_TARGET_DAYS=7          # iç hedef, hukuki taahhüt değil
MIN_ACCOUNT_AGE=18                   # kayıtta beyan; doğum tarihi saklanmaz
SUPPORT_EMAIL=                       # şikâyet/kaldırma/KVKK talepleri için (kullanıcıdan alınır)
USERNAME_CHANGE_COOLDOWN_DAYS=30
COMMUNITY_MIN_VOTES=5                # topluluk ortalaması/uyum için en az oy
SHARE_DEFAULT_EXPIRY_DAYS=30
TOGETHER_SESSION_TTL_HOURS=24

# Monetization (Faz 10 — ERTELENDİ; şimdilik hepsi false/boş kalır, kod eklenmez)
ADS_ENABLED=false
AFFILIATE_ENABLED=false
PREMIUM_ENABLED=false
AD_NETWORK=                 # kullanıcı seçecek
AD_CLIENT_ID=               # herkese açık istemci kimliği (gizli değil)
PAYMENT_PROVIDER=           # yalnızca Premium onaylanırsa
PAYMENT_SECRET_KEY=         # GİZLİ — yalnızca env/secret manager
PAYMENT_WEBHOOK_SECRET=

# Monitoring (opsiyonel; ücretsiz planı doğrulanmadan ve kullanıcı onaylamadan doldurulmaz)
SENTRY_DSN=
```

---

## 9. "TAMAMDIR" TANIMI (Definition of Done — her faz için)

- [ ] Kabul kriterlerinin hepsi sağlandı
- [ ] Testler yazıldı ve yeşil
- [ ] Lint/format/type-check temiz
- [ ] Dokümantasyon güncellendi
- [ ] PR açıldı, CI yeşil, merge edildi
- [ ] Kullanıcıya faz özeti + nasıl çalıştırılır/test edilir bilgisi verildi
- [ ] Sonraki faz için onay alındı

---

## 10. AJANA İLK KOMUT

> **Faz sırası (v1.3):** 0 → 1 → 2 → 3 → 4 → **4B (Koleksiyonlar)** → **4C (Yakında Çıkacaklar)** → 5 → 6 → 7 (isteğe bağlı giriş, hatırlatıcılar) → **7B (Film Defterim)** → **7C (Profil, Listeler, Paylaşım, Moderasyon)** → *(opsiyonel, onayla)* **7D (Takip, Birlikte Seç)** → 8 → 9 → ~~10 (Gelir Modeli)~~ **ertelendi, atla** → 11 (Lansman). Mobil uygulama fazı kaldırıldı.
>
> **Hatırlatma:** Ürün ücretsiz ve reklamsızdır; gelir getiren hiçbir öğe eklenmez. Hesap isteğe bağlıdır; hiçbir keşif ekranı girişe bağlanmaz. LLM maliyet koruması (§3.10) Faz 3'ten itibaren zorunludur.
>
> "Bu dosyayı baştan sonuna oku. **Sadece Faz 0'ı** uygula. Bitince dur, yaptıklarını özetle, çalıştırma komutlarını ver ve Faz 1 için onay iste. Belirsiz bir nokta olursa varsayım yapmadan bana sor."
