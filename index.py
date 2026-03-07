from flask import Flask, jsonify
import requests
import base64
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

app = Flask(__name__)

# --- সেটিংস ---
# কোড থেকে চাবি মুছে ফেলা হয়েছে। এখন এটি শুধুমাত্র Vercel এর Environment Variable থেকে 'AES_KEY' নেবে।
AES_RAW_KEY = os.environ.get("AES_KEY")

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/api00007/Scrape-web/main/"

def decrypt_data(encrypted_str):
    try:
        # যদি ভার্সেলে চাবি সেট করা না থাকে
        if not AES_RAW_KEY:
            return {"error": "AES_KEY is missing in Vercel settings!"}
            
        key = AES_RAW_KEY.encode()
        data = base64.b64decode(encrypted_str)
        iv = data[:16] # প্রথম ১৬ বাইট হলো IV
        encrypted_bytes = data[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        return json.loads(decrypted_bytes.decode())
    except Exception as e:
        return {"error": f"Decryption failed: {str(e)}"}

@app.route('/<filename>')
def get_data(filename):
    # ইউজার /fawna লিখলে সে fawna.json খুঁজবে
    target_file = f"{filename}.json"
    github_url = f"{GITHUB_RAW_BASE}{target_file}"
    
    try:
        response = requests.get(github_url)
        if response.status_code == 200:
            encrypted_content = response.text.strip()
            # ডাটা ডিক্রিপ্ট করা হচ্ছে
            decrypted_json = decrypt_data(encrypted_content)
            return jsonify(decrypted_json)
        else:
            return jsonify({"error": f"File {target_file} not found on GitHub"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "Owner": "iVan-flux",
        "message": "Welcome to iVan-flux API",
        "usage": "Append /fawna or /roxi to the URL."
    })

# Vercel handler
def handler(event, context):
    return app(event, context)
