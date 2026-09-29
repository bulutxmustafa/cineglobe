# CineGlobe API v1 Dokümantasyonu

Bu belge, CineGlobe Backend API endpoint'lerinin teknik detaylarını ve şemalarını içerir.

## 📌 İnteraktif Dokümantasyon Arayüzleri

Backend sunucusu çalışırken aşağıdaki arayüzlerden API şemasına ve test panellerine erişilebilir:
- **Swagger UI:** `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc:** `http://localhost:8000/api/schema/redoc/`
- **OpenAPI 3.0 Şeması (JSON/YAML):** `http://localhost:8000/api/schema/`

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

## 🛡️ Standart Hata Formatı

Tüm hata yanıtları (400, 401, 403, 404, 429, 500) öngörülebilir ve tutarlı bir JSON formatında döner:

```json
{
  "error": {
    "code": "validation_error",
    "message": "İstek parametreleri geçersiz.",
    "status_code": 400,
    "details": {
      "query": ["Bu alan zorunludur."]
    }
  }
}
```
