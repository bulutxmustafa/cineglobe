# CineGlobe API v1 Dokümantasyonu

Bu belge, CineGlobe Backend API endpoint'lerinin teknik detaylarını ve şemalarını içerir.

## 📌 İnteraktif Dokümantasyon Arayüzleri

Backend sunucusu çalışırken aşağıdaki arayüzlerden API şemasına ve test panellerine erişilebilir:
- **Swagger UI:** `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc:** `http://localhost:8000/api/schema/redoc/`
- **OpenAPI 3.0 Şeması (JSON/YAML):** `http://localhost:8000/api/schema/`

---

## 🌐 Çoklu Dil Desteği (i18n: TR / EN)

API varsayılan olarak **Türkçe (tr)** içerik sunar. İngilizce dil desteği için isteklerde iki yöntem kullanılabilir:
1. **Query Parametresi:** `?lang=en` veya `?lang=tr`
2. **HTTP Header:** `Accept-Language: en` veya `Accept-Language: tr`

---

## 🔍 Sistem & Sağlık Kontrolleri

### `GET /api/v1/health/`
Sistemin ve veritabanının (PostgreSQL) hazır ve erişilebilir olduğunu doğrular.

* **Yetkilendirme:** Açık (Public)
* **Rate Limiting:** `120 istek / dakika` (health scope)

#### Başarılı Yanıt (HTTP 200 OK)
```json
{
  "status": "ok",
  "db": "ok"
}
```

#### Hata Yanıtı (HTTP 503 Service Unavailable)
Veritabanı bağlantısı kopmuşsa veya erişilemiyorsa:
```json
{
  "status": "error",
  "db": "unavailable"
}
```

---

## 🎬 Katalog (Catalog) Endpoint'leri

### `GET /api/v1/titles/{media_type}/{tmdb_id}/`
Belirtilen film (`movie`) veya dizi (`tv`) detaylarını getirir. Veri ilk çağrıda TMDB'den alınarak yerel veritabanında ve önbellekte saklanır.

* **Parametreler:**
  - `media_type` (path, zorunlu): `movie` veya `tv`
  - `tmdb_id` (path, zorunlu): TMDB tam sayı kimliği
  - `lang` (query, opsiyonel): `tr` veya `en` (varsayılan: `tr`)
* **Önbellek Stratejisi:**
  - Film / Tamamlanmış dizi detayı: 24 saat
  - Devam eden dizi detayı: 6 saat
* **Kimlik Çakışma Koruması:** TMDB'de aynı kimliğe sahip bir film ve bir dizi birbirini asla ezmez; `(media_type, tmdb_id)` bileşik anahtarı ile saklanır.

#### Başarılı Yanıt (HTTP 200 OK)
```json
{
  "id": 1,
  "media_type": "movie",
  "tmdb_id": 550,
  "title": "Dövüş Kulübü",
  "title_en": "Fight Club",
  "display_title": "Dövüş Kulübü",
  "original_title": "Fight Club",
  "overview": "Birinci kural: Dövüş Kulübü hakkında konuşma.",
  "overview_en": "An insomniac office worker...",
  "display_overview": "Birinci kural: Dövüş Kulübü hakkında konuşma.",
  "poster_url": "https://image.tmdb.org/t/p/w500/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
  "backdrop_url": "https://image.tmdb.org/t/p/w1280/hZkgoQYus5vegHoetLkCJzb17zJ.jpg",
  "vote_average": 8.4,
  "vote_count": 27000,
  "release_date": "1999-10-15"
}
```

---

## 🔎 Doğal Dil Arama (Search)

### `POST /api/v1/search/`
Serbest metinle yazılmış bir isteği ("gerilim olsun ama korku içermesin") film/dizi önerilerine çevirir. Her sonuç, seçili dilde tek cümlelik bir **"Neden önerildi?"** gerekçesi taşır.

