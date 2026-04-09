# plugins/safety_shield.py
import __main__
import base64
import re

# --- ১. কনফিগারেশন (অ্যাডাল্ট কি-ওয়ার্ড) ---
ADULT_KEYWORDS = [
    "erotic", "porn", "sexy", "nudity", "adult", "18+", "uncut", "kink", 
    "sex", "brazzers", "web series", "hot scenes", "softcore", "nsfw"
]

# সেফ ইমেজ (যতক্ষণ ইউজার ক্লিক না করবে এটি দেখাবে)
SAFE_PLACEHOLDER = "https://i.ibb.co/9TRmN8V/nsfw-placeholder.png"
# যদি মেইন ইমেজটি ডিলিট হয়ে যায় (Broken Link), তবে এটি দেখাবে
BROKEN_IMAGE = "https://i.ibb.co/9cc7nPh/broken-image.png"

# --- ২. গুগল বট ডিটেকশন ---
def is_google_bot():
    try:
        from flask import request
        ua = request.headers.get('User-Agent', '').lower()
        bots = ["googlebot", "bingbot", "yandexbot", "baiduspider", "slurp", "duckduckbot"]
        return any(bot in ua for bot in bots)
    except:
        return False

# --- ৩. কন্টেন্ট চেক ---
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

# --- ৪. ডিজাইন ও লার্জ ইমেজ স্ক্রিপ্ট ---
def get_safety_shield_code(is_adult):
    if not is_adult:
        return "" 

    return f"""
    <style>
        /* মাস্কিং বা ব্লার অবস্থা */
        .nsfw-masked {{
            position: relative !important;
            cursor: pointer !important;
            background: #000 !important;
            min-height: 280px;
            display: flex; align-items: center; justify-content: center;
            border-radius: 10px; border: 1px solid #333;
            overflow: hidden; margin-bottom: 20px;
        }}
        .nsfw-masked img {{
            filter: blur(60px) grayscale(1) !important;
            opacity: 0.2 !important;
            width: 100% !important;
            height: auto !important;
            transition: 0.4s ease;
        }}

        /* ক্লিক করার পর ছবি যখন বড় হবে (লার্জ ভিউ) */
        .nsfw-unmasked {{
            display: block !important;
            min-height: auto !important;
            background: transparent !important;
            border: none !important;
        }}
        .nsfw-unmasked img {{
            filter: none !important;
            opacity: 1 !important;
            width: 100% !important; /* ইমেজ পুরো উইডথ হবে */
            height: auto !important; /* রেশিও ঠিক থাকবে */
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 5px 25px rgba(0,0,0,0.5);
        }}

        /* স্ক্রিনশট গ্রিড ফিক্স */
        .screenshot-grid.nsfw-unmasked {{
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
            gap: 15px;
        }}

        .nsfw-overlay {{
            position: absolute; inset: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex; flex-direction: column;
            align-items: center; justify-content: center;
            z-index: 10; color: #fff; text-align: center;
        }}
        .nsfw-btn {{
            background: #ff4d4d; color: white; border: none;
            padding: 10px 20px; border-radius: 5px; font-weight: bold;
            margin-top: 10px; cursor: pointer; text-transform: uppercase;
        }}
        .dmca-note {{
            margin-top: 30px; padding: 15px; background: #111;
            border-radius: 8px; font-size: 12px; color: #888; text-align: center;
        }}
    </style>
    <script>
        function revealNSFW(el) {{
            const imgs = el.querySelectorAll('img');
            imgs.forEach(img => {{
                const rawUrl = img.getAttribute('data-raw');
                if (rawUrl) {{
                    img.src = atob(rawUrl);
                    img.removeAttribute('data-raw');
                    // যদি ইমেজ লিঙ্ক কাজ না করে (ImgBB ডিলিট করে দেয়)
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
    <div class="dmca-note">
        <b>DMCA:</b> Content is indexed from metadata. We do not store files. 
        <br><a href="https://t.me/CineZoneBD1" style="color:#ff4d4d;">Report / Contact</a>
    </div>
    """

# --- ৫. জেনারেটর প্রসেসর ---
if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    is_adult = is_content_adult(data)
    is_bot = is_google_bot()
    
    # বটের জন্য স্টিলথ মোড
    if is_adult and is_bot:
        data['title'] = "Restricted Content"
        data['overview'] = "Preview is not available for this content."
        links = [] 

    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    if is_adult:
        # ইমেজ সোর্স মাস্কিং
        def secure_img(match):
            img_src = match.group(1)
            # লোগো এবং টেলিগ্রাম আইকন বাদ
            if any(x in img_src.lower() for x in ["logo", "icon", "telegram"]):
                return match.group(0)
            
            if is_bot: return 'src=""'
            
            encoded = encode_b64(img_src)
            return f'src="{SAFE_PLACEHOLDER}" data-raw="{encoded}"'

        html = re.sub(r'src="([^"]+)"', secure_img, html)

        # ডিভ ট্যাগ রিপ্লেসমেন্ট
        overlay = '<div class="nsfw-overlay"><div>🔞 18+ Adult Content</div><button class="nsfw-btn">Reveal Content</button></div>'
        
        targets = ['<div class="info-poster">', '<div class="screenshot-grid">', '<div class="screenshots">']
        for target in targets:
            if target in html:
                # ক্লাস এবং ক্লিক ইভেন্ট অ্যাড করা
                new_tag = target.replace('>', f' class="nsfw-masked" onclick="revealNSFW(this)">')
                html = html.replace(target, f'{new_tag}{overlay}')

    return f"{html}\n{get_safety_shield_code(is_adult)}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🛡️ Safety Shield Finalized (No-Errors + Large View) Activated!")
