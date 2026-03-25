# plugins/tg_popup.py
import __main__

# --- 📢 SMART TELEGRAM POP-UP (WITH CROSS BUTTON) ---
def get_tg_popup_ui():
    # আপনার চ্যানেলের লিংক
    tg_url = "https://t.me/CineZoneBD1"
    
    return f"""
    <style>
        /* 🎨 পপ-আপ ডিজাইন */
        #tg-modal-overlay {{
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(10px);
            display: none; align-items: center; justify-content: center;
            z-index: 999999; animation: fadeIn 0.5s ease;
        }}
        .tg-modal-content {{
            background: #1a1c22; width: 85%; max-width: 380px;
            padding: 30px; border-radius: 25px; text-align: center;
            border: 2px solid #0088cc; box-shadow: 0 0 50px rgba(0, 136, 204, 0.4);
            position: relative; animation: slideUp 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            font-family: 'Poppins', sans-serif;
        }}
        
        /* ❌ ক্রস (Close) বাটন ডিজাইন */
        .tg-close-x {{
            position: absolute; top: 15px; right: 20px;
            color: #555; font-size: 30px; font-weight: 300;
            cursor: pointer; line-height: 1; transition: 0.3s;
            z-index: 10;
        }}
        .tg-close-x:hover {{ color: #ff5252; transform: scale(1.2); }}

        /* ✈️ আইকন বক্স */
        .tg-icon-box {{
            width: 85px; height: 85px; background: #0088cc;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
            margin: -75px auto 20px; border: 6px solid #1a1c22;
            box-shadow: 0 10px 25px rgba(0,136,204,0.4);
        }}
        .tg-icon-box img {{ width: 45px; }}
        
        .tg-modal-title {{ color: #fff; font-size: 20px; font-weight: 700; margin-bottom: 12px; }}
        .tg-modal-desc {{ color: #bbb; font-size: 14px; line-height: 1.6; margin-bottom: 25px; }}
        
        .tg-join-btn {{
            display: block; background: linear-gradient(135deg, #0088cc, #00d2ff);
            color: #fff !important; text-decoration: none !important;
            padding: 16px; border-radius: 50px; font-weight: bold;
            font-size: 16px; transition: 0.4s; box-shadow: 0 8px 20px rgba(0,136,204,0.3);
            text-transform: uppercase; letter-spacing: 1px;
        }}
        .tg-join-btn:hover {{ transform: scale(1.05); filter: brightness(1.1); }}
        
        .close-tg-modal-text {{
            margin-top: 18px; color: #666; font-size: 12px; cursor: pointer;
            display: inline-block; transition: 0.3s;
        }}
        .close-tg-modal-text:hover {{ color: #aaa; text-decoration: underline; }}

        @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
        @keyframes slideUp {{ from {{ transform: translateY(60px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}
    </style>

    <div id="tg-modal-overlay">
        <div class="tg-modal-content">
            <!-- ❌ ডানদিকের কোণায় ক্রস বাটন -->
            <div class="tg-close-x" onclick="closeTGModal()">&times;</div>
            
            <div class="tg-icon-box">
                <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="CineZoneBD1">
            </div>
            <div class="tg-modal-title">মুভি প্রেমিদের আড্ডায় স্বাগতম! ❤️</div>
            <div class="tg-modal-desc">
                সব লেটেস্ট মুভি ও সিরিজের ডাইরেক্ট ডাউনলোড লিংক মিস করতে না চাইলে আমাদের অফিশিয়াল চ্যানেলে জয়েন করুন।
            </div>
            <a href="{tg_url}" target="_blank" class="tg-join-btn" onclick="closeTGModal()">
                🚀 জয়েন করুন (JOIN CHANNEL)
            </a>
            <div class="close-tg-modal-text" onclick="closeTGModal()">হয়তো পরে, এখন মুভি দেখবো 🎬</div>
        </div>
    </div>

    <script>
        function showTGModal() {{
            const shown = sessionStorage.getItem('tg_popup_cinezone_final');
            if (!shown) {{
                document.getElementById('tg-modal-overlay').style.display = 'flex';
            }}
        }}

        function closeTGModal() {{
            document.getElementById('tg-modal-overlay').style.display = 'none';
            sessionStorage.setItem('tg_popup_cinezone_final', 'true');
        }}

        /* ৩.৫ সেকেন্ড পর ভেসে উঠবে */
        setTimeout(showTGModal, 3500);
    </script>
    """

# ==========================================================
# 🔥 MONKEY PATCH: HTML GENERATOR (INJECT POP-UP)
# ==========================================================

original_html_func = __main__.generate_html_code

def tg_popup_injector(data, links, user_ads, owner_ads, share):
    html = original_html_func(data, links, user_ads, owner_ads, share)
    tg_popup = get_tg_popup_ui()
    return html + tg_popup

# মেইন জেনারেটর রিপ্লেস করা
__main__.generate_html_code = tg_popup_injector

async def register(bot):
    print("🚀 CineZoneBD1 Telegram Pop-up (with Cross) Ready!")

print("✅ Telegram Pop-up Plugin Updated Successfully!")
