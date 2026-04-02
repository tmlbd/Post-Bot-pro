import os
import sys
import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import render_template_string

# মেইন ফাইলকে ডাইনামিকভাবে খুঁজে বের করা (যাতে 'No module named main' এরর না আসে)
main = sys.modules['__main__']

# --- ১. গ্যালারি ইউআরএল (এখানে আপনার রেন্ডার/হোস্ট লিঙ্ক দিন) ---
SERVER_URL = "https://gorgeous-donetta-nahidcrk-7b84dba9.koyeb.app" 

# --- ২. ফ্লাস্ক গ্যালারি টেমপ্লেট ---
GALLERY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }} - Private Gallery</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { background: #0b0b0e; color: white; font-family: 'Segoe UI', sans-serif; text-align: center; padding: 20px; }
        .container { max-width: 800px; margin: auto; }
        img { width: 100%; border-radius: 12px; margin-bottom: 20px; border: 1px solid #1a1a24; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { color: #ff5252; text-transform: uppercase; margin-bottom: 30px; }
        .footer { color: #444; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔞 {{ title }}</h2>
        <div style="border-bottom: 1px solid #222; margin-bottom: 30px;"></div>
        {% for img in images %}
            <img src="{{ img }}" alt="Screenshot">
        {% endfor %}
        <div class="footer">Securely Hosted by SPA Bot System</div>
    </div>
</body>
</html>
"""

# --- ৩. মেইন ফাংশন প্যাচিং (Monkey Patching) ---
original_generate_html = main.generate_html_code

def patched_generate_html(data, links, user_ads, owner_ads, share=20):
    is_nsfw = data.get('adult', False) or data.get('force_adult', False)
    
    if is_nsfw:
        temp_data = data.copy()
        post_id = data.get('post_id', 'temp')
        gallery_link = f"{SERVER_URL}/gallery/{post_id}"
        
        # ব্লগার থেকে অ্যাডাল্ট ছবি সরিয়ে ফেলা (যাতে ব্যান না হয়)
        temp_data['manual_screenshots'] = []
        temp_data['images'] = {'backdrops': []}
        
        # ক্লিন HTML জেনারেট করা
        html = original_generate_html(temp_data, links, user_ads, owner_ads, share)
        
        # ব্লগার কোডে গ্যালারি বাটন ইনজেক্ট করা
        gallery_btn = f'''
        <div class="section-title">📸 Screenshots (18+)</div>
        <div style="background: rgba(229, 9, 20, 0.1); padding: 25px; border-radius: 12px; text-align: center; border: 2px dashed #ff5252; margin: 20px 0;">
            <p style="color: #ff5252; font-weight: bold; font-size: 16px; margin-bottom: 10px;">🔞 Content Age-Restricted!</p>
            <p style="color: #ccc; font-size: 13px; margin-bottom: 15px;">To comply with Blogger policy, screenshots are moved to our private server.</p>
            <a href="{gallery_link}" target="_blank" 
               style="display: inline-block; background: #E50914; color: white; padding: 14px 30px; border-radius: 8px; text-decoration: none; font-weight: bold; box-shadow: 0 4px 20px rgba(229, 9, 20, 0.5);">
               🔓 VIEW PRIVATE SCREENSHOTS
            </a>
        </div>
        '''
        if "<!-- Screenshots Section -->" in html:
            html = html.replace("<!-- Screenshots Section -->", gallery_btn)
        else:
            html = html.replace('<!-- Download Section -->', f'{gallery_btn}\n<!-- Download Section -->')
        return html
    else:
        return original_generate_html(data, links, user_ads, owner_ads, share)

# --- ৪. সিলেকশন লজিক ইন্টারসেপ্টর ---
async def patched_on_select(client, cb):
    try:
        _, m_type, m_id = cb.data.split("_")
        details = await main.get_tmdb_details(m_type, m_id)
        if not details: return await cb.message.edit_text("❌ Details not found.")
            
        uid = cb.from_user.id
        main.user_conversations[uid] = { "details": details, "links":[], "state": "" }
        
        # মুভিটি ১৮+ কি না চেক করা
        is_adult = details.get('adult', False)
        
        if is_adult:
            # যদি ১৮+ হয়, তবে ল্যাঙ্গুয়েজের আগে ম্যানুয়াল স্ক্রিনশটের অপশন দেবে
            btns = [
                [InlineKeyboardButton("✅ Yes, Add Manual SS", callback_data=f"nsfw_ask_ss_yes_{uid}")],
                [InlineKeyboardButton("⏭️ No, Skip Screenshots", callback_data=f"nsfw_ask_ss_no_{uid}")]
            ]
            await cb.message.edit_text(
                f"🔞 **অ্যাডাল্ট কন্টেন্ট ডিটেক্ট হয়েছে!**\nমুভি: **{details.get('title') or details.get('name')}**\n\nআপনি কি এই মুভির জন্য গ্যালারিতে আলাদাভাবে স্ক্রিনশট অ্যাড করতে চান?", 
                reply_markup=InlineKeyboardMarkup(btns)
            )
        else:
            # সাধারণ মুভি হলে সরাসরি আগের ফ্লো (ল্যাঙ্গুয়েজ চাওয়া)
            main.user_conversations[uid]["state"] = "wait_lang"
            await cb.message.edit_text(f"✅ Selected: **{details.get('title') or details.get('name')}**\n\n🗣️ Enter **Language**:")
            
    except Exception as e:
        print(f"Selection Error: {e}")

# --- ৫. প্লাগইন রেজিস্ট্রেশন ফাংশন ---
async def register(bot):
    # মেইন ফাইলের ফাংশনগুলো রিপ্লেস করা
    main.generate_html_code = patched_generate_html
    main.on_select = patched_on_select

    # ১৮+ স্ক্রিনশট হ্যান্ডলার
    @bot.on_callback_query(filters.regex("^nsfw_ask_ss_"))
    async def nsfw_choice(client, cb):
        _, _, _, choice, uid = cb.data.split("_")
        uid = int(uid)
        
        if choice == "yes":
            main.user_conversations[uid]["state"] = "wait_screenshots"
            main.user_conversations[uid]["details"]["manual_screenshots"] = []
            await cb.message.edit_text("📸 **১৮+ স্ক্রিনশটগুলো পাঠান।**\nএকটি একটি করে ছবি পাঠান, সব পাঠানো শেষ হলে **DONE** বাটনে ক্লিক করুন।")
        else:
            main.user_conversations[uid]["state"] = "wait_lang"
            await cb.message.edit_text("🗣️ Enter **Language** (e.g. Hindi):")

    # ফ্লাস্ক গ্যালারি রুট অ্যাড করা
    @main.app.route('/gallery/<post_id>')
    def adult_gallery_page(post_id):
        # ডাটাবেস থেকে পোস্ট রিড (Async to Sync)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        post = loop.run_until_complete(main.posts_col.find_one({"_id": post_id}))
        
        if not post or 'manual_screenshots' not in post['details']:
            return "<h3>❌ Gallery empty or post not found.</h3>", 404
            
        title = post['details'].get('title', 'NSFW Gallery')
        images = post['details'].get('manual_screenshots', [])
        return render_template_string(GALLERY_TEMPLATE, title=title, images=images)

    print("✅ Plugin: NSFW External Gallery & Selection Manager Loaded!")
