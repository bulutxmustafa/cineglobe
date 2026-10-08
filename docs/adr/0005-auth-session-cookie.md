# 5. Kimlik Doğrulama: Oturum Çerezi + CSRF (JWT değil)

* **Durum:** Kabul Edildi (Accepted)
* **Tarih:** 2026-10-09
* **Karar Vericiler:** CineGlobe Ekibi

## Bağlam (Context)
Plan Faz 7 iki seçenek sunuyor:
- JWT (kısa ömürlü access + refresh),
- güvenli çerez tabanlı oturum.

Ayrıca hesap **isteğe bağlı**: keşif özelliklerinin tamamı misafire açık. Web arayüzü SSR/prerender kullanacak (Faz 5) ve API ile aynı alan adından sunulacak: Vercel'de `/api/*` istekleri Django'ya yönlendiriliyor (ADR-0004).

## Karar (Decision)
* **Django oturumu + HttpOnly çerez** (`SameSite=Lax`, üretimde `Secure`), 30 gün geçerli. Oturum kayıtları veritabanında; çıkış yapınca sunucu tarafında geçersiz olur.
* **CSRF:** DRF `SessionAuthentication` CSRF'i yalnızca giriş yapmış kullanıcılar için denetler. **Kayıt, giriş ve şifre sıfırlama** uçlarında CSRF ayrıca zorunlu tutulur; aksi halde "login CSRF" saldırısıyla ziyaretçi saldırganın hesabına sokulabilir. Arayüz önce `GET /api/v1/auth/csrf/` çağırır, `csrftoken` çerezini okur ve değeri `X-CSRFToken` başlığıyla gönderir.
* **Giriş e-postayla yapılır** (özel `accounts.User`; e-posta büyük/küçük harf duyarsız tekil). Şifreler **Argon2** ile özetlenir.
* **Kaba kuvvet koruması:** kayıt, giriş ve şifre sıfırlama uçları dakikada 10 istekle sınırlı.
* **Hesap avlamaya karşı:** yanlış şifre ile kayıtlı olmayan e-posta aynı yanıtı alır; şifre sıfırlama her zaman 200 döner.
* **Herkese açık uçlar** (koleksiyonlar, yakında çıkacaklar) kimlik doğrulama yapmaz. Bu, CDN önbelleği için gerekli: yanıta `Vary: Cookie` eklenmez.

## Neden JWT değil?
* Token'ı JavaScript'in erişebildiği bir yerde saklamak gerekirdi (XSS riski). HttpOnly çerez bu riski kaldırır.
* Refresh token döngüsü, iptal listesi ve ek kütüphane gerektirmez.
* Arayüz ve API aynı alan adında olduğu için çerez doğal olarak çalışır.
* Mobil uygulama kapsam dışı (ADR-0002); tarayıcı dışı istemci yok.

## Sonuçlar (Consequences)
* Arayüz ile API **aynı alan adında** olmalı (Vercel yönlendirmesi). Farklı alan adı gerekirse `SameSite=None` ve CORS ile kimlik bilgisi gönderimi ayrıca değerlendirilir.
* "Google ile giriş" (opsiyonel) yapılmadı; ileride `django-allauth` ile eklenebilir.
* E-posta gönderimi (şifre sıfırlama, hatırlatıcı e-postaları), ücretsiz bir sağlayıcı kullanıcı tarafından seçilene kadar kapalı. Yerelde e-postalar konsola yazılıyor. Bu durumda hatırlatıcılar uygulama içi bildirimle gider.