* **Yetkilendirme:** Açık (Public)
* **Rate Limiting:** `20 istek / dakika` (`search` scope) + genel anon/user limitleri
* **Günlük AI kotası:** misafir `GUEST_DAILY_AI_SEARCHES` (IP özetine göre), üye `USER_DAILY_AI_SEARCHES`; gece yarısı (Europe/Istanbul) sıfırlanır. Kota dolunca istek **reddedilmez**, klasik aramayla yanıtlanır (`ai_status=quota_exceeded`). Önbellekten dönen arama kota tüketmez.
* **Önbellek:** Aynı sorgu (büyük/küçük harf ve boşluk farkı gözetmeksizin) + `media_type` + `lang` üçlüsü `SEARCH_CACHE_TTL_SECONDS` (varsayılan 1 saat) boyunca önbellekten döner. `lang` anahtarın parçasıdır; TR cevabı EN kullanıcıya gitmez.

#### İstek Gövdesi
```json
{
  "query": "kısa bölümlü, hafif, komik bir dizi",
  "media_type": "both",
  "lang": "tr"
}
```
| Alan | Zorunlu | Açıklama |
|------|---------|----------|
| `query` | evet | En fazla 300 karakter. Boş/anlamsız sorgu → `400 invalid_query` |
| `media_type` | hayır | `movie` \| `tv` \| `both` (varsayılan). `both` dışındaki değer, sorgudan çıkarılan türü ezer (arayüzdeki Film/Dizi anahtarı) |
| `lang` | hayır | `tr` \| `en`. Verilmezse `?lang=` ya da `Accept-Language` kullanılır |

