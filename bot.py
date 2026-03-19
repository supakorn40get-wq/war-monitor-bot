import time
import requests
import nest_asyncio
import feedparser
import asyncio
import google.generativeai as genai
from playwright.async_api import async_playwright
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

nest_asyncio.apply()

# === 1. ตั้งค่าบอท ===
TELEGRAM_TOKEN = "8722326137:AAGFB2lBVtwci5A6hLfzfyjhBvQ7kyTSRG0"
CHAT_ID = "1231426206"
GEMINI_API_KEY = "AIzaSyA0KbVHJ_7x3sewK-vQWujU71jpzRu2a0Y" 

URL = "https://finance.worldmonitor.app/?lat=20.0000&lon=0.0000&zoom=1.00&view=global&timeRange=7d&layers=cables%2Cpipelines%2Csanctions%2Cweather%2Ceconomic%2Cwaterways%2Coutages%2Cnatural%2CtradeRoutes"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        payload = {"chat_id": CHAT_ID, "caption": caption}
        files = {"photo": photo}
        requests.post(url, data=payload, files=files)

def verify_news_with_gemini(headline):
    prompt = f"หัวข้อข่าวนี้: '{headline}' เป็นข่าวที่มีนัยสำคัญต่อตลาดการเงินโลก โดยเฉพาะราคาทองคำ (XAUUSD) หรือเป็นข่าวสงครามความรุนแรง ใช่หรือไม่? ตอบแค่ 'YES' หรือ 'NO'"
    try:
        response = model.generate_content(prompt)
        return "YES" in response.text.strip().upper()
    except Exception:
        return False

def translate_to_thai(headline):
    prompt = f"แปลพาดหัวข่าวนี้เป็นภาษาไทยให้สละสลวย กระชับ และเป็นภาษาข่าว: '{headline}'"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return headline

def check_breaking_news():
    # 🎯 เปลี่ยนจากการดูข่าวหน้า 1 เป็นการ "ค้นหา" คีย์เวิร์ดแบบเจาะจงไปเลย
    rss_url = "https://news.google.com/rss/search?q=XAUUSD+OR+Gold+OR+FED+OR+CPI+OR+interest+rate+OR+war+OR+missile&hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(rss_url)
        now = datetime.now(timezone.utc)
        
        for entry in feed.entries[:15]:  # ดึงมาเช็ค 15 ข่าวล่าสุด
            try:
                pub_date = parsedate_to_datetime(entry.published)
                # 🎯 ขยายเวลาสแกนย้อนหลังเป็น 12 ชั่วโมง (43200 วินาที) เผื่อ GitHub แอบอู้
                if (now - pub_date).total_seconds() <= 43200:
                    if verify_news_with_gemini(entry.title):
                        thai_headline = translate_to_thai(entry.title)
                        return f"🚨 **(AI Alert) ข่าวด่วนกระทบตลาดทองคำ!** 🚨\n\n🇹🇭 {thai_headline}\n🇬🇧 (ต้นฉบับ: {entry.title})"
            except Exception:
                continue
    except Exception:
        pass
    return None

async def capture_dashboard(headline):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"])
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(10000) 
        try:
            pop_up_button = page.locator("text=/Got it/i").first
            await pop_up_button.wait_for(state="visible", timeout=5000)
            await pop_up_button.click(force=True)
        except:
            pass 
        await page.wait_for_timeout(10000) 
        await page.screenshot(path="war_alert.png", timeout=30000)
        await browser.close()
        send_telegram_photo("war_alert.png", headline)

async def start_monitor():
    headline = check_breaking_news()
    if headline:
        await capture_dashboard(headline)

if __name__ == "__main__":
    asyncio.run(start_monitor())
