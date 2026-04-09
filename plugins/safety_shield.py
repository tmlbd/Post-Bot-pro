import __main__
import base64
import re

# --- ১. কনফিগারেশন ---
ADULT_KEYWORDS = [
    "erotic", "porn", "sexy", "nudity", "adult", "18+", "uncut", "kink", 
    "sex", "brazzers", "web series", "hot scenes", "softcore", "nsfw"
]

# ব্যাকআপ প্লেসহোল্ডার ইমেজ
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

# --- ৩. আল্টিমেট ইমেজ রিকভারি স্ক্রিপ্ট (Triple Proxy) ---
def get_safety_shield_code(is_adult):
    sources_json = str(SAFE_SOURCES)
    
    style = ""
    if is_adult:
        style = """
        <style>
            .nsfw-masked { position: relative !important; display: block !important; overflow: hidden !important; cursor: pointer !important; background: #000 !important; border-radius: 12px; margin-bottom: 20px; min-height: 250px; }
            .nsfw-masked img { filter: blur(70px) grayscale(1) !important; opacity: 0.3 !important; width: 100% !important; transition: 0.5s; }
            .nsfw-unmasked img { filter: blur(0px) grayscale(0) !important; opacity: 1 !important; }
            .nsfw-overlay { position: absolute; inset: 0; z-index: 10; background: rgba(0,0,0,0.8); backdrop-filter: blur(15px); display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; text-align: center; }
            .nsfw-btn { background: #ff4d4d; color: #fff; border: none; padding: 12px 24px; border-radius: 50px; font-weight: bold; cursor: pointer; }
        </style>
        """

    return f"""
    {style}
    <script>
        const safeSources = {sources_json};
        
        // মাল্টি-প্রক্সি রিকভারি লজিক
        function fixImage(img) {{
            let original = img.getAttribute('data-origin') || img.src;
            if (!img.getAttribute('data-origin')) img.setAttribute('data-origin', original);
            
            let attempt = parseInt(img.getAttribute('data-attempt') || "0");
            
            const proxies = [
                "https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url=",
                "https://i0.wp.com/", // WordPress Proxy
                "https://wsrv.nl/?url=" // Weserv Proxy
            ];

            if (attempt < proxies.length) {{
                let cleanUrl = original.replace(/^https?:\/\//, '');
                let nextUrl = (attempt === 1) ? proxies[attempt] + cleanUrl : proxies[attempt] + encodeURIComponent(original);
                
                img.setAttribute('data-attempt', attempt + 1);
                img.src = nextUrl;
            }} else {{
                img.onerror = null;
                img.src = safeSources[0]; // সব ফেল করলে প্লেসহোল্ডার
            }}
        }}

        function revealNSFW(el) {{
            const img = el.querySelector('img');
            const encodedUrl = img.getAttribute('data-raw');
            if (encodedUrl) {{
                let rawUrl = atob(encodedUrl);
                img.src = rawUrl;
                img.removeAttribute('data-raw');
                img.onerror = function() {{ fixImage(this); }};
            }}
            el.classList.add('nsfw-unmasked');
            const overlay = el.querySelector('.nsfw-overlay');
            if(overlay) overlay.remove();
        }}

        // পেজ লোড হওয়ার পর সব ইমেজ চেক করা
        document.addEventListener("DOMContentLoaded", function() {{
            document.querySelectorAll('img').forEach(img => {{
                if (img.src.includes('catbox.moe') || img.src.includes('googleusercontent')) {{
                    img.addEventListener('error', () => fixImage(img));
                    // যদি ইমেজ লোড না হয়ে থাকে তবে ম্যানুয়ালি ফিক্স ট্রিগার করা
                    if (img.naturalWidth === 0) fixImage(img);
                }}
            }});
        }});
    </script>
    """

# --- ৪. মেইন জেনারেটর (ম্যানুয়াল ও অটো কন্টেন্ট ফিক্সার) ---
if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    is_adult = is_content_adult(data)
    is_bot = is_google_bot()
    
    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    def process_images(match):
        img_tag = match.group(0)
        img_src = match.group(1)
        
        # আইকন বাদ দিন
        if any(x in img_src.lower() for x in ["logo", "icon", "telegram", "banner"]): 
            return img_tag
        
        if is_bot:
            return 'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"'

        if is_adult:
            encoded_url = encode_b64(img_src)
            overlay = '<div class="nsfw-overlay">🔞<br><button class="nsfw-btn">Reveal Content</button></div>'
            return f'''<div class="nsfw-masked" onclick="revealNSFW(this)">{overlay}<img src="{SAFE_SOURCES[0]}" data-raw="{encoded_url}"></div>'''
        else:
            # নরমাল মুভির জন্য সরাসরি মাল্টি-প্রক্সি সিস্টেম অ্যাপ্লাই
            proxy_url = f"https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url={img_src}"
            return f'<img src="{proxy_url}" data-origin="{img_src}" onerror="fixImage(this)">'

    # সব ইমেজ ট্যাগকে প্রসেস করা (ম্যানুয়াল আপলোড করা ইমেজসহ)
    html = re.sub(r'<img [^>]*src="([^"]+)"[^>]*>', process_images, html)

    return f"{html}\n{get_safety_shield_code(is_adult)}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🛡️ Image Recovery Shield (Triple Proxy Support) Activated!")
