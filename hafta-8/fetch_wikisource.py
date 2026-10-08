import urllib.request
import json
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

file_path = r'c:\Users\ardah\OneDrive\Masaüstü\yazılım\ML\projects\yz50_odevler\hafta-8\input_tr.txt'

# Kullanıcının eklediği ilk 414 satırı koruyalım, sonradan eklenen Wikipedia yazılarını silelim
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    original_text = "".join(lines[:414])
except Exception:
    original_text = ""

target_size = 1000000 # ~1 MB
text_collected = original_text

print("Vikikaynak'tan (tr.wikisource.org) şiirler, hikayeler ve edebi eserler indiriliyor...")
url = "https://tr.wikisource.org/w/api.php?action=query&generator=random&grnnamespace=0&grnlimit=20&prop=extracts&explaintext=1&format=json"

while len(text_collected) < target_size:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))
            pages = data['query'].get('pages', {})
            for page_id in pages:
                extract = pages[page_id].get('extract', '')
                if extract and len(extract) > 100:
                    text_collected += "\n\n" + extract
        
        print(f"Toplanan metin boyutu: {len(text_collected) / 1024:.0f} KB / 1000 KB")
        time.sleep(1.5)
    except Exception as e:
        print(f"\nHata: {e}")
        time.sleep(5)

text_collected = text_collected[:target_size]

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text_collected)

print(f"\nBaşarıyla eklendi! Vikikaynak eserleriyle dosya boyutu 1 MB oldu.")
