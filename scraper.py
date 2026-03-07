import requests
import re
import json
import random
import time
import os

# --- কনফিগারেশন ---
BASE_URL = "http://www.fawanews.sc/"
OUTPUT_FILE = "fawna.json" # তোর বলা নতুন ফাইলের নাম
REPO_DIR = os.getcwd() 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.google.com/"
}

# ফিল্টার কি-ওয়ার্ডস (তোর অরিজিনাল কোড অনুযায়ী)
NEWS_KEYWORDS = ["announce", "retirement", "chief", "report", "confirm", "interview", "says", "warns", "exit", "driver", "reserve", "statement", "suspension", "injury"]
MATCH_KEYWORDS = [" vs ", " v ", "cup", "league", "atp", "wta", "golf", "sport", "cricket", "football", "tennis", "tour", "nba", "basketball", "race", "prix", "match", "live"]

def fetch_proxies():
    """ইউকে এবং ইউএসএ প্রক্সি সংগ্রহ"""
    print("[-] প্রক্সি লিস্ট সংগ্রহ করা হচ্ছে...")
    try:
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=3000&country=gb,us&ssl=all&anonymity=all"
        res = requests.get(url, timeout=5)
        return [p.strip() for p in res.text.strip().split('\n') if p.strip()]
    except:
        return [None]

def push_to_github():
    """গিটহাবে fawna.json ফাইল পুশ করার লজিক"""
    print("[-] GitHub এ আপডেট পাঠানো হচ্ছে...")
    try:
        os.system("git add .")
        os.system(f'git commit -m "Manual Update Fawna: {time.ctime()}" || echo "Nothing to commit"')
        os.system("git pull origin main --rebase")
        os.system("git push origin main")
        print("[SUCCESS] GitHub এ fawna.json আপডেট সম্পন্ন হয়েছে।")
    except Exception as e:
        print(f"[ERROR] GitHub পুশ ফেইল: {e}")

def run_scraper():
    proxies = fetch_proxies()
    random.shuffle(proxies)
    
    final_data = []
    session = requests.Session()
    session.headers.update(HEADERS)
    
    success = False
    for proxy in proxies[:15]: # প্রথম ১৫টা প্রক্সি ট্রাই করবে
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        if proxy_dict: session.proxies.update(proxy_dict)
        
        try:
            print(f"[-] ট্রাই করছি: {proxy if proxy else 'Direct'}")
            # বাধা কাটানোর জন্য ডাবল হিট
            session.get(BASE_URL, timeout=10)
            time.sleep(1)
            res = session.get(BASE_URL, timeout=10)
            
            if res.status_code == 200 and "fawanews" in res.text.lower():
                print("[SUCCESS] সাইটে ঢোকা গেছে। ডাটা প্রসেস হচ্ছে...")
                html = res.text
                
                # তোর অরিজিনাল লজিক অনুযায়ী লিঙ্ক ও টেক্সট কালেকশন
                links_data = re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.S)
                
                seen_links = set()
                for href, full_text in links_data:
                    clean_text = re.sub('<[^<]+?>', '', full_text).strip()
                    text_lower = clean_text.lower()
                    
                    if any(bad in text_lower for bad in NEWS_KEYWORDS): continue
                    
                    if any(k in text_lower for k in MATCH_KEYWORDS) or " vs " in text_lower:
                        if href not in seen_links:
                            full_url = href if href.startswith("http") else BASE_URL.rstrip("/") + "/" + href.lstrip("/")
                            
                            # Rivels ও Title আলাদা করার অরিজিনাল লজিক
                            lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
                            rivels_text = lines[0] if lines else "Live Match"
                            title_text = lines[1] if len(lines) >= 2 else "Sports Live"

                            try:
                                # ভিডিও লিঙ্ক এক্সট্রাকশন (মাল্টি-স্ট্রিম সাপোর্ট)
                                m_res = session.get(full_url, timeout=7)
                                m3u8_links = re.findall(r'["\']([^"\']+\.m3u8[^"\']*)["\']', m_res.text)
                                m3u8_links = list(dict.fromkeys(m3u8_links))

                                for idx, m3u8 in enumerate(m3u8_links, 1):
                                    link_title = f"{title_text} (Stream {idx})" if len(m3u8_links) > 1 else title_text
                                    
                                    final_data.append({
                                        "Id": str(len(final_data) + 1),
                                        "Rivels": rivels_text,
                                        "Title": link_title,
                                        "Link": f"{m3u8}|referer={BASE_URL}"
                                    })
                            except: continue
                            seen_links.add(href)
                
                if final_data:
                    success = True
                    break
        except: continue

    if final_data:
        # ফাইল সেভ করা
        with open(OUTPUT_FILE, "w") as f:
            json.dump(final_data, f, indent=4)
        print(f"[+] মোট {len(final_data)}টি লিঙ্ক fawna.json এ সেভ হয়েছে।")
        
        # গিটহাবে পুশ করা
        push_to_github()
    else:
        print("[!] কোনো ডাটা পাওয়া যায়নি। প্রক্সি সমস্যা হতে পারে।")

if __name__ == "__main__":
    # এক রাউন্ড রান হবে
    run_scraper()
