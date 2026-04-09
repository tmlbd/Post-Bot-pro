import __main__
import base64
import re

# --- ১. কনফিগারেশন ---
ADULT_KEYWORDS = [
    "erotic", "porn", "sexy", "nudity", "adult", "18+", "uncut", "kink", 
    "sex", "brazzers", "web series", "hot scenes", "softcore", "nsfw"
]

# ব্যাকআপ প্লেসহোল্ডার (অরিজিনাল ছবি সার্ভার থেকে ডিলিট হলে বা না পাওয়া গেলে এটি দেখাবে)
SAFE_SOURCES = [
    "https://i.ibb.co/9TRmN8V/nsfw-placeholder.png",
    "https://images2.imgbox.com/5b/72/Z8pS7FQX_o.png"
]

# --- ২. ডিটেকশন লজিক ---
def is_google_bot():
    try:
        from flask import request
        ua = request.headers.get('User-Agent', '').lower()
        bots = ["googlebot", "bingbot", "yandexbot", "baiduspider", "slurp", "duckduckbot"]
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

# --- ৩. পাওয়ারফুল জাভাস্ক্রিপ্ট (ইমেজ রিকভারি + ডিজাইন) ---
def get_safety_shield_code(is_adult):
    sources_json = str(SAFE_SOURCES)
    
    # অ্যাডাল্ট কন্টেন্টের জন্য প্রিমিয়াম ব্লার ডিজাইন
    style_code = ""
    if is_adult:
        style_code = """
        <style>
            .nsfw-masked { position: relative !important; display: block !important; overflow: hidden !important; cursor: pointer !important; background: #000 !important; border-radius: 12px; margin-bottom: 20px; min-height: 250px; border: 1px solid #333; }
            .nsfw-masked img { filter: blur(75px) grayscale(1) !important; opacity: 0.3 !important; width: 100% !important; transition: 0.6s ease-in-out !important; }
            .nsfw-unmasked img { filter: blur(0px) grayscale(0) !important; opacity: 1 !important; box-shadow: 0 10px 30px rgba(0,0,0,0.7); }
            .nsfw-overlay { position: absolute; inset: 0; z-index: 10; background: rgba(0,0,0,0.8); backdrop-filter: blur(15px); display: flex; flex-direction: column; align-items: center; justify-content: center; color: #fff; text-align: center; }
            .nsfw-btn { background: #ff4d4d; color: #fff; border: none; padding: 12px 26px; border-radius: 50px; font-weight: bold; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 15px rgba(255,77,77,0.4); }
        </style>
        """

    return f"""
    {style_code}
    <script>
        const safeSources = {sources_json};

        // মাল্টি-প্রক্সি ফেইলওভার সিস্টেম (ইমেজ ফিক্সার)
        function fixImage(img) {{
            if (img.getAttribute('data-fixing') === 'true') return;
            img.setAttribute('data-fixing', 'true');

            let originalUrl = img.getAttribute('data-origin') || img.src;
            if (!img.getAttribute('data-origin')) img.setAttribute('data-origin', originalUrl);

            let attempt = parseInt(img.getAttribute('data-attempt') || "0");
            
            // প্রক্সি লিস্ট (গুগল, ওয়ার্ডপ্রেস, এবং ওয়েসার্ভ)
            const proxies = [
                "https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=2592000&url=" + encodeURIComponent(originalUrl),
                "https://i0.wp.com/" + originalUrl.replace(/^https?:\/\//, ''),
                "https://wsrv.nl/?url=" + encodeURIComponent(originalUrl)
            ];

            if (attempt < proxies.length) {{
                img.setAttribute('data-attempt', attempt + 1);
                img.src = proxies[attempt];
                img.setAttribute('data-fixing', 'false');
            }} else {{
                img.onerror = null;
                img.src = safeSources[0]; // সব পদ্ধতি ব্যর্থ হলে প্লেসহোল্ডার
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
                // যদি ইমেজ লোড না হয় তবে ফিক্স ফাংশন কল করো
                setTimeout(() => {{ if(img.naturalWidth === 0) fixImage(img); }}, 500);
            }}
            el.classList.add('nsfw-unmasked');
            const overlay = el.querySelector('.nsfw-overlay');
            if(overlay) overlay.remove();
            el.onclick = null;
        }}

        // পেজ লোড হওয়ার পরBroken ইমেজগুলো চেক করা
        document.addEventListener("DOMContentLoaded", function() {{
            document.querySelectorAll('img').forEach(img => {{
                if (img.naturalWidth === 0) fixImage(img);
                img.onerror = function() {{ fixImage(this); }};
            }});
        }});
    </script>
    """

# --- ৪. মেইন জেনারেটর (ইন্টিগ্রেশন) ---
if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    is_adult = is_content_adult(data)
    is_bot = is_google_bot()
    
    # বটকে কন্টেন্ট থেকে দূরে রাখা
    if is_adult and is_bot:
        data['title'] = "Content Restricted"
        data['overview'] = "Preview unavailable for safety policy reasons."
        links = [] 

    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    # সব ইমেজ ট্যাগকে প্রসেস করা (ম্যানুয়াল আপলোড করা ইমেজসহ)
    def process_images(match):
        img_tag = match.group(0)
        img_src = match.group(1)
        
        # আইকন, লোগো বা টেলিগ্রাম ব্যানার বাদ দিন
        if any(x in img_src.lower() for x in ["logo", "icon", "telegram", "banner", "onesignal"]): 
            return img_tag
        
        if is_bot:
            return 'src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"'

        if is_adult:
            # অ্যাডাল্ট হলে ব্লার মাস্ক এবং এনকোডেড সোর্স
            encoded_url = encode_b64(img_src)
            overlay = '<div class="nsfw-overlay">🔞<br><button class="nsfw-btn">Reveal Content</button></div>'
            return f'''<div class="nsfw-masked" onclick="revealNSFW(this)">{overlay}<img src="{SAFE_SOURCES[0]}" data-raw="{encoded_url}" data-origin="{img_src}"></div>'''
        else:
            # নরমাল মুভির জন্য সরাসরি ইমেজ রিকভারি প্রক্সি অ্যাপ্লাই
            return f'<img src="{img_src}" data-origin="{img_src}" onerror="fixImage(this)">'

    # সব <img> ট্যাগের সোর্স খুঁজে প্রসেস করা হচ্ছে
    html = re.sub(r'<img [^>]*src="([^"]+)"[^>]*>', process_images, html)

    return f"{html}\n{get_safety_shield_code(is_adult)}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🛡️ Safety Shield: 100% Image Recovery & NSFW Protection Active!")
