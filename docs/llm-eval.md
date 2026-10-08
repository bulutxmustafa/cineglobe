# LLM Kalite Kapısı — Değerlendirme Raporları

Bu dosya, arama sorgusunu filtreye çeviren LLM sağlayıcısının **kalite kapısını** (plan §3.10) geçip geçmediğini kayıt altına alır. Her çalıştırma tarihli olarak sona eklenir. Sağlayıcı veya model değiştiğinde set yeniden çalıştırılmalıdır.

**Set:** [`backend/apps/search/eval/queries.json`](../backend/apps/search/eval/queries.json). Planın 9 zorunlu senaryosu ve 21 gerçekçi TR/EN sorgu: tür hariç tutma, on yıllar, dizi durumu, oyuncu adları ve 2 prompt injection denemesi.

**Kapı (hepsi sağlanmalı):**
1. Geçerli JSON: yeniden denemeyle ≥ %95, ilk denemede ≥ %90
2. `media_type` doğruluğu ≥ %90
3. `genres_exclude` ihlali = 0 ("korku içermesin" denen sorguda korku asla dahil edilmemeli)
4. Prompt injection sorguları geçmeli
5. Ortalama yanıt süresi ≤ 6 sn

**Çalıştırma** (canlı API anahtarı gerekir, CI'da çalışmaz):
```bash
python backend/manage.py run_llm_eval --provider gemini --report docs/llm-eval.md
```
Kapı geçilmezse `LLM_PROVIDER_CHAIN=anthropic,classic` (Claude Haiku 5.5) ile tekrar çalıştırıp sonuçlar karşılaştırılır.

> **Not:** `classic` (AI'sız kural tabanlı) satırı karşılaştırma için bir taban çizgisidir. LLM'in bu tabandan özellikle oyuncu adı (`people`) ve serbest ifadelerde daha iyi olması beklenir. Gemini Flash-Lite (ücretsiz katman) 2026-10-08'de kapıyı 30/30 ile geçti; varsayılan zincir `gemini,classic` olarak kalır. Claude Haiku 5.5 ölçülmedi (gerek görülmedi).

## 2026-10-08 — `classic` (`rules`)

**Sonuç: ✅ GEÇTİ** — 27/30 sorgu tamamen doğru

| Kriter | Değer | Durum |
|---|---|---|
| Geçerli JSON (yeniden denemeyle / ilk denemede) | 100% / 100% | ✅ |
| `media_type` doğruluğu | 100% | ✅ |
| `genres_exclude` ihlali | 0 | ✅ |
| Prompt injection | geçti | ✅ |
| Ortalama süre | 0.00 sn | ✅ |

<details><summary>Başarısız sorgular</summary>

- `s9a` “Robert Downey Jr.'ın en iyi filmleri” → people=[], expected any of ['robert downey jr.']
- `s9b` “RDJ'yi seviyorum, en iyi filmlerini sırala” → people=[], expected any of ['robert downey jr.']
- `r13` “Bryan Cranston'ın oynadığı en iyi diziler” → people=[], expected any of ['bryan cranston']

</details>

## 2026-10-08 — `gemini` (`gemini-3.5-flash-lite`)

**Sonuç: ✅ GEÇTİ** — 30/30 sorgu tamamen doğru

| Kriter | Değer | Durum |
|---|---|---|
| Geçerli JSON (yeniden denemeyle / ilk denemede) | 100% / 100% | ✅ |
| `media_type` doğruluğu | 100% | ✅ |
| `genres_exclude` ihlali | 0 | ✅ |
| Prompt injection | geçti | ✅ |
| Ortalama süre | 1.42 sn | ✅ |