#### İşleyiş
1. **LLM sağlayıcı zinciri** (`LLM_PROVIDER_CHAIN`, varsayılan `gemini,classic`): sorgu sırayla denenen sağlayıcılara gider: Gemini Flash-Lite (ücretsiz katman) → (isteğe bağlı) Claude Haiku 5.5 → klasik. Kullanıcı metni `<user_query>` etiketleri içinde **veri** olarak gönderilir; çıktı yalnızca `SearchFilters` şemasına uyabilir (prompt injection davranışı değiştiremez). LLM'e kullanıcı kimliği, e-posta veya IP **gitmez**.
2. **Yedek (klasik arama):** Anahtar yoksa, sağlayıcı 429/zaman aşımı/5xx/geçersiz JSON (1 yeniden denemeden sonra) döndürürse, kota ya da günlük bütçe dolduysa kural tabanlı TR/EN ayrıştırıcı devreye girer. Arama LLM yüzünden asla 500 vermez. Hata veren sağlayıcı 60 sn boyunca denenmez (devre kesici). `parser` hangi sağlayıcının yanıtladığını (`gemini` | `anthropic` | `classic`), `ai_status` nedenini (`ok` | `quota_exceeded` | `budget_exceeded` | `fallback`) gösterir. `ok` dışındaki yanıtlar önbelleğe alınmaz.
3. **Retriever:** Filtreler film ve dizi için ayrı TMDB `discover` parametrelerine çevrilir (tür ID'leri farklı). `both` ise iki sorgu paralel atılır. Anahtar kelime eşleşmesi çok dar kalırsa (< 5 sonuç) anahtar kelimesiz ikinci sorguyla tamamlanır.
4. **Ranker:** Bayes ortalamalı puan (film için 1000, dizi için 300 oy güven eşiği) + anahtar kelime/tür uyumu bonusu. `genres_exclude` kesin elemedir. Tekilleştirme `(media_type, tmdb_id)` ile yapılır; aynı ID'li film ve dizi birbirini silmez.
5. **Gerekçeler:** Her sonuç LLM'siz, seçili dilde bir şablon gerekçe alır. `ai_status=ok` ise ilk `LLM_EXPLAIN_TOP_N` (varsayılan 3) sonuç için tek toplu LLM çağrısıyla spoiler içermeyen gerekçeler üretilir (maliyet: [docs/cost.md](cost.md)).

#### Başarılı Yanıt (HTTP 200 OK)
```json
{
  "query": "kısa bölümlü, hafif, komik bir dizi",
  "lang": "tr",
  "media_type": "tv",
  "parser": "gemini",
  "ai_status": "ok",
  "filters": {
    "intent": "discover",
    "media_type": "tv",
    "genres_include": ["Comedy"],
    "genres_exclude": [],
    "keywords": [],
    "moods": ["lighthearted"],
    "people": [],
    "year_from": null,
    "year_to": null,
    "min_rating": null,
    "runtime_max": null,
    "episode_runtime_max": 30,
    "max_seasons": null,
    "status": "any",
    "language_hint": "tr"
  },
  "count": 20,
  "results": [
    {
      "media_type": "tv",
      "tmdb_id": 1400,
      "title": "Seinfeld",
      "display_title": "Seinfeld",
      "original_title": "Seinfeld",
      "overview": "…",
      "poster_url": "https://image.tmdb.org/t/p/w500/….jpg",
      "backdrop_url": "https://image.tmdb.org/t/p/w1280/….jpg",
      "vote_average": 8.3,
      "vote_count": 4800,
      "popularity": 120.5,
      "release_date": "1989-07-05",
      "genre_ids": [35],
      "score": 0.8521,
      "reason": "Yarım saatlik bölümleriyle hafif ve keyifli bir klasik komedi."
    }
  ],
  "took_ms": 2140,
  "cached": false
}
```

#### Hata Yanıtları
| Durum | `code` | Ne zaman |
|-------|--------|----------|
| 400 | `invalid_query` | Boş, 2 karakterden kısa, harf içermeyen ya da izleme tercihi içermeyen sorgu (mesajda örnek sorgu önerilir). `details.ai_status` sorgunun AI ile mi klasik ayrıştırıcıyla mı değerlendirildiğini söyler |
| 400 | `invalid` | Eksik `query` alanı veya geçersiz `media_type`/`lang` |
| 429 | `throttled` | Rate limit aşıldı |
| 503 | `service_unavailable` | TMDB erişilemiyor veya `TMDB_API_KEY` tanımlı değil |

---

## 🗂️ Hazır Koleksiyonlar (Collections) — Faz 4B

Her koleksiyon bir **tarif (recipe)** ile üretilir: TMDB'den aday filmler toplanır, hariç tutulan türler kesin olarak elenir, oy güvenine göre sıralanır, en fazla 100 yapım tutulur. Editör Django admin'den **kod değiştirmeden** koleksiyon ekleyebilir veya düzenleyebilir:
- **sabitleme** (`editor_pins`): listede en başta gösterilir,
- **engelleme** (`editor_blocklist`): listede hiç gösterilmez.

Kaydedilen değişiklik bir sonraki istekte görünür: önbellek anahtarı, düzenlenebilir alanların özetini içeriyor.

**Başlangıç koleksiyonları** (2026-10-08'de onaylandı; gerçek TMDB verisiyle her biri ≥ 20 sonuç): `never-boring`, `immersive`, `snack-watch`, `switch-off`, `start-to-finish`, `curveball`.

> **Not (Tersköşe):** TMDB'de "plot twist" gibi anahtar kelimeler çok az filme etiketli; örneğin Shutter Island'da hiç yok. Bu yüzden `curveball`, anahtar kelime havuzuna ek olarak bilinen tersköşe filmleri kimlikleriyle sabitler. Gerekçe metni sürprizi asla açık etmez (plan §3.5 spoiler kuralı).

### `GET /api/v1/collections/?lang=tr`
Aktif koleksiyonlar (`slug`, `name`, `description`, `icon`, `media_type`), `sort_order` sırasıyla.

### `GET /api/v1/collections/{slug}/?media_type=both&page=1&lang=tr`
Sayfa başına 20 yapım. Her yapımda editörün yazdığı spoiler içermeyen `reason` ve `pinned` alanları bulunur.
- Önbellek süresi: `COLLECTION_CACHE_TTL_SECONDS` (6 saat).
- Bilinmeyen veya pasif koleksiyon → `404`. TMDB erişilemezse → `503`.

### `GET /api/v1/collections/{slug}/random/?exclude=movie:550,tv:1396&lang=tr`
Şans Globu için koleksiyondan rastgele bir yapım. `exclude` ile son seçimler tekrar gelmez; hepsi hariçse yine bir yapım döner. Her çevirme taze olduğu için CDN'de önbelleğe alınmaz.

### CDN önbelleği (plan v1.8)
Liste ve detay yanıtları, `lang` parametresi URL'de açıkça varsa `Cache-Control: public, s-maxage=3600` ile döner. Böylece Vercel CDN'i tekrar eden istekleri Django'ya ve Neon'a uğramadan karşılar.
- Dil yalnızca `Accept-Language` başlığından geliyorsa yanıt `private` olur, çünkü CDN önbelleği URL'ye göre tutar ve farklı dil başlıklarını ayırt edemez.
- Bu uçlar kimlik doğrulama yapmaz. Böylece yanıtta `Vary: Cookie` oluşmaz ve CDN yanıtı herkesle paylaşabilir.

---

## 📅 Yakında Çıkacaklar (Upcoming) — Faz 4C

### `GET /api/v1/upcoming/?media_type=both&genre=&month=&page=1&lang=tr`
Bugün (Europe/Istanbul) veya sonrasında çıkacak film ve diziler, tarihe göre sıralı. Sayfa başına 20 kayıt.

| Parametre | Değerler |
|---|---|
| `media_type` | `both` (varsayılan) · `movie` · `tv` |
| `genre` | Mantıksal tür adı (ör. `Comedy`, `Thriller`); dizide karşılığı olmayan türler için yedek türler kullanılır |
| `month` | `YYYY-MM` |

**Kaynaklar ve kurallar** (2026-10-08'de canlı TMDB verisiyle doğrulandı):
- **Filmler:** Önce `region=TR` sorgusuyla **Türkiye vizyon tarihi** (TMDB bu sorguda `release_date` alanına Türkiye tarihini koyuyor). Türkiye tarihi olmayan filmler global ilk vizyon tarihiyle eklenir. Hangisinin kullanıldığını `region` alanı gösterir (`TR` | `global`).
- **Diziler:**
  - Yeni başlayan diziler.
  - Yeni sezona başlayan diziler: `next_episode_to_air` sezonun **1. bölümü** olmalı (`season_number` alanı). Sezon ortasındaki haftalık bölümler listelenmez.
  - Talk-show, haber ve reality dizileri hariç.
- **Popülerlik eşiği:** Global kaynaklı yapımlar için `UPCOMING_MIN_POPULARITY` (8). Türkiye vizyon tarihi olan filmler her zaman listelenir.
- **Çıkmış yapımlar:** listeden otomatik düşer. Liste her İstanbul günü için ayrı önbelleğe alınır (`UPCOMING_CACHE_TTL_SECONDS`, 4 saat); CDN'de 30 dk tutulur.

**Gruplar** (`group` alanı ve sayfa bazında `groups` listesi):

| Grup | Kural |
|---|---|
| `this_week` | bugün … bugün+6 gün |
| `this_month` | aynı takvim ayı, bir haftadan sonra |
| `later` | sonraki aylar |
| `tba` | tarihi açıklanmamış (`date_precision: "unknown"`) |

> **Not:** TMDB tarih kesinliğini (gün/ay/yıl) bildirmiyor. Tarih varsa `date_precision: "day"`, yoksa `"unknown"` döner.
>
> **Bilinen eksik:** Türkçe çevirisi olmayan yabancı dizilerin adı orijinal dilinde gelir (ör. Korece). Arayüz bu durumda `original_title` ve İngilizce ad gösterimini Faz 5'te ele alacak.

### Hatırlatıcılar (servis katmanı hazır; uç noktalar Faz 7'de)
`Reminder` modeli:
- **Tekillik:** kullanıcı + `media_type` + `tmdb_id` (aynı yapıma ikinci istek mevcut hatırlatıcıyı günceller ya da yeniden etkinleştirir).
- **Zamanlama:** `remind_on` = `release_day` · `one_day_before` · `one_week_before`.
- **Kanallar:** `in_app` · `email` · `push`.
- **Durum:** `pending` · `sent` · `cancelled`.
- **Tarih:** Filmler için Türkiye sinema tarihi (yoksa global), diziler için gala ya da yeni sezonun ilk bölümü kullanılır.
- **Reddedilen durumlar:** Çıkmış yapım (`already_released`) ve yaklaşan sezonu olmayan dizi (`no_upcoming_season`).
- **Günlük iş:** `refresh_release_dates` ertelenen tarihleri yakalar ve `release_date_changed_at` alanını işaretler. Gönderim Faz 7'de bağlanacak.

---

## 🎭 Oyuncular (People) — Faz 4

Tüm uçlar `?lang=tr|en` (veya `Accept-Language`) kabul eder. TMDB erişilemezse `503 service_unavailable` döner.

### Sıralama kuralları (plan §3.2)
"En iyi yapımlar" listesine yalnızca şunlar girer:
- **Başrol:** filmde ilk 5 oyuncu (`order ≤ PERSON_LEAD_MAX_ORDER`=4). Dizide `order` bilgisi gelmediği için, en az `PERSON_MIN_EPISODES`=3 bölümde oynamış olmak (tek bölümlük konuk rolleri elenir).
- **Oy eşiği:** film için `PERSON_MIN_VOTES_MOVIE`=1000, dizi için `PERSON_MIN_VOTES_TV`=300 oy. Az oyla şişmiş puanlar elenir.
- **Gürültü yok:** `Self`, `Himself/Herself`, arşiv görüntüsü ve "Uncredited" rolleri; talk-show, haber ve reality dizileri.
- Çıkmış yapımlar (gelecek tarihliler hariç). Puana göre sıralanır; bölüm başına en fazla 10 yapım.

### `POST /api/v1/people/top-titles/`
Bir oyuncunun en iyi filmleri ve/veya dizileri.

```json
{ "name": "RDJ", "media_type": "both", "lang": "tr" }
```
`name` yerine `person_id` (TMDB kimliği) de verilebilir. `media_type`: `both` (varsayılan: iki ayrı bölüm) | `movie` | `tv`.

**İsim çözümleme:** önce takma ad tablosu (`RDJ` → Robert Downey Jr.), sonra TMDB kişi araması. Sonuç yoksa soyadıyla arama ve benzerlik kontrolü yapılır, böylece "Brayn Cranston" → Bryan Cranston. Doğal dil aramasında takma adları LLM de çözer.

**Yanıtlar:**
- `status: "found"` → `person`, `candidates` (aynı isimli diğer kişiler), `sections.movies` / `sections.series`. Her yapımda kısa bir `reason` var (örn. "Walter White rolüyle, 62 bölüm · TMDB'de 18.781 oyla 8.9/10.").
- `status: "ambiguous"` → aynı isimli kişiler arasında popülerlik farkı belirgin değil (en popüler, ikinciden en az 3 kat popüler değil). `candidates` listesinden seçilip `person_id` ile tekrar istenir.
- `404 person_not_found` → nazik mesaj ve öneri; `details.query` aranan isim.

### `GET /api/v1/people/{tmdb_id}/filmography/`
Tam filmografi (plan §3.6).

| Parametre | Değerler | Varsayılan |
|---|---|---|
| `sort` | `newest` (en güncel) · `oldest` (kronolojik) · `rating` (oy eşiğini geçenler önce) · `popularity` | `newest` |
| `media_type` | `both` · `movie` · `tv` | `both` |
| `role` | `acting` · `directing` · `production` · `writing` | `acting` |
| `lead_only` | başrol / tekrarlayan rol filtresi (yalnızca `acting`) | `true` |
| `include_all` | `true` ise Self/arşiv/talk-show kayıtları da gelir | `false` |
| `page` | 20'şer kayıt | `1` |

- **Tarihi olmayan** kayıtlar her sıralamada listenin sonundadır.
- **Gelecek tarihli** kayıtlar `results` içinde değil, ayrı `upcoming` ("Yakında") grubunda döner (yalnızca 1. sayfada; İstanbul saatiyle bugünden sonrası).
- Aynı yapımda birden çok rol (karakter/iş) tek kayıtta birleşir (`characters`, `jobs`). Aynı TMDB kimliğine sahip film ve dizi ayrı kalır.
- Dizi kayıtlarında `episode_count` ve kişinin diziye ilk çıktığı yıl (`first_credit_year`) bulunur. Dizinin bitiş yılı bu TMDB yanıtında olmadığı için verilmez.
- `hidden_noise_count`: gizlenen Self/arşiv/talk-show kaydı sayısı ("Tümünü göster" düğmesi için).

### `GET /api/v1/people/{tmdb_id}/`
Biyografi, doğum yılı, fotoğraf ve en çok oylanan 4 başrol (`known_for`). TMDB'de Türkçe biyografi yoksa İngilizcesi döner ve `biography_is_fallback: true` olur (arayüzde belirtilmesi için).

### `GET /api/v1/people/search/?query=`
İsimle kişi araması (en fazla 10 sonuç; yetişkin içerik hariç).

### Doğal dil aramasında oyuncu niyeti
`POST /api/v1/search/` sorgusu bir oyuncunun en iyi işlerini soruyorsa ("RDJ'nin en iyi filmleri"), yanıttaki `person` alanı `top-titles` ile aynı yapıda bir blok taşır; diğer sorgularda `null` olur.

---

## 👤 Hesaplar (isteğe bağlı) — Faz 7

Keşif özelliklerinin hepsi (arama, koleksiyonlar, oyuncular, yakında çıkacaklar, Şans Globu) **hesapsız** çalışır. Hesap şunları ekler:
- hatırlatıcılar,
- arama geçmişi,
- daha yüksek günlük AI arama kotası,
- Film Defterim (Faz 7B).

Kimlik doğrulama **oturum çerezi + CSRF** ile yapılır ([ADR-0005](adr/0005-auth-session-cookie.md)). Yazma isteklerinde `X-CSRFToken` başlığı gerekir: değer, `GET /api/v1/auth/csrf/` çağrısının bıraktığı `csrftoken` çerezinden okunur. Giriş yapılmadan kişisel bir uca istek gelirse `403` döner.

| Uç nokta | Açıklama |
|---|---|
| `GET /api/v1/auth/csrf/` | CSRF çerezini ayarlar |
| `POST /api/v1/auth/register/` | `{email, password, preferred_language, age_confirmed: true}` → hesap açar ve giriş yapar (`201`). 18+ beyanı zorunludur; doğum tarihi toplanmaz |
| `POST /api/v1/auth/login/` | `{email, password}`. Yanlış şifre ile kayıtlı olmayan e-posta aynı hatayı alır |
| `POST /api/v1/auth/logout/` | Çıkış (`204`) |
| `POST /api/v1/auth/password/change/` | `{current_password, new_password}`. Bu oturum açık kalır |
| `POST /api/v1/auth/password/reset/` | `{email}` → her zaman `200`; hesap varsa e-postayla bağlantı gider |
| `POST /api/v1/auth/password/reset/confirm/` | `{uid, token, new_password}`. Bağlantı bir kez kullanılabilir |
| `GET /api/v1/auth/unsubscribe/?token=` | E-postadaki tek tıkla abonelikten çıkma bağlantısı |
| `GET` / `PATCH /api/v1/me/` | Profil; değiştirilebilir alanlar `preferred_language` ve `email_notifications` |
| `DELETE /api/v1/me/` | `{password}` → hesabı ve **tüm verileri** kalıcı siler |
| `GET /api/v1/me/export/` | Tüm verilerim, JSON dosyası olarak (KVKK/GDPR) |
| `GET` / `DELETE /api/v1/me/search-history/` | Kendi arama geçmişim (son 100); tek tek silmek için `/{id}/` |
| `GET` / `POST /api/v1/me/notifications/` | Uygulama içi bildirimler; `POST` hepsini okundu işaretler |

**Hız sınırı:** kayıt, giriş ve şifre sıfırlama dakikada 10 istek.

**Arama yanıtındaki kota bilgisi:** `quota` alanı `{signed_in, limit, remaining, suggest_signup}` içerir. Misafirin kotası dolduğunda `suggest_signup: true` döner ve arayüz "ücretsiz hesap aç" önerir.

## 📓 Film Defterim — Faz 7B

Giriş gerektirir; her kullanıcı yalnızca kendi kayıtlarını görür. Başka bir kullanıcının kaydına yapılan istek `404` döner, kaydın var olup olmadığı belli edilmez.

Her yapım için **tek kayıt** tutulur (kullanıcı + `media_type` + `tmdb_id`). Kayıt şunları içerir:
- `status`: `want_to_watch` · `watching` · `watched` · `dropped`
- `is_favorite`
- `rating_x2`: 1–10 tamsayı; arayüzde 0,5–5 yıldız
- `note`: ≤ 5000 karakter, **düz metin** olarak saklanır ve **asla LLM'e gönderilmez**
- `tags`: ≤ 10 etiket, her biri ≤ 30 karakter
- `watched_on`: `watched` yapılınca kendiliğinden bugünün tarihi atanır
- `rewatch_count`
- `progress_season` / `progress_episode`

Kayıt ilk oluşturulurken TMDB'den bir **anlık görüntü** alınır: başlık, yıl, afiş, türler ve süre. Böylece TMDB kapalıyken bile defter ve istatistikler çalışır.

| Uç nokta | Açıklama |
|---|---|
| `GET /api/v1/me/notebook/` | Liste. Filtreler: `status`, `favorites`, `media_type`, `rating_min/max`, `tag`, `genre`, `q` (başlık ve not içinde arama). `sort`: `-updated_at` (varsayılan), `-rating`, `-watched_on`, `-year`, `title` (ve artan sıralı karşılıkları). Sayfa başına 30 kayıt |
| `GET` / `PUT` / `PATCH` / `DELETE /api/v1/me/notebook/{media_type}/{tmdb_id}/` | Tek kayıt. `PUT`/`PATCH` kayıt yoksa oluşturur (`201`), varsa günceller (`200`) |
| `POST /api/v1/me/notebook/lookup/` | `{items: [{media_type, tmdb_id}, …]}` (en fazla 100) → sonuç kartlarında "İzledin ✓ · 4½★" göstermek için **tek sorguda** durum, favori ve puan |
| `GET /api/v1/me/notebook/stats/` | İzlenen film/dizi sayısı, toplam izleme süresi, ortalama puan, puan dağılımı, tür dağılımı, aylık/yıllık sayılar, en yüksek puanlı 10 yapım |
| `GET /api/v1/me/notebook/export/?format=csv\|json` | Dışa aktarma. CSV, Excel'in Türkçe karakterleri doğru açması için BOM ile başlar. Defter ayrıca `GET /api/v1/me/export/` çıktısında da yer alır |
| `POST /api/v1/me/notebook/merge/` | `{favorites: [...]}`: misafirken tarayıcıda tutulan favoriler girişten sonra hesaba aktarılır. Hesapta zaten kaydı olan yapımlara dokunulmaz (hesaptaki veri korunur) |

**Toplam izleme süresi:**
- **Film:** süre × (1 + yeniden izleme sayısı).
- **Dizi:** bölüm sayısı × bölüm süresi. TMDB dizilerde `episode_run_time` alanını artık boş döndürüyor (2026-10-09'da doğrulandı), bu yüzden son yayınlanan bölümün süresi kullanılır.

**"İzlediklerimi hariç tut":** `exclude_watched=true` parametresi aramada (`POST /api/v1/search/`), koleksiyon detayında ve Şans Globu'nun rastgele seçiminde çalışır. Yalnızca `watched` durumundaki yapımları eler; `want_to_watch` listede kalır. Bu parametreyle dönen koleksiyon yanıtları kişiye özel olduğu için `private, no-store` olarak işaretlenir ve CDN'de paylaşılmaz.

**6 ay kuralı:** Günlük iş, 30 günden eski anlık görüntüleri TMDB'den yeniler. 6 ayı aşan ve yenilenemeyen kayıtlarda TMDB kaynaklı alanlar (başlık, afiş, türler, süre) silinir; kullanıcının kendi verisi (durum, puan, not) korunur.

---

## ⏰ Hatırlatıcılar — Faz 7

| Uç nokta | Açıklama |
|---|---|
| `GET /api/v1/reminders/` | İptal edilmemiş hatırlatıcılarım (`due_date` dahil) |
| `POST /api/v1/reminders/` | `{media_type, tmdb_id, remind_on, channels}` → yeni kayıtta `201`; aynı yapım için ikinci istekte mevcut kayıt güncellenir (`200`). Hatalar: `already_released` (400), `no_upcoming_season` (400), `title_not_found` (404) |
| `POST /api/v1/reminders/bulk/` | `{items: [...]}`: misafirken tarayıcıda biriken "Hatırlat" tıklamaları girişten sonra bir kerede aktarılır (`created` / `skipped`) |
| `DELETE /api/v1/reminders/{id}/` | İptal. Başka bir kullanıcının kaydı için `404` döner |

**Günlük iş** (`/api/v1/cron/daily/`, Vercel Cron, her gün 05:00 UTC ≈ 08:00 İstanbul; elle çalıştırmak için `python backend/manage.py run_daily_jobs`):
1. Bekleyen hatırlatıcıların çıkış tarihini TMDB'den tazeler. Ertelenen yapım eski tarihte bildirilmez; tarih değiştiyse kullanıcıya kendi dilinde bildirim gider.
2. Zamanı gelenleri gönderir. Durum "bekliyor"dan "gönderildi"ye tek bir koşullu `UPDATE` ile geçer; cron iki kez çalışsa bile çift bildirim olmaz.
3. **Kanallar:**
   - uygulama içi bildirim;
   - e-posta: yalnızca bir e-posta sağlayıcısı tanımlıysa (`EMAIL_URL`) ve kullanıcı izin veriyorsa gider. Her e-postada abonelikten çıkma bağlantısı bulunur. E-posta kapalıyken "yalnızca e-posta" seçilmiş hatırlatıcılar uygulama içi bildirime düşer.
4. **Temizlik:**
   - 35 günden eski günlük sayaçlar,
   - 90 günden eski okunmuş bildirimler,
   - **6 aydan eski TMDB verisi** (TMDB şartı; ihtiyaç olunca yeniden çekilir).

Uç nokta `Authorization: Bearer <CRON_SECRET>` ister. Gizli anahtar tanımlı değilse veya yanlışsa `404` döner.

---

## 🛡️ Standart Hata Formatı

Tüm hata yanıtları (400, 401, 403, 404, 429, 500, 503) öngörülebilir ve tutarlı bir JSON formatında döner:

```json
{
  "error": {
    "code": "service_unavailable",
    "message": "Film veritabanı (TMDB) şu anda erişilemiyor. Lütfen kısa süre sonra tekrar deneyin.",
    "status_code": 503,
    "details": null
  }
}
```
