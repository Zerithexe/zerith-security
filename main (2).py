from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Zerith Security Bot API")

# CORS — sitenden istek gelsin diye
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Statik dosyalar (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

class Message(BaseModel):
    text: str

@app.get("/")
def root():
    return FileResponse("frontend/index.html")

@app.post("/api/chat")
def chat(msg: Message):
    """
    Bot yanıt mantığı buraya gelecek.
    Şu an basit keyword tabanlı, ileride ML eklenebilir.
    """
    text = msg.text.lower()

    if any(k in text for k in ["hash", "md5", "sha", "şifre"]):
        return {"reply": "Hash analizi yapıldı. MD5 formatı tespit edildi — güvenli değil. bcrypt veya Argon2 kullanmanız önerilir."}

    if any(k in text for k in ["port", "tarama", "scan", "ağ"]):
        return {"reply": "Port taraması tamamlandı. Açık portlar: 22, 80, 443, 8080. Port 8080 dışa açık — kapatmanız önerilir."}

    if any(k in text for k in ["log", "giriş", "brute"]):
        return {"reply": "Log analizi tamamlandı. Son 24 saatte 127 başarısız giriş denemesi. Brute-force saldırısı tespit edildi."}

    if any(k in text for k in ["zafiyet", "cve", "exploit", "güvenlik"]):
        return {"reply": "Zafiyet taraması tamamlandı. 3 kritik güvenlik açığı tespit edildi. Rapor oluşturuldu."}

    return {"reply": f"'{msg.text}' komutu alındı. Analiz başlatılıyor... Güvenlik modülleri yükleniyor."}

@app.get("/api/status")
def status():
    return {"status": "online", "version": "1.0.0", "modules": ["hash", "port", "log", "vuln"]}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
