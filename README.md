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
- 🔓 **Giriş isteğe bağlı:** Hesap açmadan arayabilir, keşfedebilir, Şans Globu'nu kullanabilirsiniz
- 📓 **Film Defterim (üyelere):** İzlediklerinizi işaretleyin, puan verin, özel notlar yazın, kendi istatistiklerinizi görün
- ❤️ **Favoriler & izleme listesi**
- 🌐 **Yalnızca web** (telefon ve tablet tarayıcılarında tam uyumlu; native mobil uygulama yok)

> Faz planı ve ayrıntılar için bkz. [`CINEGLOBE_PLAN.md`](CINEGLOBE_PLAN.md) (v1.3).

---

## 🏗️ Mimari & Teknoloji Yığını

- **Backend:** Python 3.10+, Django 5, Django REST Framework, drf-spectacular (OpenAPI/Swagger)
- **Veritabanı:** PostgreSQL 16 (İlişkisel veri + `(media_type, tmdb_id)` tekil anahtar yapısı)
- **Önbellek (Cache):** Redis 7
- **Doğal Dil Anlama (NLU):** Claude API (Anthropic) + Pydantic veri doğrulama
- **Veri Kaynağı:** TMDB API (Film & Dizi verileri)
- **Web Frontend:** Vue 3, Vite, TypeScript, Pinia, Tailwind CSS, GSAP, three.js / globe.gl (arama motoru dostu olması için SSR/prerender — Nuxt 3 veya Vite SSG, ADR ile seçilir)
- **Gelir:** Reklam (onay yönetimli), affiliate bağlantılar, opsiyonel Premium — TMDB ticari lisansı alınmadan açılmaz
- **Konteynerizasyon & Dağıtım:** Docker, Docker Compose, GitHub Actions, DigitalOcean

---

## 📁 Proje Klasör Yapısı

```text
cineglobe/
├── backend/            # Django REST API
│   ├── apps/           # Django uygulamaları (catalog, search, people, collections, upcoming, reminders, notebook, monetization, accounts)
│   ├── config/         # Django ayarları (base, dev, prod)
│   ├── requirements/   # Bağımlılıklar (base.txt, dev.txt, prod.txt)
│   ├── tests/          # pytest test paketi
│   └── Dockerfile      # Multi-stage Docker yapısı
├── web/                # Vue 3 Web Frontend (tek istemci)
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
- **Doğal Dil Arama:** `POST http://localhost:8000/api/v1/search/` — gövde: `{"query": "gerilim olsun ama korku içermesin", "media_type": "both", "lang": "tr"}` *(Faz 3; `ANTHROPIC_API_KEY` yoksa kural tabanlı ayrıştırıcıyla çalışır)*
- **Koleksiyonlar:** `http://localhost:8000/api/v1/collections/{slug}/?lang=tr` *(Faz 4B)*
- **Oyuncu Filmografisi:** `http://localhost:8000/api/v1/people/{tmdb_id}/filmography/?sort=newest|oldest&lang=en` *(Faz 4)*
- **Yakında Çıkacaklar:** `http://localhost:8000/api/v1/upcoming/?media_type=both&lang=tr` *(Faz 4C)*
- **Film Defterim (giriş gerekir):** `http://localhost:8000/api/v1/me/notebook/?status=watched&sort=-rating` *(Faz 7B)*
- **Defter İstatistikleri (giriş gerekir):** `http://localhost:8000/api/v1/me/notebook/stats/` *(Faz 7B)*
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

> **Önemli Lisans Notu:** TMDB ücretsiz API kullanımı ticari olmayan projeler içindir ve platform arayüzünde (footer / Hakkında bölümünde) **TMDB logosu ve atıf metni zorunludur**. TMDB, ana amacı gelir elde etmek olan projeleri ticari sayar; **reklam, affiliate veya Premium açılmadan önce TMDB'den ticari lisans/yazılı onay alınmalıdır** (bkz. `CINEGLOBE_PLAN.md` §2 ve Faz 10).
