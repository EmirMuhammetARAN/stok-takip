# Stok Takip Sistemi

Bu proje, belirli e-ticaret sitelerinde (Bershka, Stradivarius) ürün stoklarını takip edip, stok geldiğinde e-posta ile bildirim gönderen bir sistemdir.

## Özellikler
- FastAPI tabanlı backend (main.py)
- Playwright ile otomatik stok kontrolü yapan worker (worker.py)
- React tabanlı frontend (frontend klasörü)
- SQLite veritabanı
- E-posta ile bildirim

## Kurulum

### 1. Backend ve Worker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  
playwright install chromium
```

### 2. Frontend

```bash
cd frontend
npm install
npm start
```

## Kullanım
1. `main.py`'yi başlatın: `uvicorn main:app --reload`
2. React arayüzünden veya API'ye POST isteği ile takip ekleyin.
3. `worker.py`'yi başlatın: `python worker.py`

## Güvenlik Uyarısı
- **Kesinlikle** `worker.py` içindeki e-posta ve şifre bilgilerinizi (GONDEREN_MAIL, SIFRE) doğrudan paylaşmayın! Bunları `.env` dosyası veya ortam değişkeni ile yönetin. Örnek:
  - `.env` dosyası oluşturun:
    ```env
    GONDEREN_MAIL=ornek@gmail.com
    SIFRE=uygulama_sifresi
    ```
  - Kodda `os.environ` ile okuyun.
- `takip.db` dosyasını ve hassas bilgileri `.gitignore` ile hariç tutun.

## .gitignore Örneği
```
venv/
__pycache__/
takip.db
.env
frontend/node_modules/
```

## Lisans
MIT
