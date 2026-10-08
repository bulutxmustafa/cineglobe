# 🎬 CineGlobe — Film & Dizi Keşif Platformu (Aşamalı Geliştirme Planı)

> **Bu dosya kodlama ajanı (Claude Code / Google Antigravity) için ana talimat dosyasıdır.**
> Çalışma adı: **CineGlobe** (istenirse değiştirilebilir).
> **Sürüm notu (v1.1):** Platform artık **film + dizi** destekler. Kodda "movie" yerine genel `Title` kavramı kullanılır (`media_type`: `movie` | `tv`).
> **Sürüm notu (v1.2):** Eklenenler: (a) **TR/EN çift dil** (arayüz + içerik + LLM çıktısı), (b) **Hazır Koleksiyonlar** (Sıkılmam Diyeceğiniz Filmler, Sürükleyici, Çerezlik, Kafanızı Dağıtacak, Başladığı Gibi Bitecek, Tersköşe…), (c) **Oyuncu filmografisi** (kronolojik + en güncel sıralama), (d) **Yakında Çıkacaklar** + **hatırlatıcı**. Yeni bölümler: §3.4–§3.7, Faz 4B, Faz 4C; Faz 2/5/7/10 güncellendi.

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
| F6 | **Web + Mobil** | Vue.js web, Flutter iOS/Android |
| F7 | **Çift dil: Türkçe / English** | Dil değiştirici; arayüz, film/dizi başlık-özet verisi, arama sorguları ve "neden önerildi?" metinleri seçilen dilde |
| F8 | **Hazır Koleksiyonlar (kürasyonlu kategoriler)** | "Sıkılmam diyeceğiniz filmler", "Sürükleyici", "Çerezlik", "Kafanızı dağıtacak", "Başladığı gibi bitecek", "Tersköşe" |
| F9 | **Oyuncu filmografisi** | Her oyuncunun sayfasında tüm film/dizileri; **kronolojik** (eski→yeni / yeni→eski) ve **en güncel** sıralama |
| F10 | **Yakında Çıkacaklar & Hatırlatıcı** | Vizyona/yayına girecek film ve diziler listesi; "Hatırlat" ile bildirim/e-posta |

### 1.3 Kapsam Dışı (v1)
Film/dizi izletme (streaming), sosyal ağ özellikleri, ödeme sistemi. (Şimdilik yok.)

---

## 2. TEKNOLOJİ KARARLARI (Gerekçeli)

| Katman | Seçim | Neden |
|--------|-------|-------|
| Backend | **Django 5 + Django REST Framework** | Olgun, güvenli varsayılanlar, admin paneli, PostgreSQL ile mükemmel uyum, ORM/migration |
| Veritabanı | **PostgreSQL 16** (+ `pgvector` opsiyonel) | İlişkisel veri + ileride anlamsal arama |
| Film & dizi verisi | **TMDB API** | Kapsamlı film, dizi, oyuncu ve anahtar kelime verisi (`/movie` ve `/tv` endpointleri) |
| Doğal dil anlama | **Claude API (Anthropic)** | Kullanıcı cümlesini yapılandırılmış filtreye çevirir |
| Web frontend | **Vue 3 + Vite + TypeScript + Pinia + Vue Router** | İstenen; hızlı ve modern |
| Stil | **Tailwind CSS** + özel tasarım tokenları | Premium görünüm için tutarlı sistem |
| Animasyon | **GSAP** (UI) + **three.js / globe.gl** (küre) | Şans Globu için |
| Mobil | **Flutter** (iOS + Android) | Tek kod tabanı, güçlü animasyon; Vue ile kod paylaşılamayacağı için React Native'in ek avantajı yok |
| Cache | **Redis** (önce basit DB/locmem, gerekirse Redis) | TMDB & LLM çağrılarını azaltır |
| Deploy | **DigitalOcean** (App Platform veya Droplet + Managed PostgreSQL) | İstenen |
| CI/CD | **GitHub Actions** | Test + deploy otomasyonu |
| Test | pytest, Vitest, Playwright, Flutter test | Her katman için |

> **Not (lisans):** TMDB ücretsiz kullanım genelde ticari olmayan projeler içindir ve **atıf (attribution) zorunludur**. Site gelir getirecekse TMDB ile ticari lisans konuşulmalı. Ajan bunu Faz 2'de kullanıcıya hatırlatmalı ve footer'a atıf koymalı.

---

## 3. MİMARİ

