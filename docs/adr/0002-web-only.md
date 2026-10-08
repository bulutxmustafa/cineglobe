# 2. Yalnızca Web İstemcisi (Flutter Mobil Uygulamadan Vazgeçilmesi)

* **Durum:** Kabul Edildi (Accepted)
* **Tarih:** 2026-10-08
* **Karar Vericiler:** CineGlobe Ekibi
* **Geçersiz kıldığı:** [ADR-0001](0001-tech-stack.md) §7 "Mobil İstemci: Flutter (iOS + Android)"

## Bağlam (Context)

ADR-0001, Vue 3 web istemcisine ek olarak Flutter ile native iOS/Android uygulaması öngörüyordu. Plan v1.3 ile ürün önceliği değişti: tek kişilik ekip, sıfıra yakın işletme maliyeti hedefi ve organik (arama motoru) trafiği önemseyen bir model. İki ayrı istemciyi geliştirmek, test etmek ve mağazalarda yayınlamak (Apple Developer hesabı ücretlidir; mağaza inceleme süreçleri, gizlilik beyanları) bu hedeflerle çelişiyor. Repoda mobil tarafta yalnızca boş bir iskelet (`mobile/analysis_options.yaml`) ve bir CI iş akışı vardı; kod yazılmamıştı.

## Karar (Decision)

* CineGlobe v1 **yalnızca web** olarak geliştirilir: Vue 3 tabanlı tek istemci, telefon ve tablet tarayıcılarında birinci sınıf (responsive, dokunma hedefleri ≥ 44px).
* `mobile/` klasörü, `.github/workflows/ci-mobile.yml` ve `.gitignore` içindeki Flutter girdileri kaldırılır.
* Mobil push bildirimleri (FCM/APNs) kapsamdan çıkar; hatırlatıcı kanalları uygulama içi bildirim, e-posta ve opsiyonel web push'tur.
* Ana ekrana eklenebilir web uygulaması (PWA) v2 fikir havuzunda değerlendirilir.

## Sonuçlar (Consequences)

### Olumlu
* Tek kod tabanı ve tek CI hattı: daha hızlı geliştirme, daha az bakım.
* Mağaza ücreti, inceleme süreci ve platforma özel gizlilik beyanları yok.
* SSR/prerender ile tüm içerik sayfaları arama motorlarına açık olur (v1.3 §2).

### Olumsuz / Dikkat Edilmesi Gerekenler
* Native bildirim ve çevrimdışı deneyim yok; mobil kullanıcı deneyimi tamamen tarayıcı performansına bağlı. Şans Globu (three.js) için düşük güçlü cihaz ayarları (Faz 6) daha da önemli hâle gelir.
* İleride native uygulama istenirse backend API'si (`/api/v1/...`) zaten istemciden bağımsızdır; yeni bir ADR ile yeniden değerlendirilebilir.
