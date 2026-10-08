# 3. Sağlayıcıdan Bağımsız LLM Zinciri ve Maliyet Koruması

* **Durum:** Kabul Edildi (Accepted)
* **Tarih:** 2026-10-08
* **Karar Vericiler:** CineGlobe Ekibi
* **Değiştirdiği:** [ADR-0001](0001-tech-stack.md) §4 "Doğal Dil Anlama: Claude API"

## Bağlam (Context)

Plan v1.4–v1.5 ile ürün tamamen ücretsiz ve gelirsiz oldu (TMDB'nin ticari olmayan lisansına uymak için). Bu durumda her AI araması doğrudan proje sahibine maliyet yazıyor. Claude API ücretli; Gemini'nin ücretsiz katmanı ise maliyetsiz ama hız sınırlı, garantisiz ve istekleri Google'ın ürün geliştirmesinde kullanabiliyor. İlk Faz 3 uygulaması tek bir sağlayıcıya (Claude) sabitlenmişti.

## Karar (Decision)

* Tüm AI çağrıları `LLMProvider` arayüzünden geçer (`parse_query`, `explain`). Uygulamalar: `GeminiProvider`, `AnthropicProvider`, `ClassicProvider` (AI'sız kurallar).
* Hangi sağlayıcının hangi sırayla deneneceği **yalnızca ortam değişkeniyle** belirlenir: `LLM_PROVIDER_CHAIN=gemini,classic` (varsayılan). Claude Haiku 5.5'e geçmek kod değişikliği gerektirmez. `classic` her zaman zincirin sonuna eklenir.
* `LLMRouter` zinciri yönetir: geçici hatada (429, zaman aşımı, 5xx, 401/403) devre kesici 60 sn açılır; geçersiz çıktı bir kez yeniden denenir; günlük kota ve (ücretli sağlayıcılar için) günlük USD bütçesi aşılırsa AI atlanır. Her çağrı kişisel veri içermeyen `LLMUsageLog` satırıyla ve Redis harcama sayacıyla kaydedilir.
* Yapılandırılmış çıktı: Claude'da `messages.parse` + Pydantic, Gemini'de `response_json_schema`. İkisi de aynı `SearchFilters` doğrulamasından geçer.
* Kalite kapısı: `run_llm_eval` komutu, 30 sorguluk setle sağlayıcıyı ölçer; sonuç `docs/llm-eval.md`'ye işlenir. Gemini kapıyı geçemezse Haiku 5.5'e geçiş önerilir.

## Sonuçlar (Consequences)

### Olumlu
* Varsayılan işletme maliyeti $0. Ücretli sağlayıcıya geçilirse harcama günlük tavanla sınırlı.
* Hiçbir LLM durumu (çökme, kota, bütçe) arama sayfasını bozmaz; kullanıcı her zaman sonuç görür ve `ai_status` ile nedenini öğrenir.
* Yeni bir sağlayıcı eklemek tek bir sınıf ve bir kayıt satırı demek.

### Olumsuz / Dikkat Edilmesi Gerekenler
* Gemini ücretsiz katmanında gönderilen sorgular Google tarafından kullanılabilir. LLM'e yalnızca sorgu metni ve herkese açık film bilgisi gider (testle kanıtlı). Arama kutusundaki uyarı (Faz 5) ve gizlilik metni (Faz 11) bunu belirtmeli.
* Ücretsiz katmanın sınırları ve model adları habersiz değişebilir. `GEMINI_MODEL` env'den okunur, kalite kapısı periyodik yeniden çalıştırılmalı.
* Kota ve devre kesici sayaçları önbellekte tutulur; production'da Redis zorunludur (locmem süreç başına ayrı sayar).