```
┌────────────┐   ┌──────────────┐
│  Vue Web   │   │ Flutter App  │
└─────┬──────┘   └──────┬───────┘
      └────────┬────────┘
               ▼
      ┌──────────────────┐
      │ Django REST API  │──► Claude API (sorgu → filtre)
      │  (/api/v1/...)   │──► TMDB API (film & dizi verisi)
      └───────┬──────────┘
              ▼
      PostgreSQL (+ Redis cache)
```

### 3.1 Doğal Dil Arama Akışı (KRİTİK)

1. Kullanıcı yazar: *"Silahlı çatışma olsun ama istihbarat da olsun"*
2. Backend, Claude'a sistem prompt'uyla gönderir; Claude **yalnızca JSON** döner:
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
- Kaynak: kullanıcının favori film ve dizileri (giriş yoksa tarayıcıda localStorage, giriş varsa DB).
- Kullanıcı isterse globe üzerinde **Film / Dizi / Hepsi** filtresi seçebilir.
- Boşsa: "Önce birkaç film veya dizi favorile" yönlendirmesi + popüler film/dizilerden demo modu.
- Animasyon: 3D dünya küresi, butona basınca ease-out ile hızlanıp yavaşlayarak döner; durunca seçilen yapımın afişi küreden "fırlar" (scale + glow) ve detay kartı açılır.
- Rastgelelik backend'de değil frontend'de yapılabilir; ama "aynısı tekrar çıkmasın" kuralı (son 3 seçimi hariç tut) uygulanır.
- `prefers-reduced-motion` açıksa animasyon sade fade'e düşer.

### 3.4 Çift Dil (TR / EN) — Uçtan Uca
Dil sadece buton etiketlerinden ibaret değildir; dört katmanda ele alınır:

1. **Arayüz metinleri:** Web `vue-i18n`, mobil `flutter_localizations` + ARB dosyaları. Çeviri anahtarları tek kaynaktan (`docs/i18n/keys.md`) yönetilir; metin kodun içine gömülmez.
2. **İçerik verisi:** Tüm API uçları `?lang=tr|en` (veya `Accept-Language`) kabul eder; TMDB'ye `language=tr-TR` / `en-US` olarak iletilir. **Fallback:** Türkçe özet/başlık boşsa İngilizceye düşülür (TMDB'de birçok yapımın TR özeti yoktur) ve arayüzde belli edilir.
3. **Arama & LLM:** Kullanıcı hangi dilde yazarsa yazsın sorgu anlaşılır (`language_hint` zaten var). "Neden önerildi?" açıklamaları **seçili arayüz diline** göre üretilir. Cache anahtarına `lang` eklenir (aksi halde TR cevabı EN kullanıcıya gider).
4. **Koleksiyon & etiket metinleri:** Koleksiyon adı/açıklaması, tür adları, rozetler iki dilli saklanır (`name_tr`, `name_en`).

