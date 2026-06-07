# ⚡ Zerith Security Bot

Yapay zeka destekli, açık kaynaklı siber güvenlik aracı.

## 📁 Proje Yapısı

```
zerith-security/
├── frontend/
│   └── index.html       ← Web sitesi (Vercel'e yükle)
├── backend/
│   ├── main.py          ← FastAPI sunucusu
│   └── requirements.txt
├── vercel.json          ← Vercel ayarları
└── README.md
```

---

## 🚀 Siteyi Yayınlama (Vercel — Ücretsiz)

### Adım 1: GitHub'a yükle
```bash
git init
git add .
git commit -m "ilk commit"
git remote add origin https://github.com/KULLANICI/zerith-security.git
git push -u origin main
```

### Adım 2: Vercel'e bağla
1. https://vercel.com adresine git, GitHub ile giriş yap
2. "New Project" → GitHub reposunu seç
3. Deploy et → `zerithsecurity.vercel.app` hazır!

---

## 🖥️ Bot Sunucusunu Çalıştırma (Railway — Ücretsiz)

### Yerel test:
```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000 adresinde çalışır
```

### Railway'e deploy (ücretsiz):
1. https://railway.app → GitHub ile giriş yap
2. "New Project" → "Deploy from GitHub repo"
3. `backend/` klasörünü seç
4. Otomatik deploy olur, URL alırsın

### Frontend'i sunucuya bağla:
`frontend/index.html` dosyasında şu satırı bul ve Railway URL'ini yaz:
```js
const API_URL = "https://SENIN-RAILWAY-URL.railway.app";
```

---

## 🔍 SEO Notları

- `index.html` içinde meta taglar zaten ayarlı
- Arama motorları `zerith security bot` aramasında siteyi bulacak
- Google Search Console'a ekle: https://search.google.com/search-console

---

## 📌 Özellikler

- ✅ Hash & MD5/SHA analizi
- ✅ Port taraması
- ✅ Log analizi
- ✅ Zafiyet tespiti
- ✅ FastAPI REST API
- ✅ Ücretsiz hosting (Vercel + Railway)
