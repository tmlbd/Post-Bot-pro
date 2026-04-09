import __main__
import base64
import re
import os
import requests
import logging

# --- ১. কনফিগারেশন ---
logger = logging.getLogger(__name__)

# আপনার দেওয়া ImgBB API Key সরাসরি এখানে সেট করা হলো
IMGBB_API_KEY = "1821270072482fb07921cfd72d31c37e"

ADULT_KEYWORDS = ["erotic", "porn", "sexy", "nudity", "adult", "18+", "nsfw", "hot scenes"]
SAFE_PLACEHOLDER = "https://i.ibb.co/9TRmN8V/nsfw-placeholder.png"

# --- ২. ইমেজ আপলোড সিস্টেম ওভাররাইড (ImgBB নিশ্চিত করা) ---
def improved_upload_core(file_content):
    """সব ইমেজ ImgBB-তে আপলোড করার মেইন ইঞ্জিন"""
    try:
        url = "https://api.imgbb.com/1/upload"
        data = {"key": IMGBB_API_KEY}
        files = {"image": ("image.png", file_content)}
        resp = requests.post(url, data=data, files=files, timeout=25)
        if resp.status_code == 200:
            return resp.json()['data']['url']
    except Exception as e:
        logger.error(f"ImgBB Upload Error: {e}")
    return None

# মেইন বটের পুরনো ফাংশনগুলোকে হাইজ্যাক করা
def patched_upload_to_catbox(file_path):
    with open(file_path, "rb") as f:
        return improved_upload_core(f.read())

def patched_upload_to_catbox_bytes(img_bytes):
    if hasattr(img_bytes, 'read'):
        img_bytes.seek(0)
        return improved_upload_core(img_bytes.read())
    return improved_upload_core(img_bytes)

# মেইন বটের ফাংশনগুলোকে রিপ্লেস করা
__main__.upload_to_catbox = patched_upload_to_catbox
__main__.upload_to_catbox_bytes = patched_upload_to_catbox_bytes
__main__.upload_image_core = improved_upload_core


# --- ৩. গুগল বট এবং অ্যাডাল্ট কন্টেন্ট চেক ---
def is_google_bot():
    try:
        from flask import request
        ua = request.headers.get('User-Agent', '').lower()
        return any(bot in ua for bot in ["googlebot", "bingbot", "yandexbot", "baiduspider"])
    except: return False

def is_content_adult(data):
    if data.get('adult') or data.get('force_adult'): return True
    title = (data.get("title") or "").lower()
    overview = (data.get("overview") or "").lower()
    return any(word in title or word in overview for word in ADULT_KEYWORDS)

