import time
import requests
import nest_asyncio
import feedparser
import asyncio
from playwright.async_api import async_playwright

nest_asyncio.apply()

# === 1. ตั้งค่าบอท ===
TELEGRAM_TOKEN = "8722326137:AAGFB2lBVtwci5A6hLfzfyjhBvQ7kyTSRG0"
CHAT_ID = "1231426206"
URL = "https://finance.worldmonitor.app/?lat=20.0000&lon=0.0000&zoom=1.00&view=global&timeRange=7d&layers=cables%2Cpipelines%2Csanctions%2Cweather%2Ceconomic%2Cwaterways%2Coutages%2Cnatural%2CtradeRoutes"
WAR_KEYWORDS = ["war", "attack", "strike", "missile", "explosion", "bombing", "invasion"]

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        payload = {"chat_id": CHAT_ID, "caption": caption}
        files = {"photo": photo}
        requests.post(url, data=payload, files=files)

def check_breaking_news(seen_news):
    rss_url = "https://news.google.com/news/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            link = entry.link
            if link not in seen_news:
                for kw in WAR_KEYWORDS:
                    if kw in title:
                        seen_news.add(link)
                        return entry.title
    except Exception as e:
        pass
    return None

async def capture_dashboard(headline):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # สเปคเครื่อง GitHub แรง โหลดเว็บเสร็จไวแน่นอน
        await page.goto(URL, timeout=60000)
        await page.wait_for_timeout(10000) 
        
        try:
            pop_up_button = page.locator("text=/Got it/i").first
            await pop_up_button.wait_for(state="visible", timeout=5000)
            await pop_up_button.click(force=True)
        except:
            pass 
            
        await page.wait_for_timeout(10000) 
        screenshot_path = "war_alert.png"
        
        await page.screenshot(path=screenshot_path, timeout=30000)
        await browser.close()
        
        caption = f"🚨 **ด่วน! ตรวจพบสถานการณ์ความรุนแรง** 🚨\n\n📰 หัวข้อข่าว:\n{headline}"
        send_telegram_photo(screenshot_path, caption)

async def start_monitor():
    seen_news = set()
    
    # ส่งรูปทดสอบเครื่องใหม่
    await capture_dashboard("✅ (TEST) อัปเกรดระบบมารันบน GitHub เครื่องแรงกว่าเดิม พร้อมทำงาน!")
    
    while True:
        headline = check_breaking_news(seen_news)
        if headline:
            await capture_dashboard(headline)
        await asyncio.sleep(600) # รอ 10 นาที

if __name__ == "__main__":
    asyncio.run(start_monitor())
