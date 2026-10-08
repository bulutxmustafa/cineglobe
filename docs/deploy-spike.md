# Barındırma Denemesi (Spike): Vercel Hobby + Neon Free

Amaç: Django API'sinin Vercel + Neon üzerinde **ücretsiz** ve kabul edilebilir hızda çalıştığını ölçmek ([ADR-0004](adr/0004-hosting.md)).

**Durum:** ⏳ Kullanıcının hesap açması bekleniyor. Kod tarafı hazır (v1.8 uyumluluğu).

## 1. Hesaplar (kullanıcı yapar, kart eklemeden)
1. **Neon:** [neon.com](https://neon.com) → GitHub ile kaydol → **Free** plan → yeni proje (`cineglobe`), bölge olarak Avrupa (ör. Frankfurt). Panelde **Connection string → Pooled connection** adresini kopyala. Adres `-pooler` içerir ve `sslmode=require` ile biter.
2. **Vercel:** [vercel.com](https://vercel.com) → GitHub ile kaydol → **Hobby**. Kart isteyen bir adım çıkarsa **durun**: Hobby kart istemez.
3. Vercel → **Add New → Project** → `bulutxmustafa/cineglobe` deposunu içe aktar. **Root Directory: `backend`**. Framework olarak Django algılanmalı.

## 2. Vercel ortam değişkenleri (yalnızca Vercel panelinden girilir; sohbete veya depoya yazılmaz)
| Değişken | Değer |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | uzun rastgele bir değer (ör. `python -c "import secrets; print(secrets.token_urlsafe(50))"`) |
| `DATABASE_URL` | Neon **pooled** bağlantı adresi |
| `DJANGO_ALLOWED_HOSTS` | `.vercel.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://<proje-adı>.vercel.app` |
| `TRUSTED_PROXY_COUNT` | `1` |
| `TMDB_API_KEY`, `GEMINI_API_KEY` | `.env` dosyanızdaki değerler |

## 3. Veritabanı tablolarını oluşturma (bir kez, yerelden)
`migrate` komutu Neon'da tabloları ve önbellek tablosunu oluşturur. Neon adresini komut satırında yalnızca bu komut için verin; `.env` dosyasına yazmanız gerekmez:
Windows (PowerShell):
```powershell
$env:DATABASE_URL="<neon-pooled-adresi>"; python backend/manage.py migrate; Remove-Item Env:DATABASE_URL
```
macOS/Linux:
```bash
DATABASE_URL="<neon-pooled-adresi>" python backend/manage.py migrate
```

## 4. Ölçüm
```bash
python backend/manage.py measure_deploy https://<proje-adı>.vercel.app
```
Komut iki şeyi ölçer:
- **İlk istek:** 10+ dk boşta kaldıktan sonra `/api/v1/health/` süresi (Vercel soğuk başlangıcı + Neon uyanması).
- **Sıcak istek:** 20 istek; ortalama ve p95.

Sonucu aşağıdaki tabloya ekler.

## 5. Sonuçlar
| Tarih | İlk istek | Sıcak ort. | Sıcak p95 | Hata | Karar |
|---|---|---|---|---|---|
| — | — | — | — | — | bekleniyor |

**Karar kapısı:** ilk istek ≲ 5 sn **ve** sıcak istek ≲ 800 ms → Vercel + Neon ile devam. Aksi halde yedek plan.
