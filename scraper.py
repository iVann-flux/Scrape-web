import requests
import re
import json
import random
import time
import os
import base64
from datetime import datetime
import pytz
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# --- সেটিংস ---
BASE_URL = "http://www.fawanews.sc/"
OUTPUT_FILE = "fawna.json" 
# আপনার দেওয়া ৩২ ক্যারেক্টারের সিক্রেট কি
SECRET_KEY = b"RanaSjja_786_AES_Enc_Key_2026_01" 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
}

# ফিল্টার কি-ওয়ার্ডস
NEWS_KEYWORDS = ["announce", "retirement", "chief", "report", "confirm", "interview", "says", "warns", "exit", "driver", "reserve", "statement", "suspension", "injury"]
MATCH_KEYWORDS = [" vs ", " v ", "cup", "league", "atp", "wta", "golf", "sport", "cricket", "football", "tennis", "tour", "nba", "basketball", "race", "prix", "match", "live"]

def get_ist_time():
    """ইন্ডিয়ান স্ট্যান্ডার্ড টাইম (IST) বের করার ফাংশন"""
    ist = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist).strftime('%d/%m/%y %H:%M:%S IST')

def encrypt_data(final_package):
    """পুরো প্যাকেজকে (Trademark + Data) এনক্রিপ্ট করার ফাংশন"""
    try:
        raw_text = json.dumps(final_package, indent=4)
        cipher = AES.new(SECRET_KEY, AES.MODE_CBC)
        iv = cipher.iv
        encrypted_bytes = cipher.encrypt(pad(raw_text.encode(), AES.block_size))
        return base64.b64encode(iv + encrypted_bytes).decode()
    except Exception as e:
        print(f"[ERROR] এনক্রিপশন ফেইল: {e}")
        return None

def fetch_proxies():
    print("[-] প্রক্সি সংগ্রহ করা হচ্ছে...")
    try:
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=gb,us&ssl=all&anonymity=all"
        res = requests.get(url, timeout=10)
        return [p.strip() for p in res.text.strip().split('\n') if p.strip()]
    except: return [None]

def push_to_github():
    print("[-] GitHub এ আপডেট পাঠানো হচ্ছে...")
    try:
        os.system('git config --global user.email "api00007@gmail.com"')
        os.system('git config --global user.name "iVann-flux"')
        
        # জটলা পরিষ্কার এবং শুধুমাত্র JSON ফাইল পুশ করা
        os.system("git add .")
        os.system('git commit -m "Auto sync" || echo "Clean"')
        os.system("git pull origin main --rebase -X ours")
        
        os.system(f"git add {OUTPUT_FILE}")
        os.system(f'git commit -m "Update: {get_ist_time()}"')
        os.system("git push origin main --force")
        print("[SUCCESS] GitHub আপডেট সফল।")
    except Exception as e:
        print(f"[ERROR] GitHub পুশ ফেইল: {e}")

def run_automation():
    proxies = fetch_proxies()
    random.shuffle(proxies)
    
    match_list = []
    session = requests.Session()
    session.headers.update(HEADERS)
    
    found_any = False
    for i, proxy in enumerate(proxies[:15]):
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        if proxy_dict: session.proxies.update(proxy_dict)
        try:
            print(f"[{i+1}/15] ট্রাই করছি: {proxy if proxy else 'Direct'}")
            session.get(BASE_URL, timeout=10)
            time.sleep(1)
            res = session.get(BASE_URL, timeout=10)
            
            if res.status_code == 200 and "fawanews" in res.text.lower():
                links_data = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', res.text, re.S)
                seen_links = set()
                for href, full_text in links_data:
                    clean_text = re.sub('<[^<]+?>', '', full_text).strip()
                    text_lower = clean_text.lower()
                    if any(bad in text_lower for bad in NEWS_KEYWORDS): continue
                    if any(k in text_lower for k in MATCH_KEYWORDS) or " vs " in text_lower:
                        if href not in seen_links:
                            full_url = href if href.startswith("http") else BASE_URL.rstrip("/") + "/" + href.lstrip("/")
                            lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
                            rivals = lines[0] if lines else "Match"
                            title = lines[1] if len(lines) >= 2 else "Live"
                            try:
                                m_res = session.get(full_url, timeout=7)
                                m3u8_links = re.findall(r'["\']([^"\']+\.m3u8[^"\']*)["\']', m_res.text)
                                m3u8_links = list(dict.fromkeys(m3u8_links))
                                for idx, m3u8 in enumerate(m3u8_links, 1):
                                    match_list.append({"Id": str(len(match_list) + 1), "Rivels": rivals, "Title": f"{title} (Stream {idx})" if len(m3u8_links) > 1 else title, "Link": f"{m3u8}|referer={BASE_URL}"})
                            except: continue
                            seen_links.add(href)
                if match_list:
                    found_any = True
                    break
        except: continue

    if found_any:
        # --- আপনার ট্রেডমার্ক প্যাকেজ তৈরি করা হচ্ছে ---
        final_package = {
            "Owner": "iVan-flux",
            "Telegram": "https://t.me/iVan_flux",
            "App name": "fawna-auto-scarpe-api",
            "Last update": get_ist_time(),
            "Total_Matches": len(match_list),
            "Live_Data": match_list
        }
        
        print(f"[+] এনক্রিপ্ট করা হচ্ছে {len(match_list)}টি লিঙ্ক...")
        encrypted_string = encrypt_data(final_package)
        
        if encrypted_string:
            with open(OUTPUT_FILE, "w") as f:
                f.write(encrypted_string)
            push_to_github()
    else:
        print("[!] কোনো ডাটা পাওয়া যায়নি।")

if __name__ == "__main__":
    while True:
        try:
            print(f"\n[!] স্ক্র্যাপ শুরু: {get_ist_time()}")
            run_automation()
            print("[-] কাজ শেষ। ১৫ মিনিট বিরতি...")
            time.sleep(900) # ১৫ মিনিট লুপ
        except KeyboardInterrupt: break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)
