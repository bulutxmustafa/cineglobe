# 🎬 CineGlobe — Film & Dizi Keşif Platformu

CineGlobe, kullanıcıların doğal dille ne izlemek istediklerini ifade edebildikleri ("Silahlı çatışma var ama istihbarat da işin içinde olsun"), yapay zekanın (Claude) bu istekleri anlayıp gerekçeleriyle birlikte zengin film ve dizi önerileri sunduğu modern bir keşif platformudur.

---

## ✨ Özellikler

- 🔎 **Doğal dille arama:** "Silahlı çatışma olsun ama istihbarat da olsun" gibi cümlelerle film ve dizi bulma
- 🌍 **Türkçe / English:** Arayüz, içerik ve öneri gerekçeleri seçilen dilde
- 🗂️ **Hazır koleksiyonlar:** Sıkılmam Diyeceğiniz Filmler, Sürükleyici, Çerezlik, Kafanızı Dağıtacak, Başladığı Gibi Bitecek, Tersköşe ve daha fazlası
- 🎭 **Oyuncu sayfaları:** En iyi yapımlar + tam filmografi (kronolojik veya en güncelden başlayarak)
- 📅 **Yakında çıkacaklar:** Yaklaşan film/diziler ve **hatırlatıcı** (uygulama içi, e-posta, push)
- 🌐 **Şans Globu:** Butona bas, dünya dönsün, sürpriz bir film/dizi çıksın (favorilerden veya bir koleksiyondan)
- ❤️ **Favoriler & izleme listesi**
- 📱 **Web (Vue) + Mobil (Flutter)**

> Faz planı ve ayrıntılar için bkz. [`CINEGLOBE_PLAN.md`](CINEGLOBE_PLAN.md) (v1.2).

---

## 🏗️ Mimari & Teknoloji Yığını

- **Backend:** Python 3.10+, Django 5, Django REST Framework, drf-spectacular (OpenAPI/Swagger)
- **Veritabanı:** PostgreSQL 16 (İlişkisel veri + `(media_type, tmdb_id)` tekil anahtar yapısı)
- **Önbellek (Cache):** Redis 7
- **Doğal Dil Anlama (NLU):** Claude API (Anthropic) + Pydantic veri doğrulama
- **Veri Kaynağı:** TMDB API (Film & Dizi verileri)
- **Web Frontend:** Vue 3, Vite, TypeScript, Pinia, Tailwind CSS, GSAP, three.js / globe.gl
- **Mobil Uygulama:** Flutter (iOS & Android)
- **Konteynerizasyon & Dağıtım:** Docker, Docker Compose, GitHub Actions, DigitalOcean

---

## 📁 Proje Klasör Yapısı

```text
cineglobe/
├── backend/            # Django REST API
│   ├── apps/           # Django uygulamaları (catalog, search, people, collections, upcoming, reminders, accounts)
│   ├── config/         # Django ayarları (base, dev, prod)
│   ├── requirements/   # Bağımlılıklar (base.txt, dev.txt, prod.txt)
│   ├── tests/          # pytest test paketi
│   └── Dockerfile      # Multi-stage Docker yapısı
├── web/                # Vue 3 Web Frontend
├── mobile/             # Flutter Mobil Uygulama
├── docs/               # Mimari ve Tasarım Belgeleri
│   └── adr/            # Mimari Karar Kayıtları (ADR)
├── .github/            # GitHub Actions CI/CD ve PR şablonu
│   └── workflows/
├── docker-compose.yml  # PostgreSQL, Redis ve Backend servisleri
├── .env.example        # Çevre değişkenleri örnek şablonu
├── CINEGLOBE_PLAN.md   # Ana geliştirme planı
└── README.md
```

---

## 🚀 Hızlı Başlangıç (Lokal Geliştirme)

### 1. Depoyu Klonlama ve Çevre Değişkenleri
```bash
git clone https://github.com/bulutxmustafa/cineglobe.git
cd cineglobe

# Örnek çevre değişkenlerini kopyalayın
cp .env.example .env
```

### 2. Docker Servislerini Başlatma
PostgreSQL ve Redis servislerini Docker ile ayağa kaldırın:
```bash
docker compose up -d postgres redis
```

Servis durumunu kontrol edin:
```bash
docker compose ps
```

### 3. Backend Ortamı Kurulumu & Çalıştırma
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r backend/requirements/dev.txt

# Veritabanı tablolarını oluşturun
python backend/manage.py migrate

# Backend geliştirme sunucusunu başlatın
python backend/manage.py runserver
```

### 4. API & Dokümantasyon Erişimi
Sunucu çalıştıktan sonra:
- **Sağlık Kontrolü:** [http://localhost:8000/api/v1/health/](http://localhost:8000/api/v1/health/)
- **Film/Dizi Detayı:** `http://localhost:8000/api/v1/titles/{media_type}/{tmdb_id}/?lang=tr`
- **Koleksiyonlar:** `http://localhost:8000/api/v1/collections/{slug}/?lang=tr` *(Faz 4B)*
- **Oyuncu Filmografisi:** `http://localhost:8000/api/v1/people/{tmdb_id}/filmography/?sort=newest|oldest&lang=en` *(Faz 4)*
- **Yakında Çıkacaklar:** `http://localhost:8000/api/v1/upcoming/?media_type=both&lang=tr` *(Faz 4C)*
- **Swagger UI:** [http://localhost:8000/api/schema/swagger-ui/](http://localhost:8000/api/schema/swagger-ui/)
- **ReDoc:** [http://localhost:8000/api/schema/redoc/](http://localhost:8000/api/schema/redoc/)

### 5. Test Paketi & Kapsam
```bash
# Birim ve entegrasyon testlerini çalıştırın
pytest

# Test kapsam raporu ile birlikte çalıştırın
pytest --cov=backend --cov-report=term-missing
```

### 6. Kod Standartları ve Pre-commit
```bash
pre-commit install
pre-commit run --all-files
```

---

## 🌿 Git & Branch Stratejisi

- `main`: Üretime hazır, korumalı ana dal.
- `develop`: Entegrasyon dalı.
- `feature/<faz>-<kısa-ad>`: Özellik geliştirme dalları (örn. `feature/p0-init-setup`).
- Commit formatı: [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `test:`, `docs:`, `chore:`, `refactor:`, `ci:`).

---

## 📄 Lisans & Atıf (TMDB Attribution)

Bu ürün film ve dizi verilerini sağlamak için TMDB API'sini kullanır ancak TMDB tarafından onaylanmamış veya sertifikalandırılmamıştır.

> **Önemli Lisans Notu:** TMDB ücretsiz API kullanımı ticari olmayan projeler içindir ve platform arayüzünde (özellikle web ve mobil footer alanlarında) **TMDB logosu ve atıf metni zorunludur**. Projenin ileride ticari gelir modeli içermesi durumunda TMDB ticari lisansı edinilmelidir.
