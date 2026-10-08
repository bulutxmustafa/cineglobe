# Maliyet Modeli & LLM Maliyet Koruması

Plan §3.10'un uygulama notları. Amaç: ürün ücretsiz kalırken AI aramasının faturası kontrolden çıkmasın ve AI çalışmasa bile site açık kalsın.

## Hangi çağrı para harcar?

| Kaynak | Maliyet | Not |
|---|---|---|
| TMDB API | $0 | Ticari olmayan kullanım (plan §2). Discover sonuçları 1 saat önbellekte. |
| Gemini Flash-Lite, **ücretsiz katman** (varsayılan) | $0 | Hız/günlük sınırlı, SLA yok. **İstekler Google tarafından ürün geliştirmede kullanılabilir.** Bu yüzden LLM'e yalnızca sorgu metni ve herkese açık film bilgisi gider. |
| Gemini Flash-Lite, ücretli katman | giriş $0,30 / çıkış $2,50 (1M token) | Yalnızca `GEMINI_FREE_TIER=False` ise maliyet hesaplanır. |
| Claude Haiku 5.5 (yedek/yükseltme) | giriş $0,10 / çıkış $0,50 (1M token) | `LLM_PROVIDER_CHAIN=anthropic,classic` ile açılır. API faturası claude.ai aboneliğinden ayrıdır. |
| Klasik arama (`classic`) | $0 | Kural tabanlı, ağ çağrısı yok. Zincirin her zaman son halkası. |

Fiyatlar 2026-10-08'de resmi sayfalardan alındı ([Gemini](https://ai.google.dev/gemini-api/docs/pricing), Claude fiyatları Anthropic dokümanından) ve [`cost_guard.py`](../backend/apps/search/cost_guard.py) içindeki `PRICES_PER_MTOK` tablosunda tutuluyor. Fiyat değişirse yalnızca bu tablo güncellenir. Tabloda olmayan bir model $0 sayılır ve raporda öyle görünür; bu sayede maliyet sessizce şişirilmez.

**Gemini ücretsiz katman sınırları:** Google, sayısal sınırları (dakikalık ve günlük istek) yalnızca proje bazında [AI Studio](https://aistudio.google.com/) üzerinde gösteriyor. Anahtar alındığında bu değerler buraya yazılmalı. `GUEST_DAILY_AI_SEARCHES` ve `USER_DAILY_AI_SEARCHES` toplamı, günlük istek sınırını aşmayacak şekilde ayarlanmalı. Bir AI araması 1 ayrıştırma çağrısı ve (ilk `LLM_EXPLAIN_TOP_N` sonuç için) 1 açıklama çağrısı demek, yani **2 istek**.

## Arama başına tahmin (henüz ölçülmedi)

Varsayım: önbelleğe takılmayan bir arama = ayrıştırma (~900 giriş + 200 çıkış token) + 3 sonuç için açıklama (~700 giriş + 200 çıkış token).

| Sağlayıcı | 1 arama | 10.000 arama/ay |
|---|---:|---:|
| Gemini ücretsiz katman | $0 | $0 |
| Claude Haiku 5.5 | ≈ $0,00036 | ≈ $3,6 |

Türkçe metin daha fazla token tutar; gerçek değer **ölçülene kadar 1×–2× aralığında** düşünülmeli. Ölçüm, ilk canlı haftadan sonra admin panelindeki toplamlardan buraya işlenecek (Faz 3 kabul kriteri).

## Koruma merdiveni (uygulandı)

1. **Önbellek:** Sorgu büyük/küçük harf, noktalama ve boşluktan bağımsız normalize edilir. Anahtar `sorgu + media_type + lang` (1 saat). Önbellekten dönen arama LLM çağırmaz ve kota tüketmez.
2. **Ucuz model:** Varsayılan Gemini ücretsiz katman. Model kimlikleri `.env`'den (`GEMINI_MODEL`, `ANTHROPIC_MODEL_PARSER/EXPLAIN`) okunur.
3. **Açıklamayı ucuzlatma:** Her sonuç LLM'siz şablon gerekçe alır. LLM gerekçesi yalnızca ilk `LLM_EXPLAIN_TOP_N` (varsayılan 3) sonuç için, tek toplu çağrıyla üretilir. `0` yapılırsa hiç çağrılmaz.
4. **Kota:** Misafir `GUEST_DAILY_AI_SEARCHES` (IP SHA-256 ile özetlenir, ham IP saklanmaz), üye `USER_DAILY_AI_SEARCHES`. Gece yarısı (Europe/Istanbul) sıfırlanır. Ayrıca dakikada 20 istek hız sınırı var.
5. **Günlük bütçe tavanı** (`LLM_DAILY_BUDGET_USD`, yalnızca ücretli sağlayıcılar): Her çağrının maliyeti Redis sayacına eklenir. Tavan dolunca ücretli sağlayıcılar atlanır. Ücretsiz Gemini etkilenmez.
6. **Yedek:** Hata, 429, zaman aşımı, kota ya da bütçe → klasik arama. Kullanıcı her zaman 200 ve sonuç alır. Yanıttaki `ai_status` (`ok` | `quota_exceeded` | `budget_exceeded` | `fallback`) arayüze nedenini söyler.
7. **Devre kesici:** 429/zaman aşımı/5xx/yetki hatası veren sağlayıcı `LLM_CIRCUIT_BREAKER_SECONDS` (60 sn) boyunca denenmez. Geçersiz JSON bir kez yeniden denenir.
8. **Uzunluk sınırları:** Sorgu ≤ 300 karakter. `max_tokens`: ayrıştırma 1024 (Gemini) / 2048 (Haiku), açıklama 2048 / 4096.

**Henüz yapılmadı:** Bot koruması (CAPTCHA/Turnstile) Faz 8'de, kullanıcıyla netleştirilerek. Gecelik toplu işler için Batch API, koleksiyon doğrulaması (Faz 4B) yazılınca.

## İzleme

- **Django admin → Search → LLM usage logs:** Bugün ve bu ay için çağrı, başarısız çağrı, token ve USD toplamları, ayrıca günlük bütçe durumu. Her satırda sağlayıcı, model, çağrı türü, sonuç, token ve maliyet var. **Sorgu metni, kullanıcı ve IP kaydedilmez.**
- Gece yarısı sıfırlanan sayaçlar: `llm:spend_micro_usd:<tarih>`, `llm:quota:<tarih>:<kimlik>`.
