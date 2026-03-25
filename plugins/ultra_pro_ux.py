# plugins/ultra_pro_ux.py
import __main__
import base64

# --- 🎭 ADVANCED UX & UI INJECTOR ---
def get_ultra_ux_css(data):
    # মুভির ব্যাকড্রপ ইমেজ নেওয়া
    backdrop = data.get('backdrop_path')
    bg_url = f"https://image.tmdb.org/t/p/original{backdrop}" if backdrop else ""
    
    return f"""
    <style>
        /* 🌌 ইমারসিভ ব্যাকগ্রাউন্ড ইফেক্ট */
        body {{ 
            background: #05060a !important; 
            background-image: linear-gradient(to bottom, rgba(5,6,10,0.8), #05060a), url('{bg_url}') !important;
            background-attachment: fixed !important;
            background-size: cover !important;
            background-position: center !important;
        }}
        
        /* 🏷️ মিডিয়া ব্যাজ স্টাইল */
        .media-badges {{ 
            display: flex; gap: 8px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; 
        }}
        .badge {{ 
            background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
            color: #fff; font-size: 11px; padding: 3px 10px; border-radius: 4px; font-weight: 600;
            text-transform: uppercase; letter-spacing: 1px;
        }}
        .badge-4k {{ color: #ffd700; border-color: #ffd700; }}
        .badge-hdr {{ color: #00d1b2; border-color: #00d1b2; }}

        /* 📱 ফ্লোটিং অ্যাকশন বার (Mobile Pro) */
        .floating-bar {{
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            background: rgba(25, 27, 34, 0.9); backdrop-filter: blur(15px);
            padding: 10px 25px; border-radius: 50px; display: flex; gap: 25px;
            border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            z-index: 1000; transition: 0.3s;
        }}
        .floating-bar a {{ color: #fff; text-decoration: none; font-size: 13px; display: flex; align-items: center; gap: 8px; font-weight: 500; }}
        .floating-bar a:hover {{ color: #E50914; }}

        /* ⏳ স্মুদ গ্লোয়িং প্রগ্রেস */
        #unlock-timer {{
            width: 0%; height: 4px; background: linear-gradient(90deg, #E50914, #ff5252);
            position: absolute; bottom: 0; left: 0; transition: width 5s linear;
            box-shadow: 0 0 10px #E50914;
        }}
    </style>
    """

def get_ultra_ux_js():
    return """
    <script>
    /* বাটনে ক্লিক করলে প্রগ্রেস বার দেখানো */
    function startUnlock(btn, type) {
        let randomAd = AD_LINKS[Math.floor(Math.random() * AD_LINKS.length)];
        window.open(randomAd, '_blank'); 
        
        btn.style.position = 'relative';
        btn.innerHTML += '<div id="unlock-timer"></div>';
        btn.disabled = true;
        
        let timeLeft = 5;
        let timer = setInterval(function() {
            btn.innerHTML = "⏳ UNLOCKING " + timeLeft + "s";
            if (timeLeft < 0) {
                clearInterval(timer);
                document.getElementById('view-details').style.display = 'none';
                document.getElementById('view-links').style.display = 'block';
                window.scrollTo({top: 0, behavior: 'smooth'});
            }
            timeLeft--;
        }, 1000);
        
        setTimeout(() => { document.getElementById('unlock-timer').style.width = '100%'; }, 10);
    }
    </script>
    """

# ==========================================================
# 🔥 MONKEY PATCH: HTML GENERATOR (ULTRA UX)
# ==========================================================

original_html_gen = __main__.generate_html_code

def ultra_ux_generator(data, links, user_ads, owner_ads, share):
    # আগের জেনারেটর থেকে HTML নেওয়া (এতে প্রিমিয়াম টেমপ্লেটও থাকবে)
    html = original_html_gen(data, links, user_ads, owner_ads, share)
    
    # মিডিয়া ব্যাজ লজিক
    quality = data.get('custom_quality', '').upper()
    badges_html = '<div class="media-badges">'
    badges_html += '<div class="badge">Dual Audio</div>'
    if '4K' in quality or '2160P' in quality: badges_html += '<div class="badge badge-4k">4K UHD</div>'
    if '1080P' in quality: badges_html += '<div class="badge badge-hdr">1080p Full HD</div>'
    badges_html += '<div class="badge">Dolby 5.1</div><div class="badge">HEVC</div></div>'
    
    # ফ্লোটিং মেনু লজিক
    floating_menu = f"""
    <div class="floating-bar">
        <a href="https://t.me/{(await __main__.bot.get_me()).username}" target="_blank">💬 Report Link</a>
        <a href="https://t.me/{(await __main__.bot.get_me()).username}" target="_blank">✈️ Join Group</a>
    </div>
    """
    
    ux_css = get_ultra_ux_css(data)
    ux_js = get_ultra_ux_js()
    
    # HTML এ ব্যাজ ইনজেক্ট করা (মুভি টাইটেলের ঠিক নিচে)
    html = html.replace('<div class="movie-title">', badges_html + '<div class="movie-title">')
    
    # ফাইনাল আউটপুট
    return f"{ux_css}\n{ux_js}\n{html}\n{floating_menu}"

# মেইন জেনারেটর রিপ্লেস করা
__main__.generate_html_code = ultra_ux_generator

async def register(bot):
    print("🚀 Ultra UX & Immersive Design: Ready!")

print("✅ Ultra UX Plugin Loaded!")
