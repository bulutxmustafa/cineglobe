# 4. Ücretsiz Barındırma: Vercel Hobby + Neon Free

* **Durum:** Önerildi (Proposed). Barındırma denemesinin ([deploy-spike.md](../deploy-spike.md)) sonucu bekleniyor.
* **Tarih:** 2026-10-08
* **Karar Vericiler:** CineGlobe Ekibi
* **Değiştirdiği:** [ADR-0001](0001-tech-stack.md) §2 (Redis önbellek) ve §9 (DigitalOcean)

## Bağlam (Context)

Plan v1.8 bir **Sıfır Ödeme Politikası** getirdi: proje gelirsiz bir prototip, hiçbir servise kart eklenmeyecek. DigitalOcean'ın yönetilen PostgreSQL ve App Platform'u aylık ≈ $20 tutuyor. Bu yüzden ücretsiz seçenekler değerlendirildi. Kısıtlar:
- limit aşıldığında **fatura değil duraklama** olmalı,
- kart istenmemeli,
- Django + PostgreSQL çalışabilmeli.

## Karar (Decision)

* **Web + API:** Vercel Hobby. Vercel, `backend/manage.py` dosyasını otomatik algılar ve `WSGI_APPLICATION` üzerinden Django'yu tek bir Python fonksiyonu olarak çalıştırır. API projesinin kök dizini `backend/`; bağımlılıklar `backend/requirements.txt` dosyasından okunur. `ASGI_APPLICATION` ayarı kasıtlı olarak yok: Vercel ikisi birden varsa ASGI'yi seçiyor.
* **Veritabanı:** Neon Free. Bağlantı için Neon'un **pooled** adresi kullanılır, `DB_CONN_MAX_AGE=0`.
* **Redis yok:** Sunucusuz fonksiyonlar bellek paylaşmaz. Önbellek Django `DatabaseCache` ile, günlük kota ve bütçe sayaçları atomik `DailyCounter` tablosuyla veritabanında tutulur.
* **Statik dosyalar:** `STATIC_ROOT` tanımlı olduğu için Vercel derleme sırasında `collectstatic` çalıştırır ve dosyaları CDN'den sunar. Yerelde WhiteNoise kullanılır.
* **Soğuk başlangıç:** LLM SDK'ları ilk kullanımda yüklenir (`anthropic` ~2,4 sn, `google.genai` ~0,8 sn). Django'nun başlangıçtaki import süresi ~0,36 sn.
* **Proxy:** Vercel arkasında `TRUSTED_PROXY_COUNT=1`; istemci IP'si `X-Forwarded-For` başlığından okunur (hız sınırı ve misafir kotası için). `SECURE_PROXY_SSL_HEADER` tanımlı.
* **Taşınabilirlik:** `backend/Dockerfile` (gunicorn, prod ayarları) yedek plan için korunur: Render ücretsiz katmanı ya da Cloud Run (fatura hesabı ister, yalnızca kullanıcı onayıyla).

## Karar kapısı (spike)
- İlk istek (10+ dk boşta kaldıktan sonra) **≲ 5 sn** ve sıcak istek **≲ 800 ms** ise bu ADR "Kabul Edildi" olur.
- Değilse kullanıcıya rapor verilir ve yedek plan önerilir.

## Sonuçlar (Consequences)

### Olumlu
* Aylık $0; limit aşımı fatura değil duraklama demek.
* Git'e push edilince otomatik yayın, PR'lar için önizleme adresi.

### Olumsuz / Dikkat Edilmesi Gerekenler
* **Neon işlem kotası** (≈ 400 saat/ay): Önbellek de veritabanında olduğu için sürekli trafik kotayı ay ortasında bitirebilir. Önlem: herkese açık GET yanıtları Vercel CDN'inde önbelleğe alınır (`Cache-Control: s-maxage`) ve sayfalar prerender edilir (ayrıntı: [cost.md](../cost.md)).
* **Soğuk başlangıç:** Vercel fonksiyonu ve Neon uykudan birlikte uyanır. İlk istek birkaç saniye sürebilir; arayüzde yükleme durumu gösterilir.
* **Zamanlanmış işler:** Sürekli çalışan işçi yok. Günlük işler Vercel Cron veya GitHub Actions ile korumalı bir endpoint üzerinden tetiklenir.
* **Hobby yalnızca ticari olmayan kullanım içindir.** Bu, TMDB lisans kararımızla zaten uyumlu.
