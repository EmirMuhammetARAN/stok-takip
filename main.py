from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sqlite3
from pydantic import BaseModel, EmailStr

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TakipIstegi(BaseModel):
    mail: EmailStr
    url: str
    beden: str

def db_init():
    conn = sqlite3.connect('takip.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS takipler 
                      (mail TEXT, url TEXT, beden TEXT, durum TEXT, ip TEXT)''')
    conn.commit()
    conn.close()

@app.post("/takip-baslat")
@limiter.limit("5/hour")
async def takip_baslat(request: Request, istek: TakipIstegi):
    conn = sqlite3.connect('takip.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM takipler WHERE mail = ? AND durum = 'aktif'", (istek.mail,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Aga zaten aktif bir takibin var!")
    
    client_ip = request.client.host
    cursor.execute("INSERT INTO takipler VALUES (?, ?, ?, 'aktif', ?)", 
                   (istek.mail, istek.url, istek.beden, client_ip))
    conn.commit()
    conn.close()
    return {"message": "Takip sıraya alındı. Stok gelince mail atacağız!"}

db_init()