# plugins/safety_shield.py
import __main__
import base64
import re
import requests
import time

# --- ১. কনফিগারেশন ও কিওয়ার্ডস ---
ADULT_KEYWORDS = [
    "erotic", "porn", "sexy", "nudity", "adult", "18+", "uncut", "kink", 
    "sex", "brazzers", "web series", "hot scenes", "softcore", "nsfw",
    "x-rated", "hardcore", "kamini", "ullu", "kooku", "desifilm"
]

# গুগল বটের জন্য একটি সেফ ইমেজ
SAFE_PLACEHOLDER = "https://i.ibb.co/9TRmN8V/nsfw-placeholder.png"
# ইমেজ যদি সার্ভার থেকে ডিলিট হয়ে যায় (ImgBB এর ক্ষেত্রে)
BROKEN_IMAGE = "https://i.ibb.co/9cc7nPh/broken-image.png"

# মেমরি ক্যাশ (একই ইমেজ বারবার আপলোড হওয়া রোধ করতে)
URL_CACHE = {}

# --- ২. টেলিগ্রাফ অটো-আপলোডার লজিক ---
def upload_to_telegraph(img_url):
    """ImgBB এর ডিলিট হওয়া থেকে বাঁচতে অটোমেটিক টেলিগ্রাফে ট্রান্সফার করবে"""
    if img_url in URL_CACHE:
        return URL_CACHE[img_url]
    
    # লোগো বা টেলিগ্রাম লিঙ্ক হলে ট্রান্সফার করার দরকার নেই
    if any(x in img_src.lower() for x in ["logo", "icon", "telegram", "banner"]):
        return img_url

    try:
        # ছবি ডাউনলোড
        response = requests.get(img_url, timeout=10)
        if response.status_code == 200:
            files = {'file': ('image.jpg', response.content, 'image/jpeg')}
            res = requests.post('https://telegra.ph/upload', files=files, timeout=15)
            res_data = res.json()
            if isinstance(res_data, list) and 'src' in res_data[0]:
                new_url = 'https://telegra.ph' + res_data[0]['src']
                URL_CACHE[img_url] = new_url
                return new_url
    except:
        pass # কোনো ভুল হলে আগের লিঙ্কই রিটার্ন করবে
    return img_url

# --- ৩. গুগল বট ও অ্যাডাল্ট ডিটেকশন ---
def is_google_bot():
    try:
        from flask import request
        ua = request.headers.get('User-Agent', '').lower()
        bots = ["googlebot", "bingbot", "yandexbot", "baiduspider", "slurp", "duckduckbot", "crawler"]
        return any(bot in ua for bot in bots)
    except:
        return False

def is_content_adult(data):
    if data.get('adult') is True or data.get('force_adult') is True:
        return True
    
    title = (data.get("title") or data.get("name") or "").lower()
    overview = (data.get("overview") or "").lower()
    
    for word in ADULT_KEYWORDS:
        if word in title or word in overview:
            return True
    return False

def encode_b64(text):
    return base64.b64encode(text.encode()).decode()

