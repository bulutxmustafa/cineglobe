# Maliyet Modeli & LLM Maliyet Koruması

Plan §3.10 ve v1.8 (Sıfır Ödeme Politikası) uygulama notları. Amaç: hiçbir servise para ödemeden yayında kalmak, AI çalışmasa bile siteyi açık tutmak.

## Altyapı: aylık $0 (Sıfır Ödeme Politikası, plan v1.8)

Hiçbir servise kart eklenmez. Aşağıdaki tüm limitler 2026-10-08'de resmi sayfalardan doğrulandı. **Hiçbirinde limit aşımı fatura çıkarmaz**; ilgili özellik duraklar.

| Servis | Ücretsiz limit | Limit dolunca | Kaynak |
|---|---|---|---|
| **Vercel Hobby** (web + Django fonksiyonu) | Aylık 1.000.000 fonksiyon çağrısı, 4 saat aktif CPU, 360 GB-saat bellek, 100 GB veri aktarımı, 1.000.000 CDN isteği; fonksiyon süresi en fazla 300 sn (biz 30 sn ile sınırlıyoruz) | Özellik 30 gün duraklar; **fatura yok**. Yalnızca ticari olmayan kişisel kullanım | [vercel.com/docs/plans/hobby](https://vercel.com/docs/plans/hobby) |
| **Neon Free** (PostgreSQL) | Proje başına 1 GB depolama, aylık 100 CU-saat (0,25 CU ile ≈ 400 saat), 5 GB veri aktarımı; 5 dk boşta kalınca uyur; 6 saatlik geri yükleme geçmişi + 1 elle anlık görüntü | CU-saat bitince işlem **ay sonuna kadar askıya alınır**; depolama dolunca yazma işlemleri başarısız olur. Veri silinmez, **fatura yok** | [neon.com/docs/introduction/plans](https://neon.com/docs/introduction/plans) |
| **Gemini** (ücretsiz katman) | Dakikada 15 istek (ölçüldü); günlük sınır AI Studio'da | 429 → devre kesici → klasik arama | [ai.dev/rate-limit](https://ai.dev/rate-limit) |
| **GitHub Actions** | Herkese açık depoda standart çalıştırıcılar ücretsiz | Ödeme yöntemi yoksa kullanım engellenir, **fatura yok** | [docs.github.com](https://docs.github.com/en/billing/concepts/product-billing/github-actions) |
| **TMDB API** | Ticari olmayan kullanım ücretsiz | — | [themoviedb.org/api-terms-of-use](https://www.themoviedb.org/api-terms-of-use) |

### ⚠️ Bilinen risk: Neon işlem kotası
Önbellek, kota ve bütçe sayaçları veritabanında tutulduğu için **her API isteği veritabanını uyandırır**. Neon 5 dk boşta kalınca uyur. Ancak trafik sürekli olursa 0,25 CU'luk veritabanı ayda 744 saat çalışır, ücretsiz kota ise ≈ 400 saat. Bu durumda kota **ayın ortasında biter** ve veritabanı ay sonuna kadar askıda kalır.

**Önlemler:**
1. Herkese açık GET yanıtlarına `Cache-Control: s-maxage` eklenir (yayın fazında). Tekrar eden istekleri Vercel CDN'i karşılar; bu istekler Django'ya ve veritabanına hiç ulaşmaz.
2. Web arayüzünün sayfaları mümkün olduğunca prerender edilir (Faz 5).
3. Neon panelinde CU-saat kullanımı haftalık kontrol edilir; %80'de önlem alınır (bkz. plan Faz 9 "limit izleme").

### Önbellek
Django `DatabaseCache` (`django_cache` tablosu; `migrate` sırasında otomatik oluşturulur). En fazla `CACHE_MAX_ENTRIES`=5000 kayıt tutulur. Kayıt başına ≈ 20 KB ile ≈ 100 MB eder; 1 GB'lık Neon sınırının epey altında. Doluluğa yaklaşınca Django eski kayıtların bir kısmını kendisi siler.

## Hangi çağrı para harcar?

| Kaynak | Maliyet | Not |
|---|---|---|
| TMDB API | $0 | Ticari olmayan kullanım (plan §2). Discover sonuçları 1 saat önbellekte. |
| Gemini Flash-Lite, **ücretsiz katman** (varsayılan) | $0 | Hız/günlük sınırlı, SLA yok. **İstekler Google tarafından ürün geliştirmede kullanılabilir.** Bu yüzden LLM'e yalnızca sorgu metni ve herkese açık film bilgisi gider. |
| Gemini Flash-Lite, ücretli katman | giriş $0,30 / çıkış $2,50 (1M token) | Yalnızca `GEMINI_FREE_TIER=False` ise maliyet hesaplanır. |
| Claude Haiku 5.5 (yedek/yükseltme) | giriş $0,10 / çıkış $0,50 (1M token) | `LLM_PROVIDER_CHAIN=anthropic,classic` ile açılır. API faturası claude.ai aboneliğinden ayrıdır. |
| Klasik arama (`classic`) | $0 | Kural tabanlı, ağ çağrısı yok. Zincirin her zaman son halkası. |

Fiyatlar 2026-10-08'de resmi sayfalardan alındı ([Gemini](https://ai.google.dev/gemini-api/docs/pricing), Claude fiyatları Anthropic dokümanından) ve [`cost_guard.py`](../backend/apps/search/cost_guard.py) içindeki `PRICES_PER_MTOK` tablosunda tutuluyor. Fiyat değişirse yalnızca bu tablo güncellenir. Tabloda olmayan bir model $0 sayılır ve raporda öyle görünür; bu sayede maliyet sessizce şişirilmez.

**Gemini ücretsiz katman sınırları:** Google, sınırları proje bazında [AI Studio](https://ai.dev/rate-limit) üzerinde gösteriyor.
- **Ölçüldü (2026-10-08):** `gemini-3.5-flash-lite` için **dakikada 15 istek** (proje + model başına; `GenerateRequestsPerMinutePerProjectPerModel-FreeTier`). Sınır aşılınca API 429 döner. Devre kesici sağlayıcıyı 60 sn atlar ve o aramalar klasik aramayla yanıtlanır.
- **Günlük sınır (RPD):** henüz bilinmiyor. [ai.dev/rate-limit](https://ai.dev/rate-limit) sayfasından okunup buraya yazılmalı.

Bir AI araması 1 ayrıştırma çağrısı ve (ilk `LLM_EXPLAIN_TOP_N` sonuç için) 1 açıklama çağrısı demek, yani **2 istek**. Dakikada 15 istekle bu, **tüm kullanıcılar için toplamda dakikada ~7 AI araması** eder. `LLM_EXPLAIN_TOP_N=0` yapılırsa (gerekçeler şablonla) kapasite **~15 AI araması/dk**'ya çıkar. Önbellekten dönen aramalar bu sınırı hiç tüketmez. `GUEST_DAILY_AI_SEARCHES` ve `USER_DAILY_AI_SEARCHES` değerleri, günlük sınır öğrenildiğinde ona göre ayarlanmalı.

**Kalite kapısı çalıştırılırken** `run_llm_eval` istekleri varsayılan olarak dakikada 12 ile sınırlar (`--rpm`). Aksi halde ücretsiz katman 429 döner ve rapor modelin kalitesini değil hız sınırını ölçer (ilk denemede tam olarak bu oldu).

## Arama başına maliyet

**Ölçüldü (2026-10-08, 2 canlı arama, küçük örnek):** önbelleğe takılmayan bir arama ≈ ayrıştırma (~670 giriş + ~155 çıkış token) + 3 sonuç için açıklama (~640 giriş + ~180 çıkış token). Önbellekli arama 0 token. Uçtan uca süre önbelleksiz ~3 sn, önbellekli ~0 ms.

| Sağlayıcı | 1 arama | 10.000 arama/ay |
|---|---:|---:|
| Gemini ücretsiz katman | $0 | $0 |
| Claude Haiku 5.5 | ≈ $0,0003 | ≈ $3 |

Daha uzun ve karmaşık sorgular daha fazla token kullanır. Gerçek ortalama, canlıya çıkıştan sonra admin panelindeki toplamlardan buraya işlenecek.

## Koruma merdiveni (uygulandı)

1. **Önbellek:** Sorgu büyük/küçük harf, noktalama ve boşluktan bağımsız normalize edilir. Anahtar `sorgu + media_type + lang` (1 saat). Önbellekten dönen arama LLM çağırmaz ve kota tüketmez.
2. **Ucuz model:** Varsayılan Gemini ücretsiz katman. Model kimlikleri `.env`'den (`GEMINI_MODEL`, `ANTHROPIC_MODEL_PARSER/EXPLAIN`) okunur.
3. **Açıklamayı ucuzlatma:** Her sonuç LLM'siz şablon gerekçe alır. LLM gerekçesi yalnızca ilk `LLM_EXPLAIN_TOP_N` (varsayılan 3) sonuç için, tek toplu çağrıyla üretilir. `0` yapılırsa hiç çağrılmaz.
4. **Kota:** Misafir `GUEST_DAILY_AI_SEARCHES` (IP SHA-256 ile özetlenir, ham IP saklanmaz), üye `USER_DAILY_AI_SEARCHES`. Gece yarısı (Europe/Istanbul) sıfırlanır. Ayrıca dakikada 20 istek hız sınırı var.
5. **Günlük bütçe tavanı** (`LLM_DAILY_BUDGET_USD`, yalnızca ücretli sağlayıcılar): Her çağrının maliyeti veritabanındaki `DailyCounter` tablosuna (tek bir atomik `UPDATE` ile) eklenir. Tavan dolunca ücretli sağlayıcılar atlanır. Ücretsiz Gemini etkilenmez.
6. **Yedek:** Hata, 429, zaman aşımı, kota ya da bütçe → klasik arama. Kullanıcı her zaman 200 ve sonuç alır. Yanıttaki `ai_status` (`ok` | `quota_exceeded` | `budget_exceeded` | `fallback`) arayüze nedenini söyler.
7. **Devre kesici:** 429/zaman aşımı/5xx/yetki hatası veren sağlayıcı `LLM_CIRCUIT_BREAKER_SECONDS` (60 sn) boyunca denenmez. Geçersiz JSON bir kez yeniden denenir.
8. **Uzunluk sınırları:** Sorgu ≤ 300 karakter. `max_tokens`: ayrıştırma 1024 (Gemini) / 2048 (Haiku), açıklama 2048 / 4096.

**Henüz yapılmadı:** Bot koruması (CAPTCHA/Turnstile) Faz 8'de, kullanıcıyla netleştirilerek. Gecelik toplu işler için Batch API, koleksiyon doğrulaması (Faz 4B) yazılınca.

## İzleme

- **Django admin → Search → LLM usage logs:** Bugün ve bu ay için çağrı, başarısız çağrı, token ve USD toplamları, ayrıca günlük bütçe durumu. Her satırda sağlayıcı, model, çağrı türü, sonuç, token ve maliyet var. **Sorgu metni, kullanıcı ve IP kaydedilmez.**
- Günlük sayaçlar `DailyCounter` tablosunda (`key` + `day`; gün İstanbul saatine göre): `llm:spend_micro_usd`, `llm:quota:<kimlik>`. Kota artırma işlemi kontrol ve artırmayı tek bir `UPDATE` ile yaptığı için aynı anda çalışan iki sunucusuz fonksiyon kotayı aşamaz.
- Misafir kimliği: Vercel'de istemci IP'si `X-Forwarded-For` başlığından okunur (`TRUSTED_PROXY_COUNT=1`). Yerelde bu başlığa güvenilmez (`0`), böylece sahte başlıkla kota atlatılamaz.
