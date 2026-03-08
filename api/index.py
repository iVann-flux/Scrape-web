from flask import Flask, Response, jsonify
import requests
import base64
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

app = Flask(__name__)

# ভার্সেল সেটিংস থেকে চাবি নেবে
AES_RAW_KEY = os.environ.get("AES_KEY")
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/iVann-flux/Scrape-web/main/"

def decrypt_data(encrypted_str):
    try:
        if not AES_RAW_KEY:
            return {"error": "AES_KEY is missing in Vercel settings!"}
            
        key = AES_RAW_KEY.encode()
        data = base64.b64decode(encrypted_str)
        iv = data[:16] 
        encrypted_bytes = data[16:]
        
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        
        # ডিক্রিপ্ট করার পর ডাটা যেভাবে আছে সেভাবেই লোড করবে (অর্ডার ঠিক থাকবে)
        return json.loads(decrypted_bytes.decode())
    except Exception as e:
        return {"error": f"Decryption failed: {str(e)}"}

@app.route('/<filename>')
def get_data(filename):
    target_file = f"{filename}.json"
    github_url = f"{GITHUB_RAW_BASE}{target_file}"
    
    try:
        response = requests.get(github_url)
        if response.status_code == 200:
            encrypted_content = response.text.strip()
            decrypted_json = decrypt_data(encrypted_content)
            
            # --- ট্রেডমার্ক উপরে রাখার আসল জাদু ---
            # sort_keys=False দিলে পাইথন ডিকশনারির সিরিয়াল নষ্ট হবে না
            output = json.dumps(decrypted_json, indent=4, sort_keys=False)
            return Response(output, mimetype='application/json')
        else:
            return Response(json.dumps({"error": f"File '{target_file}' not found."}), status=404, mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json')

@app.route('/')
def home():
    home_data = {
        "Owner": "iVan-flux",
        "Telegram": "https://t.me/iVan_flux",
        "App name": "fawna-auto-scarpe-api",
        "Status": "API is Live",
        "Usage": "Add /fawna to URL"
    }
    return Response(json.dumps(home_data, indent=4, sort_keys=False), mimetype='application/json')

# ভার্সেলে ফ্ল্যাস্কের জন্য বাড়তি কোনো handler এর প্রয়োজন নেই
if __name__ == '__main__':
    app.run()
