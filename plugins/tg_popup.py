# plugins/tg_popup.py
import __main__

# --- 📢 SMART TELEGRAM POP-UP UI (প্রিমিয়াম মোডাল ডিজাইন) ---
def get_tg_popup_ui(bot_username):
    # আপনার টেলিগ্রাম চ্যানেলের লিংক (এখানে বটের ইউজারনেম বা চ্যানেলের লিংক দিতে পারেন)
    tg_url = f"https://t.me/CineZoneBD1"
    
    return f"""
    <style>
        /* 🎨 পপ-আপ ডিজাইন */
        #tg-modal-overlay {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(8px);
            display: none; align-items: center; justify-content: center;
            z-index: 999999; animation: fadeIn 0.5s ease;
        }}
        .tg-modal-content {{
            background: #1a1c22; width: 90%; max-width: 400px;
            padding: 30px; border-radius: 25px; text-align: center;
            border: 2px solid #E50914; box-shadow: 0 0 40px rgba(229, 9, 20, 0.4);
            position: relative; animation: slideUp 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        .tg-icon-box {{
            width: 80px; height: 80px; background: #0088cc;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            margin: -70px auto 20px; border: 5px solid #1a1c22;
            box-shadow: 0 10px 20px rgba(0,136,204,0.3);
        }}
        .tg-icon-box img {{ width: 45px; }}
        
        .tg-modal-title {{ color: #fff; font-size: 22px; font-weight: bold; margin-bottom: 10px; font-family: 'Poppins', sans-serif; }}
        .tg-modal-desc {{ color: #aaa; font-size: 14px; line-height: 1.6; margin-bottom: 25px; font-family: 'Poppins', sans-serif; }}
        
        .tg-join-btn {{
            display: block; background: linear-gradient(90deg, #0088cc, #00d2ff);
            color: #fff !important; text-decoration: none !important;
            padding: 15px; border-radius: 50px; font-weight: bold;
            font-size: 16px; transition: 0.3s; box-shadow: 0 5px 15px rgba(0,136,204,0.4);
        }}
        .tg-join-btn:hover {{ transform: scale(1.05); filter: brightness(1.2); }}
        
        .close-tg-modal {{
            margin-top: 15px; color: #777; font-size: 13px; cursor: pointer;
            display: inline-block; text-decoration: underline;
        }}

        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes slideUp {{ from {{ transform: translateY(50px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
    </style>

    <div id="tg-modal-overlay">
        <div class="tg-modal-content">
            <div class="tg-icon-box">
                <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram">
            </div>
            <div class="tg-modal-title">মুভি আপডেট মিস করতে না চাইলে...</div>
            <div class="tg-modal-desc">
                সব নতুন মুভি ও সিরিজের ডাইরেক্ট ডাউনলোড লিংক সবার আগে পেতে আমাদের অফিশিয়াল টেলিগ্রাম চ্যানেলে জয়েন করুন।
            </div>
            <a href="{tg_url}" target="_blank" class="tg-join-btn" onclick="closeTGModal()">
                ✈️ এখনই জয়েন করুন (JOIN NOW)
            </a>
            <div class="close-tg-modal" onclick="closeTGModal()">হয়তো পরে, এখন মুভি দেখবো</div>
        </div>
    </div>

    <script>
        /* 🧠 স্মার্ট পপ-আপ লজিক */
        function showTGModal() {{
            const shown = sessionStorage.getItem('tg_popup_shown');
            if (!shown) {{
                document.getElementById('tg-modal-overlay').style.display = 'flex';
            }}
        }}

        function closeTGModal() {{
            document.getElementById('tg-modal-overlay').style.display = 'none';
            sessionStorage.setItem('tg_popup_shown', 'true');
        }}

        /* ৩ সেকেন্ড পর পপ-আপ দেখাবে */
        setTimeout(showTGModal, 3000);
    </script>
    """

# ==========================================================
# 🔥 MONKEY PATCH: HTML GENERATOR (INJECT TG POP-UP)
# ==========================================================

original_html_func = __main__.generate_html_code

def tg_popup_injector(data, links, user_ads, owner_ads, share):
    # আগের সব প্লাগইনসহ জেনারেট করা HTML নেওয়া
    html = original_html_func(data, links, user_ads, owner_ads, share)
    
    # বটের ইউজারনেম নেওয়া (টেলিগ্রাম লিংকের জন্য)
    bot_username = ( __main__.bot.me).username
    
    # পপ-আপ কোড তৈরি করা
    tg_popup = get_tg_popup_ui(bot_username)
    
    # HTML এর একদম শেষে পপ-আপ কোডটি ইনজেক্ট করা
    return html + tg_popup

# মেইন জেনারেটর রিপ্লেস করা
__main__.generate_html_code = tg_popup_injector

async def register(bot):
    print("🚀 Smart Telegram Join Pop-up Plugin: Activated!")

print("✅ Telegram Pop-up Plugin Loaded!")
