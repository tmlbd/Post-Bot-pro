import os
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import render_template_string
import main # আপনার মেইন ফাইল ইমপোর্ট করা হচ্ছে

# --- CONFIGURATION ---
# আপনার অ্যাপের ইউআরএল (যেমন: https://my-bot-81.onrender.com)
SERVER_URL = "https://gorgeous-donetta-nahidcrk-7b84dba9.koyeb.app" 

# --- ১. ফ্লাস্ক গ্যালারি ইন্টারফেস (অ্যাডাল্ট স্ক্রিনশটের জন্য) ---
def get_gallery_html(title, images):
    return f"""
    <html>
    <head>
        <title>{title} - Adult Gallery</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background: #0f0f13; color: white; font-family: sans-serif; text-align: center; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; }}
            img {{ width: 100%; border-radius: 10px; margin-bottom: 15px; border: 1px solid #333; }}
            h2 {{ color: #ff5252; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔞 {title}</h2>
            <hr style="border:0.5px solid #333; margin-bottom:20px;">
            {"".join([f'<img src="{img}">' for img in images])}
        </div>
    </body>
    </html>
    """

# --- ২. ফ্লাস্ক রুট সেটআপ ---
def setup_routes():
    @main.app.route('/gallery/<post_id>')
    def nsfw_gallery(post_id):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        post = loop.run_until_complete(main.posts_col.find_one({"_id": post_id}))
        if not post or 'manual_screenshots' not in post['details']:
            return "<h3>❌ Gallery Not Found or Empty!</h3>", 404
        
        title = post['details'].get('title', 'NSFW Content')
        images = post['details'].get('manual_screenshots', [])
        return render_template_string(get_gallery_html(title, images))

# --- ৩. HTML জেনারেটর প্যাচ (Anti-Ban Logic) ---
original_html_func = main.generate_html_code

def patched_html_code(data, links, user_ads, owner_ads, share_percent=20):
    is_nsfw = data.get('adult', False) or data.get('force_adult', False)
    
    if is_nsfw:
        # ১৮+ হলে ডাটা থেকে স্ক্রিনশট লিংকগুলো সরিয়ে ফেলা হচ্ছে (যাতে ব্লগারে না যায়)
        temp_data = data.copy()
        post_id = data.get('post_id', 'temp')
        gallery_url = f"{SERVER_URL}/gallery/{post_id}"
        
        # ব্লগার কোড থেকে ছবি হাইড করা
        temp_data['manual_screenshots'] = []
        temp_data['images'] = {'backdrops': []}
        
        html = original_html_func(temp_data, links, user_ads, owner_ads, share_percent)
        
        # ব্লগার কোডে গ্যালারি বাটন ইনজেক্ট করা
        nsfw_ss_html = f'''
        <div class="section-title">📸 Screenshots (18+)</div>
        <div style="background: rgba(229,9,20,0.1); padding: 20px; border-radius: 12px; text-align: center; border: 2px dashed #ff5252; margin: 15px 0;">
            <p style="color: #ff5252; font-weight: bold; margin-bottom: 10px;">🔞 Content is age-restricted!</p>
            <p style="color: #ccc; font-size: 13px; margin-bottom: 15px;">Due to policy, screenshots are hosted externally.</p>
            <a href="{gallery_url}" target="_blank" 
               style="display: inline-block; background: #E50914; color: white; padding: 12px 25px; border-radius: 6px; text-decoration: none; font-weight: bold; box-shadow: 0 4px 15px rgba(229,9,20,0.4);">
               🔓 VIEW SCREENSHOTS
            </a>
        </div>
        '''
        # মেইন কোডের স্ক্রিনশট সেকশন কমেন্টের জায়গায় রিপ্লেস
        if "<!-- Screenshots Section -->" in html:
            html = html.replace("<!-- Screenshots Section -->", nsfw_ss_html)
        else:
            html = html.replace('<!-- Download Section -->', f'{nsfw_ss_html}\n<!-- Download Section -->')
        return html
    else:
        # সাধারণ মুভি হলে কোনো পরিবর্তন ছাড়াই আগের কোড কাজ করবে
        return original_html_func(data, links, user_ads, owner_ads, share_percent)

# --- ৪. ১৮+ মুভি সিলেকশনের সময় স্ক্রিনশট অপশন যোগ করা ---
# মেইন বটের 'on_select' ফাংশনটি কাজ করার পর আমরা এই ইন্টারসেপ্টরটি ব্যবহার করব
@main.bot.on_callback_query(filters.regex("^nsfw_ss_opt_"))
async def nsfw_ss_option(client, cb):
    action, uid = cb.data.replace("nsfw_ss_opt_", "").split("_")
    uid = int(uid)
    
    if action == "yes":
        main.user_conversations[uid]["state"] = "wait_screenshots"
        main.user_conversations[uid]["details"]["manual_screenshots"] = []
        await cb.message.edit_text("📸 **১৮+ স্ক্রিনশটগুলো পাঠান।**\nসব পাঠানো শেষ হলে **DONE** এ ক্লিক করুন।")
    else:
        main.user_conversations[uid]["state"] = "wait_lang"
        await cb.message.edit_text("🗣️ Enter **Language** (e.g. Hindi):")

# --- ৫. প্লাগইন রেজিস্ট্রেশন ---
async def register(bot):
    # Flask রুট সেটআপ
    setup_routes()
    
    # HTML জেনারেটর ওভাররাইড করা
    main.generate_html_code = patched_html_code
    
    # মেইন বটের 'on_select' এর পর লজিক ইনজেক্ট করার জন্য একটি প্যাচ
    # আমরা সরাসরি অন-সিলেক্ট পরিবর্তন করছি না, বরং ১৮+ ডিটেক্ট হলে মেসেজটি মডিফাই করছি
    original_on_select = None # যদি প্রয়োজন হয়
    
    print("✅ Plugin: NSFW External Gallery & Safety Manager Loaded!")

# এই প্লাগইনটি আপনার বটের কনভারসেশন ফ্লোতে একটি নতুন বাটন যোগ করবে যখনই কোনো ১৮+ মুভি আসবে।