# --- ৪. প্রিমিয়াম স্ক্রিপ্ট ও ডিজাইন ইনজেক্টর ---
def get_advanced_scripts(is_adult, data):
    title = data.get("title") or data.get("name") or "Movie"
    poster = data.get("manual_poster_url") or SAFE_PLACEHOLDER
    
    # SEO Schema Markup
    schema = f"""
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "Movie",
      "name": "{title}",
      "image": "{poster}",
      "aggregateRating": {{
        "@type": "AggregateRating",
        "ratingValue": "{data.get('vote_average', 8.5)}",
        "bestRating": "10",
        "ratingCount": "450"
      }}
    }}
    </script>
    """

    # OneSignal + AdBlock + Unlock Timer Scripts
    scripts = f"""
    {schema}
    <script src="https://cdn.onesignal.com/sdks/web/v16/OneSignalSDK.page.js" defer></script>
    <script>
      window.OneSignalDeferred = window.OneSignalDeferred || [];
      OneSignalDeferred.push(async function(OneSignal) {{
        await OneSignal.init({{ appId: "d8b008a1-623d-495d-b10d-8def7460f2ea" }});
      }});

      async function detectAdBlock() {{
        let adBlockEnabled = false;
        try {{ await fetch(new Request('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js')).catch(_ => adBlockEnabled = true); }} catch (e) {{ adBlockEnabled = true; }}
        if (adBlockEnabled) {{
            document.body.innerHTML = '<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:#0f0f13;z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;font-family:sans-serif;text-align:center;padding:20px;"><h1 style="color:#ff5252;font-size:50px;">🚫</h1><h2>Ad-Blocker Detected!</h2><p>Please disable Ad-Blocker to access the download link.</p><button onclick="window.location.reload()" style="background:#E50914;color:#fff;border:none;padding:12px 25px;border-radius:5px;cursor:pointer;margin-top:20px;">I have disabled it, Refresh!</button></div>';
        }}
      }}
      window.onload = function() {{ detectAdBlock(); }};

      function startUnlock(btn, type) {{
        let randomAd = AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)];
        window.open(randomAd, '_blank'); 
        btn.disabled = true;
        btn.style.position = 'relative';
        btn.innerHTML = '⏳ SECURING LINK... <div id="unlock-timer"></div>';
        let timeLeft = 5;
        let timer = setInterval(function() {{
            if (timeLeft < 0) {{
                clearInterval(timer);
                document.getElementById('view-details').style.display = 'none';
                document.getElementById('view-links').style.display = 'block';
                window.scrollTo({{top: 0, behavior: 'smooth'}});
            }}
            timeLeft--;
        }}, 1000);
        setTimeout(() => {{ document.getElementById('unlock-timer').style.width = '100%'; }}, 100);
      }}

      function revealNSFW(el) {{
        const imgs = el.querySelectorAll('img');
        imgs.forEach(img => {{
            const raw = img.getAttribute('data-raw');
            if (raw) {{ img.src = atob(raw); img.removeAttribute('data-raw'); img.style.filter = 'none'; }}
        }});
        el.querySelector('.nsfw-overlay')?.remove();
        el.classList.add('nsfw-unmasked');
        el.onclick = null;
      }}
    </script>
    <style>
        #unlock-timer {{ position: absolute; bottom: 0; left: 0; height: 4px; background: #ff5252; width: 0%; transition: width 5s linear; box-shadow: 0 0 10px #ff5252; }}
        .nsfw-masked {{ position: relative; cursor: pointer; overflow: hidden; background: #000; border-radius: 10px; }}
        .nsfw-masked img {{ filter: blur(60px); opacity: 0.4; transition: 0.5s; }}
        .nsfw-overlay {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.6); color: #fff; font-weight: bold; z-index: 5; }}
        .nsfw-btn-ui {{ background: #ff4d4d; padding: 8px 15px; border-radius: 5px; font-size: 12px; }}
    </style>
    """
    return scripts

# --- ৫. মেইন HTML জেনারেটর ওভাররাইড ---
if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    is_adult = is_content_adult(data)
    is_bot = is_google_bot()
    
    # যদি গুগল বট আসে, তবে লিঙ্ক এবং অ্যাডাল্ট কন্টেন্ট হাইড করা
    if is_adult and is_bot:
        data['overview'] = "Content restricted for safety."
        links = []

    # মেইন HTML জেনারেট করা
    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    # অ্যাডাল্ট কন্টেন্টের ক্ষেত্রে ইমেজ মাস্কিং
    if is_adult:
        def secure_img_tags(match):
            img_src = match.group(1)
            if any(x in img_src.lower() for x in ["logo", "telegram", "icon", "banner"]): 
                return match.group(0)
            
            if is_bot: return 'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"'
            
            # ইমেজ লিঙ্ক এনকোড করে হাইড করা
            encoded_url = base64.b64encode(img_src.encode()).decode()
            return f'src="{SAFE_PLACEHOLDER}" data-raw="{encoded_url}" style="filter:blur(50px);"'

        html = re.sub(r'src="([^"]+)"', secure_img_tags, html)
        
        # UI সেকশনে মাস্কিং অ্যাপ্লাই
        overlay = '<div class="nsfw-overlay"><div class="nsfw-btn-ui">🔞 Click to Reveal</div></div>'
        if '<div class="info-poster">' in html:
            html = html.replace('<div class="info-poster">', f'<div class="info-poster nsfw-masked" onclick="revealNSFW(this)">{overlay}')
        if '<div class="screenshot-grid">' in html:
            html = html.replace('<div class="screenshot-grid">', f'<div class="screenshot-grid nsfw-masked" onclick="revealNSFW(this)">{overlay}')

    return f"{html}\n{get_advanced_scripts(is_adult, data)}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🚀 Ultimate Safety Shield & ImgBB Engine Activated!")
