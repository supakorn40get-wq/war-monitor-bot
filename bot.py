import time
import requests
import nest_asyncio
import feedparser
import asyncio
import google.generativeai as genai
from playwright.async_api import async_playwright

nest_asyncio.apply()

# === 1. ตั้งค่าบอท ===
TELEGRAM_TOKEN = "8722326137:AAGFB2lBVtwci5A6hLfzfyjhBvQ7kyTSRG0"
CHAT_ID = "1231426206"
GEMINI_API_KEY = "AIzaSyA0KbVHJ_7x3sewK-vQWujU71jpzRu2a0Y" 

URL = "https://finance.worldmonitor.app/?lat=20.0000&lon=0.0000&zoom=1.00&view=global&timeRange=7d&layers=cables%2Cpipelines%2Csanctions%2Cweather%2Ceconomic%2Cwaterways%2Coutages%2Cnatural%2CtradeRoutes"

# เพิ่มคีย์เวิร์ดเกี่ยวกับทองคำและการเงินเข้าไปแล้วครับ!
WAR_KEYWORDS = ["war", "attack", "strike", "missile", "explosion", "bombing", "invasion", "gold", "xauusd", "precious metal", "bullion"]

# เปิดใช้งานสมอง Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def send_telegram_photo(photo_path, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        payload = {"chat_id": CHAT_ID, "caption": caption}
        files = {"photo": photo}
        requests.post(url, data=payload, files=files)

def verify_news_with_gemini(headline):
    # อัปเดตคำสั่ง AI ให้ยอมรับข่าวที่เกี่ยวกับทองคำด้วย
    prompt = f"หัวข้อข่าวนี้: '{headline}' เป็นข่าวเกี่ยวกับสงคราม การโจมตีทางการทหาร ความขัดแย้งรุนแรงระหว่างประเทศ หรือเป็นข่าวสำคัญที่ส่งผลกระทบต่อราคาทองคำ (Gold/XAUUSD) ของจริงหรือไม่? (ห้ามตอบว่าเป็นถ้าเป็นแค่ชื่อหนัง เกม หรือเรื่องแต่ง) ให้ตอบกลับมาแค่คำว่า 'YES' หรือ 'NO' เท่านั้น"
    try:
        response = model.generate_content(prompt)
        answer = response.text.strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"Gemini Error: {e}")
        return False

def translate_to_thai(headline):
    prompt = f"แปลพาดหัวข่าวนี้เป็นภาษาไทยให้สละสลวย กระชับ และเป็นภาษาข่าวที่ดูเป็นทางการ: '{headline}'"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return headline

def check_breaking_news(seen_news):
    # ใช้หมวดหมู่ข่าว World News (ถ้าอยากได้ข่าวเศรษฐกิจเน้นๆ เปลี่ยนลิงก์ตรงนี้ได้ในอนาคตครับ)
    rss_url = "https://news.google.com/news/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en"
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            link = entry.link
            if link not in seen_news:
                for kw in WAR_KEYWORDS:
                    if kw in title:
                        if verify_news_with_gemini(entry.title):
                            seen_news.add(link)
                            thai_headline = translate_to_thai(entry.title)
                            
                            # ปรับหน้าตาข้อความแจ้งเตือนให้เข้ากับทั้งสายข่าวและสายเทรด
                            final_message = f"🚨 **(AI Alert) ข่าวด่วนกระทบตลาด / ความมั่นคง** 🚨\n\n🇹🇭 {thai_headline}\n🇬🇧 (ต้นฉบับ: {entry.title})"
                            return final_message
                        else:
                            seen_news.add(link) 
    except Exception as e:
        pass
    return None

async def capture_dashboard(headline):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--autoplay-policy=no-user-gesture-required", "--mute-audio"]
        )
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
        screenshot_path = "war_alert.png"
        
        await page.screenshot(path=screenshot_path, timeout=30000)
        await browser.close()
        
        send_telegram_photo(screenshot_path, headline)

async def start_monitor():
    seen_news = set()
    await capture_dashboard("✅ (TEST) เพิ่มเรดาร์ตรวจจับข่าวทองคำ (XAUUSD) เรียบร้อยแล้ว พร้อมลุยตลาดครับ!")
    
    while True:
        headline = check_breaking_news(seen_news)
        if headline:
            await capture_dashboard(headline)
        await asyncio.sleep(600)

if __name__ == "__main__":
    asyncio.run(start_monitor())
