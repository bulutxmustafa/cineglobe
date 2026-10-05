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
