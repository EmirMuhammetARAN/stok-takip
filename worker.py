import asyncio
from playwright.async_api import async_playwright
import sqlite3
import time
import smtplib
from email.message import EmailMessage
import os

GONDEREN_MAIL = os.environ.get("GONDEREN_MAIL", "")
SIFRE = os.environ.get("SIFRE", "")

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


async def bershka_stok_kontrol(page, url, hedef_beden):
    try:
        await page.goto(f"{url}&t={int(time.time())}", wait_until="load", timeout=60000)
        try:
            if await page.is_visible("#onetrust-accept-btn-handler"):
                await page.click("#onetrust-accept-btn-handler")
        except: pass
        await asyncio.sleep(5)
        await page.mouse.wheel(0, 400)
        await asyncio.sleep(3)
        sizes = await page.query_selector_all("button[data-qa-anchor='sizeListItem'], li[data-qa-anchor='sizeListItem'], .size-item")
        for size in sizes:
            text = await size.inner_text()
            if hedef_beden.strip() in text.strip():
                classes = await size.get_attribute("class") or ""
                is_disabled = "disabled" in classes.lower() or await size.is_disabled()
                if not is_disabled:
                    return True
        return False
    except Exception:
        return False

async def stradivarius_stok_kontrol(page, url, hedef_beden):
    try:
        await page.goto(f"{url}&t={int(time.time())}", wait_until="load", timeout=60000)
        await asyncio.sleep(3)
        try:
            if await page.is_visible('button[data-testid="add-button"]'):
                await page.click('button[data-testid="add-button"]')
                await asyncio.sleep(2)
        except: pass
        sizes = await page.query_selector_all('button[data-testid="size-item"]')
        for size in sizes:
            name_el = await size.query_selector('.size-name')
            if not name_el:
                continue
            beden_text = (await name_el.inner_text()).strip()
            if hedef_beden.strip().upper() == beden_text.upper():
                classes = await size.get_attribute("class") or ""
                if 'size-no-stock' in classes:
                    return False
                return True
        return False
    except Exception:
        return False


async def master_worker():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        page = await context.new_page()

        while True:
            conn = sqlite3.connect('takip.db')
            cursor = conn.cursor()
            cursor.execute("SELECT rowid, mail, url, beden FROM takipler WHERE durum = 'aktif'")
            takipler = cursor.fetchall()
            conn.close()

            for rowid, mail, url, beden in takipler:
                if "stradivarius.com" in url:
                    stok_var = await stradivarius_stok_kontrol(page, url, beden)
                else:
                    stok_var = await bershka_stok_kontrol(page, url, beden)
                if stok_var:
                    mail_at(mail, url, beden)
                    conn = sqlite3.connect('takip.db')
                    cursor = conn.cursor()
                    cursor.execute("UPDATE takipler SET durum = 'tamamlandi' WHERE rowid = ?", (rowid,))
                    conn.commit()
                    conn.close()
                await asyncio.sleep(5)
            await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(master_worker())