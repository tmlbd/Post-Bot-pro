# plugins/safety_shield.py
import __main__
import json

# --- 🔞 ১৮+ মুভি চেনার জন্য কিওয়ার্ড লিস্ট ---
ADULT_KEYWORDS = ["erotic", "porn", "sexy", "nudity", "adult", "18+", "uncut", "kink"]

def is_content_adult(data):
    # ১. TMDB এর অফিসিয়াল অ্যাডাল্ট ফ্ল্যাগ চেক করা
    if data.get('adult') or data.get('force_adult'):
        return True
    
    # ২. টাইটেল বা ওভারভিউতে খারাপ শব্দ আছে কি না চেক করা
    title = (data.get("title") or data.get("name") or "").lower()
    overview = (data.get("overview") or "").lower()
    
    for word in ADULT_KEYWORDS:
        if word in title or word in overview:
            return True
    return False

# --- 🛡️ ANTI-COPYRIGHT & BLUR UI ---
def get_safety_shield_code(is_adult):
    blur_css = ""
    if is_adult:
        blur_css = """
        <style>
            .nsfw-blur { filter: blur(30px) !important; transition: 0.5s ease; cursor: pointer; }
            .nsfw-container { position: relative; overflow: hidden; border-radius: 15px; }
            .nsfw-overlay { 
                position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: rgba(0,0,0,0.8); color: #ff5252; padding: 10px 20px;
                border-radius: 50px; font-weight: bold; font-size: 14px;
                border: 2px solid #ff5252; pointer-events: none; z-index: 10;
                white-space: nowrap; text-shadow: 0 0 10px #ff5252;
            }
        </style>
        """
    
    disclaimer_html = """
    <div style="margin-top: 50px; padding: 20px; background: rgba(255,255,255,0.02); border-top: 1px solid #333; font-size: 12px; color: #666; text-align: justify; line-height: 1.6;">
        <b>DMCA & Copyright Disclaimer:</b> This website is an online metadata database and review portal. We do not host any copyrighted files or videos on our servers. All content provided here is for educational and informational purposes only. All links are indexed from third-party sources. If you believe your copyrighted work has been linked without permission, please contact us for immediate removal. 
        <br><br>
        <center><a href="https://t.me/CineZoneBD1" style="color:#E50914;">Report Content / DMCA Request</a></center>
    </div>
    """
    
    reveal_js = """
    <script>
    function revealImage(el) {
        let img = el.querySelector('img');
        let overlay = el.querySelector('.nsfw-overlay');
        if(img) img.classList.remove('nsfw-blur');
        if(overlay) overlay.style.display = 'none';
        el.onclick = null; // একবার ক্লিক করলে আর কাজ করবে না
    }
    </script>
    """
    return blur_css + disclaimer_html + reveal_js

# ==========================================================
# 🔥 MONKEY PATCH: HTML GENERATOR (SAFETY VERSION)
# ==========================================================

if not hasattr(__main__, 'shield_old_html'):
    __main__.shield_old_html = __main__.generate_html_code

def safety_shield_generator(data, links, user_ads, owner_ads, share):
    # ১. মুভিটি ১৮+ কি না চেক করা
    is_adult = is_content_adult(data)
    
    # ২. অরিজিনাল HTML কোড নেওয়া
    html = __main__.shield_old_html(data, links, user_ads, owner_ads, share)
    
    # ৩. যদি ১৮+ হয়, তবে ইমেজ ট্যাগগুলোতে ব্লার ক্লাস যোগ করা
    if is_adult:
        # মেইন পোস্টার ব্লার করা
        poster_pattern = '<div class="info-poster">'
        blur_poster = '<div class="info-poster"><div class="nsfw-container" onclick="revealImage(this)"><div class="nsfw-overlay">🔞 18+ Click to Reveal</div>'
        html = html.replace(poster_pattern, blur_poster)
        html = html.replace('alt="Poster">', 'alt="Poster" class="nsfw-blur"></div>')
        
        # স্ক্রিনশটগুলো ব্লার করা
        html = html.replace('<div class="screenshot-grid">', '<div class="screenshot-grid"><style>.screenshot-grid img { filter: blur(30px); cursor:pointer; }</style>')
        html = html.replace('<img onclick="revealNSFW(this)"', '<img onclick="this.style.filter=\'none\'"')

    # ৪. সেফটি কোড এবং ডিসক্লেইমার যুক্ত করা
    safety_code = get_safety_shield_code(is_adult)
    
    return f"{html}\n{safety_code}"

__main__.generate_html_code = safety_shield_generator

async def register(bot):
    print("🛡️ Safety Shield & Adult Blur Plugin: Activated!")

print("✅ Safety Shield Plugin Loaded Successfully!")
