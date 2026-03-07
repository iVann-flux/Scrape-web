from flask import Flask, jsonify
import requests
import base64
import os
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

app = Flask(__name__)

# ভার্সেল সেটিংস থেকে চাবিটি নেবে
AES_RAW_KEY = os.environ.get("AES_KEY")
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/api00007/Scrape-web/main/"

def decrypt_data(encrypted_str):
    try:
        if not AES_RAW_KEY:
            return {"error": "AES_KEY is not set in Vercel Environment Variables"}
            
        key = AES_RAW_KEY.encode()
        # এনক্রিপ্টেড স্ট্রিং থেকে ডাটা বের করা
        data = base64.b64decode(encrypted_str)
        iv = data[:16] 
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
            return jsonify({"error": f"File '{target_file}' not found on GitHub. Check branch name or file name."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return jsonify({
        "Owner": "iVan-flux",
        "Status": "API is Live",
        "Instruction": "Append /fawna to the URL to see decrypted data."
    })

# এটি ভার্সেলের জন্য জরুরি (Python Serverless Function)
# অতিরিক্ত কোনো handler দরকার নেই, ফ্লাস্ক অটোমেটিক কাজ করবে
