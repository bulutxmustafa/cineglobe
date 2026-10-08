# 1. Teknoloji Yığını ve Mimari Seçimleri

* **Durum:** Kabul Edildi (Accepted) — §7 (Flutter mobil istemci) [ADR-0002](0002-web-only.md) ile geçersiz kılındı
* **Tarih:** 2026-09-28
* **Karar Vericiler:** CineGlobe Ekibi & Antigravity Ajanı

## Bağlam (Context)

CineGlobe, kullanıcıların doğal dilde ne izlemek istediklerini yazabildikleri ("silahlı çatışma olsun ama istihbarat da olsun"), sistemin bunu anlayıp gerekçeleriyle birlikte film ve dizi önerdiği modern, premium bir keşif platformudur. Platformun web ve mobil istemcileri desteklemesi, güvenilir film/dizi verisine erişmesi ve doğal dil çıkarımlarını yüksek doğrulukla gerçekleştirmesi gerekmektedir.

## Karar (Decision)

Projenin katmanları için aşağıdaki teknoloji seçimleri yapılmıştır:

### 1. Backend: Django 5 + Django REST Framework (DRF)
* **Neden:** Olgun ve güvenli varsayılanlar, gelişmiş yetkilendirme ve admin paneli, PostgreSQL ile güçlü ORM/migration entegrasyonu, OpenAPI desteği (`drf-spectacular`).

### 2. Veritabanı: PostgreSQL 16
* **Neden:** Güçlü ilişkisel veri desteği, JSONB yetenekleri ve ileride anlamsal vektör araması (`pgvector`) için genişleme imkânı.

### 3. Film ve Dizi Verisi: TMDB API
* **Neden:** Kapsamlı film, dizi, oyuncu, tür ve anahtar kelime veri kümesi. (Not: Film ve dizi ID'leri çakışabileceği için sistemde `media_type + tmdb_id` bileşik anahtarı kullanılır). TMDB atıf kurallarına uyulacaktır.

### 4. Doğal Dil Anlama (NLU): Claude API (Anthropic)
* **Neden:** Kullanıcının serbest metin sorgusunu yapılandırılmış JSON formatında filtreye (türler, hariç tutulacaklar, anahtar kelimeler, ruh hali) dönüştürme ve "Neden önerildi?" gerekçelerini üretme yeteneği. Çıktılar backend'de Pydantic ile doğrulanır; hata durumunda deterministik fallback arama mekanizması devreye girer.

### 5. Web Frontend: Vue 3 + Vite + TypeScript + Pinia + Tailwind CSS
* **Neden:** Hızlı geliştirme döngüsü, reaktif ve performanslı bileşen mimarisi, tutarlı tip güvenliği ve tasarım tokenları ile premium/sinematik koyu tema desteği.

### 6. 3D & Animasyon: GSAP + three.js / globe.gl
* **Neden:** "Şans Globu" özelliği için etkileşimli, akıcı 3D dünya küresi animasyonları ve premium mikro etkileşimler.

### 7. Mobil İstemci: Flutter (iOS + Android)
* **Neden:** Tek kod tabanı ile hem iOS hem Android'e yüksek performanslı, zengin animasyonlu native derleme imkânı.

### 8. Cache Katmanı: Redis
* **Neden:** TMDB ve LLM çağrılarını önbelleğe alarak API yanıt sürelerini düşürmek (hedef: cache hit < 300ms) ve harici API maliyetlerini azaltmak.

### 9. CI/CD & Deploy: GitHub Actions & DigitalOcean
* **Neden:** Otomatik lint/test akışları (`ci-backend`, `ci-web`, `ci-mobile`) ve maliyet/performans dengeli DigitalOcean App Platform / Managed PostgreSQL altyapısı.

## Sonuçlar (Consequences)

### Olumlu
* Modüler, iyi tanımlanmış API sözleşmeleri (OpenAPI / Swagger).
* LLM hatalarına karşı Pydantic doğrulaması ve güvenli fallback garantisi.
* Çoklu platform (Web + Mobil) desteği için ortak backend.
* Önbellekleme sayesinde düşük gecikme ve maliyet kontrolü.

### Dikkat Edilmesi Gerekenler
* Film ve dizi türlerinin TMDB ID karşılıkları farklı olduğu için `GenreMapper` servisi zorunludur.
* Film ve dizi `tmdb_id` değerleri çakışabileceği için tüm modeller ve cache anahtarları `(media_type, tmdb_id)` ikilisiyle çalışmalıdır.
* Harici API anahtarları `.env` dosyasında tutulmalı, repoya asla sızdırılmamalıdır.
