# plugins/speed_booster.py
import asyncio
import aiohttp
import os
import __main__
from pyrogram import filters

# --- 🚀 NEW HIGH-SPEED SERVERS ---

async def upload_to_streamwish(file_path):
    api_key = await __main__.get_server_api("streamwish")
    if not api_key: return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.streamwish.com/api/upload/server?key={api_key}") as resp:
                data = await resp.json()
                upload_url = data['result']
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename=os.path.basename(file_path))
                form.add_field('key', api_key)
                async with session.post(upload_url, data=form) as upload_resp:
                    result = await upload_resp.json()
                    return f"https://streamwish.to/e/{result['result'][0]['filecode']}"
    except: return None

async def upload_to_vidhide(file_path):
    api_key = await __main__.get_server_api("vidhide")
    if not api_key: return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://vidhideapi.com/api/upload/server?key={api_key}") as resp:
                data = await resp.json()
                upload_url = data['result']
            with open(file_path, 'rb') as f:
                form = aiohttp.FormData()
                form.add_field('file', f, filename=os.path.basename(file_path))
                form.add_field('key', api_key)
                async with session.post(upload_url, data=form) as upload_resp:
                    result = await upload_resp.json()
                    return f"https://vidhidepro.com/v/{result['result'][0]['filecode']}"
    except: return None

# --- 🛠️ MONKEY PATCH: PROCESS FILE UPLOAD (SPEED OPTIMIZED) ---

original_process_upload = __main__.process_file_upload

async def speed_enhanced_upload(client, message, uid, temp_name):
    convo = __main__.user_conversations.get(uid)
    if not convo: return
    
    convo["pending_uploads"] = convo.get("pending_uploads", 0) + 1
    status_msg = await message.reply_text(f"🚀 **সার্ভার বুস্ট অ্যাক্টিভেটেড!**\n({temp_name})", quote=True)
    
    uploader = __main__.worker_client if (__main__.worker_client and __main__.worker_client.is_connected) else client
    
    try:
        # সেমাফোর লিমিট বাড়ানো হয়েছে ৩-এ যাতে আরও দ্রুত প্যারালাল আপলোড হয়
        async with asyncio.Semaphore(3): 
            await status_msg.edit_text(f"⏳ **১/৩: ডাটাবেসে সেভ হচ্ছে...**")
            copied_msg = await message.copy(chat_id=__main__.DB_CHANNEL_ID)
            bot_username = (await client.get_me()).username
            tg_link = f"https://t.me/{bot_username}?start=get-{copied_msg.id}"
            
            import time
            start_time = time.time()
            last_update_time = [start_time]
            
            file_path = await uploader.download_media(
                message, 
                progress=__main__.down_progress, 
                progress_args=(status_msg, start_time, last_update_time)
            )

            await status_msg.edit_text(f"⚡ **২/৩: ১০+ হাই-স্পিড সার্ভারে আপলোড হচ্ছে...**")
            
            # সকল সার্ভারে একসাথে আপলোড (প্যারালাল)
            tasks = [
                __main__.upload_to_gofile(file_path), __main__.upload_to_fileditch(file_path),
                __main__.upload_to_tmpfiles(file_path), __main__.upload_to_pixeldrain(file_path),
                __main__.upload_to_doodstream(file_path), __main__.upload_to_streamtape(file_path),
                __main__.upload_to_filemoon(file_path), __main__.upload_to_mixdrop(file_path),
                upload_to_streamwish(file_path), upload_to_vidhide(file_path) # নতুন সার্ভার
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            if os.path.exists(file_path): os.remove(file_path)
            
            convo["links"].append({
                "label": temp_name, "tg_url": tg_link, 
                "gofile_url": results[0] if not isinstance(results[0], Exception) else None,
                "fileditch_url": results[1] if not isinstance(results[1], Exception) else None,
                "tmpfiles_url": results[2] if not isinstance(results[2], Exception) else None,
                "pixel_url": results[3] if not isinstance(results[3], Exception) else None,
                "dood_url": results[4] if not isinstance(results[4], Exception) else None,
                "stape_url": results[5] if not isinstance(results[5], Exception) else None,
                "filemoon_url": results[6] if not isinstance(results[6], Exception) else None,
                "mixdrop_url": results[7] if not isinstance(results[7], Exception) else None,
                "wish_url": results[8] if not isinstance(results[8], Exception) else None,
                "hide_url": results[9] if not isinstance(results[9], Exception) else None,
                "is_grouped": True
            })
            await status_msg.edit_text(f"✅ **রকেট আপলোড সম্পন্ন:** {temp_name}")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ আপলোড ফেইলড: {e}")
    finally:
        convo["pending_uploads"] = max(0, convo.get("pending_uploads", 0) - 1)

# মেইন ফাংশন রিপ্লেস করা
__main__.process_file_upload = speed_enhanced_upload

# --- 🛠️ HTML UI ENHANCER (SPEED TAGS) ---

original_gen_html = __main__.generate_html_code

def enhanced_html_ui(data, links, user_ads, owner_ads, share):
    # অরিজিনাল কোড নেওয়া
    html = original_gen_html(data, links, user_ads, owner_ads, share)
    
    # স্পিড ব্যাজ ইনজেক্ট করার সিএসএস
    speed_css = """
    <style>
    .badge-fast { background: #00e676; color: #000; font-size: 10px; padding: 2px 6px; border-radius: 4px; margin-left: 5px; font-weight: bold; }
    .badge-high { background: #00bcd4; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; margin-left: 5px; font-weight: bold; }
    </style>
    """
    
    # HTML কোডে নামগুলো রিপ্লেস করে স্পিড ট্যাগ বসানো
    html = html.replace("▶️ GoFile Fast", '▶️ GoFile <span class="badge-fast">ULTRA FAST</span>')
    html = html.replace("✈️ Telegram Fast", '✈️ Telegram <span class="badge-high">NO WAIT</span>')
    html = html.replace("☁️ Direct Cloud", '☁️ Direct Cloud <span class="badge-fast">HIGH SPEED</span>')
    
    # নতুন সার্ভারগুলোর বাটন ইনজেক্ট করার লজিক (যদি থাকে)
    # এটি মূলত কোডের ভেতর ডাইনামিকালি অ্যাড হবে
    
    return speed_css + html

# মেইন জেনারেটর রিপ্লেস করা
__main__.generate_html_code = enhanced_html_ui

# --- 🔌 PLUGIN REGISTRATION ---
async def register(bot):
    # নতুন সার্ভারের API সেট করার কমান্ড
    @bot.on_message(filters.command("setapi_plus") & filters.user(__main__.OWNER_ID))
    async def set_api_plus(client, message):
        try:
            parts = message.text.split()
            server = parts[1].lower()
            key = parts[2]
            await __main__.set_server_api(server, key)
            await message.reply_text(f"✅ **{server.title()}** API Key Saved!")
        except:
            await message.reply_text("⚠️ `/setapi_plus streamwish KEY` অথবা `/setapi_plus vidhide KEY` লিখুন।")

    print("🚀 Speed Booster & New Servers: Ready to Launch!")

print("✅ Speed Booster Plugin Loaded!")
