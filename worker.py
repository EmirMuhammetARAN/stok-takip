from dotenv import load_dotenv
load_dotenv()

import time
import sqlite3
import smtplib
import re
import os
import random
import requests
from email.message import EmailMessage

GONDEREN_MAIL = os.environ.get("GONDEREN_MAIL", "")
SIFRE = os.environ.get("SIFRE", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html,*/*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.bershka.com/",
}

def mail_at(alici, urun_url, beden):
    msg = EmailMessage()
    msg.set_content(f"Aga selam! Takip ettiğin {beden} beden ürün stokta!\n\nÜrün: {urun_url}")
    msg['Subject'] = f"STOK ALARMI: {beden} Beden Geldi!"
    msg['From'] = GONDEREN_MAIL
    msg['To'] = alici
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(GONDEREN_MAIL, SIFRE)
            smtp.send_message(msg)
        print(f"[{alici}] adresine mail atıldı.")
    except Exception as e:
        print(f"Mail hatası: {e}")


def urun_id_al(url):
    # URL'den ürün ID'sini çıkar: -c0p123456789.html veya -p123456789.html
    match = re.search(r'[cp](\d{6,})', url)
    if match:
        return match.group(1)
    return None


def bershka_stok_kontrol(url, hedef_beden):
    try:
        urun_id = urun_id_al(url)
        if not urun_id:
            print(f"Ürün ID bulunamadı: {url}")
            return False

        # Türkiye store ID
        store_id = "45009507"
        country_id = "TR"
        
        api_url = f"https://www.bershka.com/itxrest/3/catalog/store/{store_id}/40259526/category/0/product/{urun_id}/detail?languageId=-5&appId=1"
        
        headers = HEADERS.copy()
        headers["Referer"] = url
        
        r = requests.get(api_url, headers=headers, timeout=20)
        
        if r.status_code != 200:
            print(f"Bershka API hata: {r.status_code}")
            return False
        
        data = r.json()
        
        # Bedenleri kontrol et
        detail = data.get("detail", {})
        colors = detail.get("colors", [])
        
        for color in colors:
            sizes = color.get("sizes", [])
            for size in sizes:
                size_name = size.get("name", "").strip()
                if hedef_beden.strip().upper() == size_name.upper():
                    stock = size.get("stock", {})
                    quantity = stock.get("quantity", 0)
                    if quantity > 0:
                        return True
        return False
    except Exception as e:
        print(f"Bershka hata: {e}")
        return False


def stradivarius_stok_kontrol(url, hedef_beden):
    try:
        urun_id = urun_id_al(url)
        if not urun_id:
            print(f"Ürün ID bulunamadı: {url}")
            return False

        store_id = "45109525"
        
        api_url = f"https://www.stradivarius.com/itxrest/3/catalog/store/{store_id}/40259526/category/0/product/{urun_id}/detail?languageId=-5&appId=1"
        
        headers = HEADERS.copy()
        headers["Referer"] = url
        
        r = requests.get(api_url, headers=headers, timeout=20)
        
        if r.status_code != 200:
            print(f"Stradivarius API hata: {r.status_code}")
            return False
        
        data = r.json()
        
        detail = data.get("detail", {})
        colors = detail.get("colors", [])
        
        for color in colors:
            sizes = color.get("sizes", [])
            for size in sizes:
                size_name = size.get("name", "").strip()
                if hedef_beden.strip().upper() == size_name.upper():
                    stock = size.get("stock", {})
                    quantity = stock.get("quantity", 0)
                    if quantity > 0:
                        return True
        return False
    except Exception as e:
        print(f"Stradivarius hata: {e}")
        return False


def master_worker():
    print("Worker başladı!")
    while True:
        conn = sqlite3.connect('takip.db')
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, mail, url, beden FROM takipler WHERE durum = 'aktif'")
        takipler = cursor.fetchall()
        conn.close()

        print(f"Aktif takip sayısı: {len(takipler)}")

        for rowid, mail, url, beden in takipler:
            try:
                if "stradivarius.com" in url:
                    stok_var = stradivarius_stok_kontrol(url, beden)
                else:
                    stok_var = bershka_stok_kontrol(url, beden)
                
                print(f"[{beden}] {url[:50]}... → {'STOKTA!' if stok_var else 'yok'}")
                
                if stok_var:
                    mail_at(mail, url, beden)
                    conn = sqlite3.connect('takip.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE takipler SET durum = 'tamamlandi' WHERE rowid = ?", (rowid,))
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"Hata: {e}")
            
            # Her ürün arasında random bekleme, bot gibi görünmesin
            time.sleep(random.uniform(3, 8))
        
        # 10 dakikada bir kontrol
        print("10 dakika bekleniyor...")
        time.sleep(600)


if __name__ == "__main__":
    master_worker()
