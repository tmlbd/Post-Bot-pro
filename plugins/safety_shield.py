import __main__
import base64
import re

# --- ১. কনফিগারেশন ---
ADULT_KEYWORDS = [
    "erotic", "porn", "sexy", "nudity", "adult", "18+", "uncut", "kink", 
    "sex", "brazzers", "web series", "hot scenes", "softcore", "nsfw"
]

# ব্যাকআপ প্লেসহোল্ডার ইমেজ (যদি অরিজিনাল ছবি একদমই না পাওয়া যায়)
SAFE_SOURCES = [
    "https://i.ibb.co/9TRmN8V/nsfw-placeholder.png",
    "https://images2.imgbox.com/5b/72/Z8pS7FQX_o.png",
    "https://pic8.co/a/240212/65ca0f2b842c1.png"
]

# --- ২. ডিটেকশন ও এনকোডিং ---
def is_google_bot():
    try:
        from flask import request
        ua = request.headers.get('User-Agent', '').lower()
        return any(bot in ua for bot in ["googlebot", "bingbot", "yandexbot", "duckduckbot"])
    except:
        return False

def is_content_adult(data):
    if data.get('adult') is True or data.get('force_adult') is True:
        return True
    title = (data.get("title") or data.get("name") or "").lower()
    overview = (data.get("overview") or "").lower()
    return any(word in title or word in overview for word in ADULT_KEYWORDS)

def encode_b64(text):
    return base64.b64encode(text.encode()).decode()

# --- ৩. পাওয়ারফুল ইমেজ রিকভারি ও ডিজাইন ---
def get_safety_shield_code(is_adult):
    sources_json = str(SAFE_SOURCES)
    
    # অ্যাডাল্ট না হলেও ইমেজ রিকভারি স্ক্রিপ্ট কাজ করবে যাতে ছবি ১০০% দেখা যায়
    style = ""
    if is_adult:
        style = """
        <style>
            .nsfw-masked { position: relative !important; display: block !important; overflow: hidden !important; cursor: pointer !important; background: #000 !important; border-radius: 12px; margin-bottom: 20px; min-height: 250px; }
            .nsfw-masked img { filter: blur(70px) grayscale(1) !important; opacity: 0.3 !important; width: 100% !important; transition: 0.5s; }
            .nsfw-unmasked img { filter: blur(0px) grayscale(0) !important; opacity: 1 !important; }
            .nsfw-overlay { position: absolute; inset: 0; z-index: 10; background: rgba(0,0,0,0.8); backdrop-filter: blur(15px); display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; }
            .nsfw-btn { background: #ff4d4d; color: #fff; border: none; padding: 12px 24px; border-radius: 50px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(255,77,77,0.4); }
        </style>
        """

    return f"""
    {style}
    <script>
        const safeSources = {sources_json};
        
        // ইমেজ সার্ভার ডাউন থাকলে বিকল্প সোর্স ট্রাই করা
        function fixImage(img) {{
            if (img.getAttribute('data-fixed')) return;
            img.setAttribute('data-fixed', 'true');
            let original = img.src;
            // গুগল প্রক্সি ব্যবহার করে ছবি লোড করা (সার্ভার ডাউন থাকলেও ছবি আসবে)
            img.src = "https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url=" + encodeURIComponent(original);
            
            img.onerror = function() {{
                img.src = safeSources[0]; // সবশেষে প্লেসহোল্ডার
            }};
        }}

        function revealNSFW(el) {{
            const img = el.querySelector('img');
            const encodedUrl = img.getAttribute('data-raw');
            if (encodedUrl) {{
                let rawUrl = atob(encodedUrl);
                img.src = "https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url=" + encodeURIComponent(rawUrl);
                img.removeAttribute('data-raw');
                img.onerror = function() {{ this.src = rawUrl; }};
            }}
            el.classList.add('nsfw-unmasked');
            const overlay = el.querySelector('.nsfw-overlay');
            if(overlay) overlay.remove();
        }}

        // সাধারণ ইমেজের জন্য (যদি অ্যাডাল্ট না হয়)
        window.onload = function() {{
            document.querySelectorAll('img').forEach(img => {{
                if (!img.src || img.src.includes('placeholder')) return;
                img.addEventListener('error', () => fixImage(img));
            }});
        }};
    </script>
    """

# --- ৪. মেইন জেনারেটর (সব ইমেজ ফিক্স করবে) ---
if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    is_adult = is_content_adult(data)
    is_bot = is_google_bot()
    
    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    # সব ইমেজ ট্যাগের জন্য লুপ (অটো এবং ম্যানুয়াল পোস্টের জন্য)
    def process_images(match):
        img_tag = match.group(0)
        img_src = match.group(1)
        
        # আইকন বাদ দিন
        if any(x in img_src.lower() for x in ["logo", "icon", "telegram", "banner"]): 
            return img_tag
        
        if is_bot:
            return 'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"'

        if is_adult:
            # অ্যাডাল্ট হলে ব্লার মাস্ক দিয়ে র‍্যাপ করুন
            encoded_url = encode_b64(img_src)
            overlay = '<div class="nsfw-overlay">🔞<button class="nsfw-btn">Reveal Content</button></div>'
            return f'''<div class="nsfw-masked" onclick="revealNSFW(this)">{overlay}<img src="{SAFE_SOURCES[0]}" data-raw="{encoded_url}"></div>'''
        else:
            # নরমাল মুভি হলেও গুগল প্রক্সি ব্যবহার করুন যাতে ইমেজ মিসিং না হয়
            proxy_url = f"https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url={img_src}"
            return f'<img src="{proxy_url}" onerror="fixImage(this)">'

    # সব ইমেজ (img src) কে প্রক্সি দিয়ে রিপ্লেস করা হচ্ছে
    html = re.sub(r'<img [^>]*src="([^"]+)"[^>]*>', process_images, html)

    return f"{html}\n{get_safety_shield_code(is_adult)}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🛡️ Image Recovery Shield (Manual & Auto 100%) Activated!")