# --- ৪. প্রিমিয়াম ডিজাইন ও লার্জ স্ক্রিনশট কন্ট্রোল (CSS & JS) ---
def get_safety_shield_code(is_adult):
    if not is_adult:
        return "" 

    no_index = '<meta name="robots" content="noindex, nofollow, noarchive">'

    return f"""
    {no_index}
    <style>
        /* মাস্কিং ডিজাইন */
        .nsfw-masked {{
            position: relative !important;
            overflow: hidden !important;
            cursor: pointer !important;
            border-radius: 12px;
            background: #0d0d0d !important;
            min-height: 320px;
            display: flex; align-items: center; justify-content: center;
            border: 2px solid rgba(255, 77, 77, 0.2);
            margin-bottom: 25px;
        }}
        .nsfw-masked img {{
            filter: blur(80px) grayscale(1) !important;
            opacity: 0.25 !important;
            transition: 0.6s ease-in-out !important;
            width: 100% !important;
            height: auto !important;
        }}

        /* রিভিল হওয়ার পর স্টাইল (স্ক্রিনশট বড় দেখাবে) */
        .nsfw-unmasked {{
            display: block !important;
            min-height: auto !important;
            cursor: default !important;
            background: transparent !important;
            border: none !important;
        }}
        .nsfw-unmasked img {{
            filter: blur(0px) grayscale(0) !important;
            opacity: 1 !important;
            width: 100% !important;
            height: auto !important;
            object-fit: contain !important;
            margin-bottom: 15px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        }}

        /* স্ক্রিনশট গ্রিড রেসপন্সিভ - মোবাইলে ১টি বড় ছবি, পিসিতে ২টি বড় ছবি */
        .screenshot-grid.nsfw-unmasked {{
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)) !important;
            gap: 20px !important;
            padding: 15px 0;
        }}

        /* ওভারলে এবং বাটন */
        .nsfw-overlay {{
            position: absolute; inset: 0;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(25px);
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            z-index: 100; color: #fff; text-align: center;
            padding: 20px;
        }}
        .nsfw-btn {{
            background: linear-gradient(45deg, #ff4d4d, #c40000);
            color: white; border: none;
            padding: 14px 28px; border-radius: 50px; font-weight: bold;
            margin-top: 15px; cursor: pointer; text-transform: uppercase;
            box-shadow: 0 5px 20px rgba(255, 77, 77, 0.5);
            font-size: 15px; transition: 0.3s;
        }}
        .nsfw-btn:hover {{ transform: scale(1.05); }}
        
        .dmca-footer {{
            margin-top: 50px; padding: 25px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px; border: 1px solid #222;
            font-size: 13px; color: #777; text-align: center;
        }}
    </style>
    <script>
        function revealNSFW(el) {{
            const imgs = el.querySelectorAll('img');
            imgs.forEach(img => {{
                const encodedUrl = img.getAttribute('data-raw');
                if (encodedUrl) {{
                    const finalUrl = atob(encodedUrl);
                    img.src = finalUrl;
                    img.removeAttribute('data-raw');
                    // ব্যাকআপ এরর চেক (ImgBB ডিলিট করলে)
                    img.onerror = function() {{
                        this.src = "{BROKEN_IMAGE}";
                        this.style.filter = "none"; this.style.opacity = "1";
                    }};
                }
            }});
            el.classList.add('nsfw-unmasked');
            const overlay = el.querySelector('.nsfw-overlay');
            if(overlay) overlay.remove();
            el.onclick = null;
        }}
    </script>
    <div class="dmca-footer">
        <b>Disclaimer:</b> This site only provides metadata. We do not host any files on our server. 
        <br><br>
        <a href="https://t.me/CineZoneBD1" style="color:#ff4d4d; text-decoration:none; font-weight:bold;">Report Violation / DMCA</a>
    </div>
    """

# --- ৫. মেইন জেনারেটর প্রসেসর (Core Logic) ---
if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    is_adult = is_content_adult(data)
    is_bot = is_google_bot()
    
    # স্টিলথ মোড (বটের জন্য)
    if is_adult and is_bot:
        data['title'] = "Protected Content"
        data['overview'] = "Preview is unavailable for this content due to safety guidelines."
        links = [] 

    # মেইন এইচটিএমএল জেনারেট করা
    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    if is_adult:
        # ইমেজ রিপ্লেসমেন্ট এবং মাইগ্রেশন লজিক
        def secure_and_migrate(match):
            img_src = match.group(1)
            
            # লোগো/আইকন বাদ দিয়ে শুধু পোস্টার ও স্ক্রিনশট ধরবে
            if any(x in img_src.lower() for x in ["logo", "icon", "telegram", "banner"]):
                return match.group(0)
            
            # ImgBB থাকলে টেলিগ্রাফে পাঠানোর চেষ্টা করবে
            migrated_url = img_src
            if "ibb.co" in img_src.lower():
                migrated_url = upload_to_telegraph(img_src)
            
            if is_bot:
                return 'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"'
            
            return f'src="{SAFE_PLACEHOLDER}" data-raw="{encode_b64(migrated_url)}"'

        # এইচটিএমএল-এর ইমেজ সোর্স পরিবর্তন
        html = re.sub(r'src="([^"]+)"', secure_and_migrate, html)

        # ওভারলে UI ইনজেকশন
        overlay_html = '<div class="nsfw-overlay"><div>🔞 18+ Content Restricted</div><button class="nsfw-btn">Tap to Reveal Screenshots</button></div>'
        
        # বিভিন্ন ডিভ ক্লাসে মাস্কিং অ্যাপ্লাই
        targets = ['<div class="info-poster">', '<div class="screenshot-grid">', '<div class="screenshots">']
        for target in targets:
            if target in html:
                class_name = target[12:-1]
                html = html.replace(target, f'<div class="{class_name} nsfw-masked" onclick="revealNSFW(this)">{overlay_html}')

    return f"{html}\n{get_safety_shield_code(is_adult)}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🛡️ Safety Shield Master V3 (Auto-Migration + Ultra Large View) Activated!")
