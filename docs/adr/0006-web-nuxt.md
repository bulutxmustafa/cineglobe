# ADR-0006: Web arayüzü için Nuxt 4 (hibrit render)

- Durum: Kabul edildi (2026-10-09)

## Bağlam
Kullanıcıların çoğu arama motorundan gelecek ("film önerileri", "ne izlesem"). Koleksiyon, oyuncu, detay, yakında çıkacaklar ve ana sayfa HTML olarak sunulmalı. Öte yandan Vercel Hobby'de aylık 1 milyon fonksiyon çağrısı ve 4 saat aktif işlemci var; her istek sunucuda render edilirse kota erken biter.

## Seçenekler
1. **Vite + vite-ssg**: yalnızca derleme anında bilinen rotaları üretir. Binlerce film/oyuncu detay sayfası için uygun değil (hepsi önceden üretilemez).
2. **Nuxt 4 + rota bazlı render kuralları**: ana sayfa ve listeler önceden üretilir/yenilenir, detay sayfaları ilk istekte render edilip CDN'de saklanır (`swr`/ISR), arama ve hesap sayfaları yalnızca istemcide çalışır.

## Karar
**Nuxt 4** (Vue 3 + TypeScript) + `@nuxtjs/i18n` (TR/EN, `/tr` `/en` önekleri, otomatik `hreflang`/canonical) + `@nuxtjs/tailwindcss`.
- `/` ve `/collections`, `/upcoming`: `swr` ile 30 dk – 1 saat CDN önbelleği.
- `/title/**`, `/person/**`: `swr` 24 saat; ilk ziyaretçi sayfayı üretir, sonrakiler CDN'den alır.
- `/search`, `/account/**`, `/s/**`: `ssr: false`, `noindex`.
- API çağrılarında her zaman `lang` parametresi açıkça gönderilir; böylece Django yanıtı da CDN'de önbelleklenebilir (bkz. `cdn_cache`).

## Sonuçlar
- Arama motoru ve JS kapalıyken içerik HTML'de bulunur.
- Kota: popüler sayfalar CDN'den döner; render yalnızca önbellek süresi dolduğunda çalışır.
- Tasarım yönü (kullanıcı isteğiyle plan v1.8'den sapma): koyu sinematik tema yerine **açık, sade, editoryal** bir site. Sıcak kâğıt zemin, koyu mürekkep metin, tek vurgu rengi, küçük köşe yarıçapı, cam efekti/degrade yok.
