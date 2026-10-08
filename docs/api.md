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
1. **QueryParser:** `ANTHROPIC_API_KEY` tanımlıysa Claude (`ANTHROPIC_MODEL`, varsayılan `claude-opus-5-5`) sorguyu structured outputs ile `SearchFilters` şemasına çevirir. Kullanıcı metni `<user_query>` etiketleri içinde **veri** olarak gönderilir; çıktı yalnızca şemaya uyabilir (prompt injection davranışı değiştiremez).
2. **Fallback:** Anahtar yoksa ya da LLM hata/zaman aşımı/geçersiz JSON/ret döndürürse kural tabanlı TR/EN ayrıştırıcı devreye girer. Arama LLM yüzünden asla 500 vermez. Yanıttaki `parser` alanı hangisinin kullanıldığını gösterir.
3. **Retriever:** Filtreler film ve dizi için ayrı TMDB `discover` parametrelerine çevrilir (tür ID'leri farklı). `both` ise iki sorgu paralel atılır. Anahtar kelime eşleşmesi çok dar kalırsa (< 5 sonuç) anahtar kelimesiz ikinci sorguyla tamamlanır.
4. **Ranker:** Bayes ortalamalı puan (film için 1000, dizi için 300 oy güven eşiği) + anahtar kelime/tür uyumu bonusu. `genres_exclude` kesin elemedir. Tekilleştirme `(media_type, tmdb_id)` ile yapılır; aynı ID'li film ve dizi birbirini silmez.
5. **Explainer:** Tüm sonuçlar için tek LLM çağrısıyla, spoiler içermeyen gerekçeler üretilir. LLM yoksa tür ve puandan oluşan şablon cümle kullanılır.

#### Başarılı Yanıt (HTTP 200 OK)
```json
{
  "query": "kısa bölümlü, hafif, komik bir dizi",
  "lang": "tr",
  "media_type": "tv",
  "parser": "llm",
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
| 400 | `invalid_query` | Boş, 2 karakterden kısa, harf içermeyen ya da izleme tercihi içermeyen sorgu (mesajda örnek sorgu önerilir) |
| 400 | `invalid` | Eksik `query` alanı veya geçersiz `media_type`/`lang` |
| 429 | `throttled` | Rate limit aşıldı |
| 503 | `service_unavailable` | TMDB erişilemiyor veya `TMDB_API_KEY` tanımlı değil |

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
