# Web arayüzünü Vercel'e koyma (test ortamı)

İki ayrı Vercel projesi, aynı GitHub deposu. Hepsi ücretsiz (Hobby + Neon Free), kart gerekmez.

1. **API projesi**: [deploy-spike.md](deploy-spike.md) adımları (Neon + `backend` klasörü).
2. **Web projesi**: Vercel → *Add New → Project* → aynı depo, **Root Directory: `web`**, Framework: Nuxt (otomatik).
   Ortam değişkenleri (Build ve Runtime):
   | Değişken | Değer |
   |---|---|
   | `NUXT_API_ORIGIN` | API projesinin adresi, ör. `https://cineglob-api.vercel.app` (sonunda `/` olmasın) |
   | `NUXT_PUBLIC_SITE_URL` | web projesinin adresi, ör. `https://cineglob.vercel.app` |
3. API projesinde `CSRF_TRUSTED_ORIGINS` değerini web adresine ayarla (`https://cineglob.vercel.app`) ve yeniden dağıt.
4. Tarayıcı yalnızca web adresiyle konuşur; `/api/v1/*` istekleri sunucuda API'ye yönlendirilir. Böylece oturum çerezi aynı siteye ait olur.

Bilinen nokta: iki Vercel katmanı arka arkaya olduğu için API tarafında hız sınırı IP'si doğrulanmalı (test sırasında bakılacak).