**Kurallar**
- Varsayılan dil: tarayıcı/cihaz diline göre, yoksa `tr`. Seçim kalıcı (localStorage / kullanıcı profili).
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
- Subjektif koleksiyonlar (Tersköşe, Sürükleyici…) için **LLM doğrulama adımı (opsiyonel, toplu & cache'li):** aday listesi Claude'a verilir, "bu yapım koleksiyon temasına uyuyor mu?" 0–1 skor + tek cümle gerekçe döner. Maliyet için günde bir kez ön-hesaplanır (cron/management command), istek anında LLM çağrılmaz.
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
- Zamanlayıcı: günlük çalışan job (Django management command + cron / DO scheduled job / Celery beat — **ajan gerekçesiyle seçsin, ADR yazsın**; basitlik için cron + management command önerilir).
- Kanallar (öncelik sırasıyla): **uygulama içi bildirim** → **e-posta** → **web push** (VAPID) → **mobil push** (FCM/APNs, Faz 10).
- **Giriş zorunluluğu:** Hatırlatıcı hesaba bağlıdır (Faz 7'ye bağımlı). Misafir kullanıcı "Hatırlat"a basarsa giriş/kayıt'a yönlendirilir; seçim giriş sonrası otomatik tamamlanır.
- Kullanıcı hatırlatıcıları listeleyebilir/iptal edebilir. Aynı yapım için mükerrer hatırlatıcı engellenir (unique: `user + media_type + tmdb_id`).
- Bildirim dili kullanıcının dil tercihinde (TR/EN). Her e-postada tek tıkla abonelikten çıkma (KVKK/GDPR).
- Endpointler: `GET /api/v1/upcoming/?media_type=&genre=&month=&page=&lang=`, `POST/GET/DELETE /api/v1/reminders/`.

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
│   │   └── accounts/   # kullanıcı, favoriler
│   ├── tests/
│   ├── requirements/ (base.txt, dev.txt, prod.txt)
│   └── Dockerfile
├── web/                # Vue 3
├── mobile/             # Flutter
├── docs/               # mimari, API, karar kayıtları (ADR)
├── .github/workflows/  # ci-backend.yml, ci-web.yml, ci-mobile.yml, deploy.yml
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
- `.gitignore` (Python, Node, Flutter, `.env`, IDE)
- PR şablonu `.github/pull_request_template.md`
- Branch protection: PR + geçen CI zorunlu
- Secrets: GitHub → Settings → Secrets (DO token, TMDB key, Anthropic key)

---

## 6. FAZLAR

---

### 🟦 FAZ 0 — Proje Kurulumu & Zemin
**Amaç:** Boş ama sağlam bir iskelet.

**Görevler**
- [ ] GitHub reposu, `main` + `develop`, branch protection
- [ ] Klasör yapısı (bkz. §4), `.gitignore`, `.env.example`, `README.md` iskeleti
- [ ] `docker-compose.yml`: `postgres`, `backend` (ve ileride `redis`)
- [ ] Lint/format: `ruff` + `black` (Python), `eslint` + `prettier` (Vue), `flutter analyze`
- [ ] `pre-commit` hook'ları
- [ ] PR şablonu, `docs/adr/0001-tech-stack.md` (bu dosyadaki kararların kaydı)

**Kabul Kriterleri**
- `docker compose up` PostgreSQL'i sorunsuz ayağa kaldırır
- `pre-commit run --all-files` hatasız
- İlk commit'ler Conventional Commits formatında

**Commit örnekleri:** `chore: initialize monorepo structure`, `chore(ci): add pre-commit config`

---

### 🟦 FAZ 1 — Backend Temeli (Django + PostgreSQL)
**Görevler**
- [ ] Django projesi, settings ayrımı (`base/dev/prod`), env okuma (`django-environ`)
- [ ] PostgreSQL bağlantısı, DRF, `django-cors-headers`, `drf-spectacular` (OpenAPI)
- [ ] `GET /api/v1/health/` endpoint'i (DB kontrolü dahil)
- [ ] Global hata formatı (tutarlı JSON hata yapısı)
- [ ] Rate limiting (DRF throttling)
- [ ] Dockerfile (multi-stage, non-root kullanıcı)

**Testler:** health endpoint testi, settings yükleme testi

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
- [ ] Görsel URL yardımcıları (poster/backdrop boyutları)
- [ ] Footer için TMDB atıf metni hazırla; kullanıcıya lisans uyarısı ver
- [ ] **(v1.2) Dil desteği:** `TMDBClient` tüm çağrılarda `lang` (`tr-TR`/`en-US`) alır; boş TR alanlarda EN fallback; cache anahtarına `lang` eklenir
- [ ] **(v1.2)** Ek endpoint'ler: `person/{id}` detayı, `movie/upcoming`, `discover` için tarih/süre/oy aralığı parametreleri (koleksiyon ve yakında çıkacaklar için gerekli), `tv/on_the_air`

**Testler:** TMDB yanıtları **mock'lanır** (gerçek API'ye test çağrısı yok), hata/timeout senaryoları; TR boş → EN fallback testi

**Kabul Kriterleri**
- `GET /api/v1/titles/{media_type}/{tmdb_id}/` (`movie` veya `tv`) çalışıyor ve cache'liyor
- Aynı `tmdb_id`'li bir film ve bir dizi birbirini ezmiyor (testle kanıtlı)
- TMDB kapalıyken API 500 değil, anlamlı 503 döner
- Anahtarlar sadece env'den okunuyor

---

### 🟦 FAZ 3 — Doğal Dil Film & Dizi Arama (Projenin Kalbi)
**Görevler**
- [ ] `QueryParser` servisi: Claude API çağrısı + sistem prompt'u (bkz. §3.1)
- [ ] Pydantic şemaları: `SearchFilters` (doğrulama, güvenli varsayılanlar)
- [ ] Fallback: LLM başarısızsa basit tür/anahtar kelime eşleştirme
- [ ] `Retriever`: filtreden TMDB adayları üretme (discover + keyword); `media_type`'a göre film, dizi veya ikisi paralel
- [ ] `Ranker`: puan × oy güveni × anahtar kelime eşleşmesi; `genres_exclude` kesin eleme
- [ ] `Explainer`: her film/dizi için tek cümlelik "neden bu film?" (toplu çağrı)
- [ ] `POST /api/v1/search/` → `{ "query": "...", "media_type": "both" }` → yapımlar (her birinde `media_type`) + açıklamalar + uygulanan filtreler
- [ ] Sorgu cache'i + kullanıcı/IP başına rate limit
- [ ] Türkçe ve İngilizce sorgu desteği; "neden önerildi?" metni `lang` parametresine göre üretilir, cache anahtarında `lang` bulunur

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

**Kabul Kriterleri**
- Yukarıdaki 5 senaryo geçiyor (LLM mock'lu birim testler + 1 opsiyonel canlı smoke test)
- Ortalama yanıt süresi hedefi: cache'siz < 6 sn, cache'li < 300 ms
- Kullanıcıya dönen her sonuçta gerekçe ve doğru `media_type` var

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
- [ ] Sayfalar: **Ana Sayfa (Hero+Arama + koleksiyon şeridi)**, **Sonuçlar**, **Detay (film ve dizi için ortak şablon; dizide sezon/bölüm bilgisi paneli)**, **Oyuncu Sonuçları (Filmler / Diziler sekmeleri)**, **Oyuncu Sayfası (filmografi: Kronolojik / En Güncel / En İyi sıralama anahtarı)**, **Koleksiyonlar (liste) + Koleksiyon Detay**, **Yakında Çıkacaklar**, **Favoriler**, **404**
- [ ] Bileşenler: `SearchBox`, `TitleCard` (film/dizi rozeti ile), `TitleGrid`, `MediaTypeToggle`, `SeasonInfo`, `ReasonBadge`, `SkeletonCard`, `Navbar`, `Footer` (TMDB atıf), **`LanguageSwitcher` (TR | EN)**, **`CollectionCard` / `CollectionRail` (yatay kaydırmalı koleksiyon şeridi)**, **`FilmographyList` + `SortToggle` (en güncel / kronolojik / en iyi)**, **`UpcomingList` (tarih gruplu) + `RemindButton`**
- [ ] **(v1.2) i18n:** `vue-i18n`, `/tr` ve `/en` URL önekleri, `hreflang`, dil seçimi kalıcı, tüm API çağrılarına `lang`, TR içerik boşsa EN fallback göstergesi, tarih/sayı `Intl`
- [ ] **(v1.2) Koleksiyon deneyimi:** ana sayfada 6 koleksiyon kartı (ikon + ad + kısa açıklama), her kart `Koleksiyon Detay`'a gider; "Bu koleksiyondan şansımı dene" butonu (Şans Globu ile bağlantı Faz 6'da)
- [ ] **(v1.2) Yakında Çıkacaklar sayfası:** aylık/haftalık gruplama, Film/Dizi/Hepsi filtresi, "Hatırlat" butonu (misafir ise giriş istemi; gerçek hatırlatma Faz 7'de bağlanır)
- [ ] API katmanı (tipli, hata yönetimi, iptal edilebilir istekler)
- [ ] Erişilebilirlik: klavye gezinme, odak halkaları, alt metinler, kontrast AA
- [ ] Responsive: 360px → 1920px
- [ ] SEO: meta etiketleri, OG görselleri
- [ ] i18n: TR/EN

**Testler**
- Vitest: bileşen + store testleri
- Playwright: "ara → sonuç gör → detaya git" akışı (API mock'lu)

**Kabul Kriterleri**
- Lighthouse: Performance ≥ 85, Accessibility ≥ 95
- Mobil görünüm bozulmuyor
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
- [ ] Performans: mobilde düşük güçlü cihaz için düşük poligon/pixel ratio sınırı, `prefers-reduced-motion` desteği
- [ ] Küre için lazy-load (ana sayfa bundle'ını şişirmesin)

**Testler:** rastgele seçim mantığı (deterministik seed ile), boş liste, tek eleman, tekrar önleme

**Kabul Kriterleri**
- Orta seviye telefonda ≥ 45 FPS
- Animasyon bitince her zaman geçerli bir film/dizi gösteriliyor (edge-case'lerde takılma yok)

---

### 🟦 FAZ 7 — Kullanıcı Hesapları & Kalıcı Favoriler
**Görevler**
- [ ] Kayıt/giriş: e-posta + şifre (Argon2) ve **Google ile giriş** (opsiyonel)
- [ ] JWT (kısa ömürlü access + refresh) veya güvenli cookie tabanlı oturum — ajan gerekçesiyle seçsin, ADR yazsın
- [ ] `Favorite`, `WatchlistItem`, `SearchHistory` modelleri (hepsinde `media_type` + `tmdb_id`)
- [ ] Diziler için opsiyonel ilerleme takibi: "izleniyor / bitti", son izlenen sezon-bölüm
- [ ] Endpoint'ler: favori CRUD, geçmiş listeleme/silme
- [ ] localStorage favorilerini girişte hesaba **birleştirme (merge)**
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

---

### 🟦 FAZ 8 — Kalite, Güvenlik, Performans
**Görevler**
- [ ] Backend kapsam ≥ %85, Web kapsam ≥ %75
- [ ] E2E (Playwright): arama, oyuncu araması, globe, giriş, favori
- [ ] Güvenlik: `bandit`, `pip-audit`, `npm audit`; CSP, HSTS, güvenli cookie, CORS whitelist
- [ ] Django `check --deploy` temiz
- [ ] Yük testi (k6/locust) — arama endpoint'i için temel senaryo
- [ ] N+1 sorgu kontrolü, gerekli DB indexleri
- [ ] LLM maliyet koruması: günlük bütçe limiti, kullanıcı başına kota, cache hit oranı loglama
- [ ] Sentry (hata takibi) entegrasyonu
- [ ] Yapısal loglama (kişisel veri sızdırmadan)

**Kabul Kriterleri**
- Tüm CI adımları yeşil, kritik/yüksek güvenlik bulgusu yok
- p95 API gecikmesi hedefleri dokümante ve ölçülmüş

---

### 🟦 FAZ 9 — CI/CD & DigitalOcean Deploy
**Altyapı (öneri, maliyet/basitlik dengesi)**
- **Backend:** DigitalOcean App Platform (Docker) *veya* Droplet + Docker Compose + Nginx + Certbot
- **Veritabanı:** DigitalOcean **Managed PostgreSQL** (otomatik yedek, VPC içi bağlantı)
- **Web:** App Platform Static Site (veya Spaces + CDN)
- **Domain/SSL:** Let's Encrypt / DO yönetimli sertifika

**Görevler**
- [ ] GitHub Actions:
  - `ci-backend.yml` → ruff, pytest (Postgres servisiyle), bandit
  - `ci-web.yml` → lint, type-check, vitest, build
  - `deploy.yml` → `main`'e merge + tag'de deploy
- [ ] Ortamlar: `staging` ve `production` (ayrı DB, ayrı anahtarlar)
- [ ] Migration'lar deploy sırasında otomatik ama **güvenli** (geri alma planı)
- [ ] Health check + otomatik yeniden başlatma
- [ ] Veritabanı yedek/restore prosedürü **test edilip** `docs/runbook.md`'ye yazılsın
- [ ] Ortam değişkenleri dokümantasyonu
- [ ] Gözlem: uptime izleme (UptimeRobot vb.), log toplama

**Kabul Kriterleri**
- `develop` → staging'e otomatik, `main` → prod'a onaylı deploy
- Bir yedekten geri yükleme başarıyla denenmiş
- Deploy'da kesinti yok veya çok kısa; rollback adımları yazılı

> **Ajan notu:** DigitalOcean token, DB şifresi gibi bilgiler için kullanıcıdan iste; kod/commit içine ASLA yazma.

---

### 🟦 FAZ 10 — Mobil Uygulama (Flutter, iOS + Android)
**Görevler**
- [ ] Flutter projesi (`mobile/`), Riverpod, `go_router`, `dio`, `freezed`/`json_serializable`
- [ ] Web ile aynı tasarım dili: renk/typografi tokenları eşleştirilir
- [ ] Ekranlar: Ana (arama + Film/Dizi/Hepsi anahtarı), Sonuçlar, Detay (film/dizi), Oyuncu, Favoriler, Giriş, **Şans Globu**
- [ ] Şans Globu: Flutter'da `flutter_animate` + özel painter veya `three_dart`/hafif 3D çözümü; alternatif olarak 2D küre + dönüş animasyonu (performans önceliği)
- [ ] Güvenli token saklama (`flutter_secure_storage`)
- [ ] Ortam ayrımı (dev/staging/prod flavors)
- [ ] **(v1.2)** Ek ekranlar: **Koleksiyonlar** (liste + detay), **Oyuncu filmografisi** (sıralama: en güncel / kronolojik / en iyi), **Yakında Çıkacaklar** + hatırlatıcı
- [ ] **(v1.2) Çift dil:** `flutter_localizations` + ARB (TR/EN), cihaz diline göre başlangıç, uygulama içi dil değiştirici, API'ye `lang`
- [ ] **(v1.2) Mobil push:** FCM (Android) + APNs (iOS) ile hatırlatıcı bildirimleri; bildirim izni onboarding'de değil, ilk "Hatırlat" anında istenir
- [ ] Ayarlar: dil, tema, hesap silme, bildirim tercihleri
- [ ] Hata/çevrimdışı durum ekranları

**Testler:** birim + widget testleri, `integration_test` ile temel akış, golden testler (ana ekranlar)

**Yayın Hazırlığı**
- [ ] Uygulama ikonu/splash, mağaza görselleri
- [ ] Gizlilik politikası + kullanım koşulları sayfaları (mağazalar zorunlu tutar)
- [ ] Android: `flutter build appbundle`, Play Console iç test
- [ ] iOS: Apple Developer hesabı (ücretli), TestFlight
- [ ] CI: `ci-mobile.yml` (analyze + test + build)

**Kabul Kriterleri**
- Gerçek cihazlarda (1 iOS + 1 Android) temel akışlar çalışıyor
- `flutter analyze` temiz, testler yeşil

---

### 🟦 FAZ 11 — Lansman & Sonrası
- [ ] Gizlilik politikası, KVKK aydınlatma metni, çerez tercihleri
- [ ] Analitik (gizlilik dostu: Plausible/PostHog)
- [ ] Geri bildirim butonu ("bu öneri iyi miydi?" 👍/👎 → ranking iyileştirme verisi)
- [ ] Sürüm notları, `CHANGELOG.md`, `v1.0.0` tag'i
- [ ] Koleksiyon kalitesi için geri bildirim: koleksiyon sayfalarında da 👍/👎, düşük skorlu yapımlar editör incelemesine düşer
- [ ] Fikir havuzu (v2): kullanıcı tarafından oluşturulan/paylaşılan koleksiyonlar, anlamsal arama (pgvector), arkadaşla ortak film seçme, "ruh haline göre" hızlı modlar, izleme platformu bilgisi (TMDB watch providers, film ve dizi için), yeni bölüm bildirimleri (devam eden dizi favorileri için)

---

## 7. TEST PİRAMİDİ ÖZETİ

| Katman | Araç | Ne test edilir |
|--------|------|----------------|
| Backend birim | pytest, pytest-django, responses/httpx-mock | Servisler, parser, ranker |
| Backend API | DRF APIClient | Endpoint, yetki, hata formatı |
| Web birim | Vitest + Vue Test Utils | Bileşen, store |
| Web E2E | Playwright | Uçtan uca kullanıcı akışı |
| Mobil | flutter_test, integration_test | Widget + akış |
| Güvenlik | bandit, pip-audit, npm audit | Bağımlılık & kod taraması |
| Yük | k6/locust | Arama endpoint'i |

**Kural:** Dış servisler (TMDB, Claude) testlerde **mock'lanır**. Canlı çağrı sadece manuel/opsiyonel smoke testlerde.

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

# External APIs
TMDB_API_KEY=
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=            # kullanılacak model kimliği (güncel dokümandan doğrula)
LLM_DAILY_BUDGET_USD=5

# Cache
REDIS_URL=redis://localhost:6379/0

# i18n
DEFAULT_LANGUAGE=tr
SUPPORTED_LANGUAGES=tr,en

# Reminders / Notifications (Faz 7 & 10)
EMAIL_BACKEND_URL=          # SMTP/Resend/SES — sağlayıcı kullanıcıyla netleştirilecek
EMAIL_FROM=
VAPID_PUBLIC_KEY=           # web push (opsiyonel)
VAPID_PRIVATE_KEY=
FCM_CREDENTIALS_JSON_PATH=  # mobil push (Faz 10)
UPCOMING_REGION=TR

# Monitoring
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

> **Faz sırası (v1.2):** 0 → 1 → 2 → 3 → 4 → **4B (Koleksiyonlar)** → **4C (Yakında Çıkacaklar)** → 5 → 6 → 7 (hatırlatıcılar dahil) → 8 → 9 → 10 → 11.
>
> "Bu dosyayı baştan sonuna oku. **Sadece Faz 0'ı** uygula. Bitince dur, yaptıklarını özetle, çalıştırma komutlarını ver ve Faz 1 için onay iste. Belirsiz bir nokta olursa varsayım yapmadan bana sor."
