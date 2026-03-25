import os
import time
import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# মেইন বটের ফাংশন ও ভ্যারিয়েবল ইমপোর্ট
try:
    from bot import (
        user_conversations, upload_semaphore, DB_CHANNEL_ID, 
        upload_to_gofile, upload_to_fileditch, upload_to_tmpfiles,
        upload_to_pixeldrain, upload_to_doodstream, upload_to_streamtape,
        upload_to_filemoon, upload_to_mixdrop, logger
    )
except ImportError:
    from __main__ import (
        user_conversations, upload_semaphore, DB_CHANNEL_ID, 
        upload_to_gofile, upload_to_fileditch, upload_to_tmpfiles,
        upload_to_pixeldrain, upload_to_doodstream, upload_to_streamtape,
        upload_to_filemoon, upload_to_mixdrop, logger
    )

async def progress_callback(current, total, status_msg, start_time):
    now = time.time()
    if not hasattr(progress_callback, "last_update"):
        progress_callback.last_update = 0
    if now - progress_callback.last_update >= 4.0 or current == total:
        progress_callback.last_update = now
        percent = (current / total) * 100 if total > 0 else 0
        speed = current / (now - start_time) if (now - start_time) > 0 else 1
        
        def hbytes(size):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0: return f"{size:.2f} {unit}"
                size /= 1024.0
            return f"{size:.2f} TB"

        bar = "🟢" * int(percent / 10) + "⚪" * (10 - int(percent / 10))
        text = (f"🚀 **সার্ভারে ফাইল ডাউনলোড হচ্ছে...**\n\n"
                f"📊 {bar} **{percent:.1f}%**\n"
                f"💾 {hbytes(current)} / {hbytes(total)}\n"
                f"⚡ স্পিড: {hbytes(speed)}/s")
        try: await status_msg.edit_text(text)
        except: pass

async def download_worker(url, file_path, status_msg):
    start_time = time.time()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=None, allow_redirects=True) as resp:
                if resp.status != 200:
                    return False, f"সার্ভার থেকে এরর এসেছে (Status: {resp.status})"
                
                # কন্টেন্ট টাইপ চেক - সবচেয়ে গুরুত্বপূর্ণ অংশ
                ctype = resp.headers.get('Content-Type', '').lower()
                if 'text' in ctype or 'html' in ctype:
                    return False, "এটি একটি ডাউনলোড ওয়েব পেজ (HTML), ডিরেক্ট ফাইল লিংক নয়।"
                
                # ফাইলের সাইজ চেক
                total_size = int(resp.headers.get('content-length', 0))
                if total_size < 1024 * 1024: # ১ এমবি এর কম হলে ভিডিও হওয়ার সম্ভাবনা নেই
                    return False, "ফাইলের সাইজ খুবই ছোট, এটি কোনো ভিডিও ফাইল নয়।"

                downloaded = 0
                with open(file_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(1024*1024):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            await progress_callback(downloaded, total_size, status_msg, start_time)
                return True, "Success"
        except Exception as e:
            return False, f"লিংক এরর: {str(e)}"

@Client.on_message(filters.private & filters.text & filters.incoming, group=-1)
async def url_upload_handler(client, message):
    uid = message.from_user.id
    text = message.text.strip()
    
    if uid not in user_conversations: return
    convo = user_conversations[uid]
    
    # শুধুমাত্র লিংক দেওয়ার স্টেজে কাজ করবে
    if convo.get("state") != "wait_link_url" or not text.startswith("http"):
        return

    # 🛑 মেইন বোটের প্রসেস থামিয়ে দেওয়া (এটিই মেইন কোডকে বাইপাস করবে)
    message.stop_propagation()

    temp_name = convo.get("temp_name", "Remote File")
    status_msg = await message.reply_text("🔍 **ডিরেক্ট লিংক কি না যাচাই করা হচ্ছে...**", quote=True)
    
    local_filename = f"dl_{uid}_{int(time.time())}.mp4"
    
    try:
        async with upload_semaphore:
            success, error_msg = await download_worker(text, local_filename, status_msg)
            
            if not success:
                # 🛑 ওয়ার্নিং মেসেজ: কোনো কিছু সেভ হবে না
                await status_msg.edit_text(
                    f"⚠️ **সতর্কবার্তা (Invalid Link!)**\n\n"
                    f"❌ **এরর:** {error_msg}\n\n"
                    f"বট আপনার এই লিংকটি **Save করেনি**।\n"
                    f"দয়া করে ভিডিও ফাইলটির আসল **Direct Link** কপি করে পুনরায় সেন্ড করুন।"
                )
                return

            # ডিরেক্ট ফাইল হলে আপলোড প্রসেস শুরু
            await status_msg.edit_text("⏳ **ডাউনলোড সফল! এখন মিরর সার্ভারগুলোতে আপলোড হচ্ছে...**")

            # টেলিগ্রাম ব্যাকআপ
            tg_msg = await client.send_document(chat_id=DB_CHANNEL_ID, document=local_filename, caption=f"Remote Upload: {temp_name}")
            bot_username = (await client.get_me()).username
            tg_link = f"https://t.me/{bot_username}?start=get-{tg_msg.id}"

            # মিররিং (প্যারালাল)
            res = await asyncio.gather(
                upload_to_gofile(local_filename), upload_to_fileditch(local_filename), 
                upload_to_tmpfiles(local_filename), upload_to_pixeldrain(local_filename), 
                upload_to_doodstream(local_filename), upload_to_streamtape(local_filename),
                upload_to_filemoon(local_filename), upload_to_mixdrop(local_filename), 
                return_exceptions=True
            )

            if os.path.exists(local_filename): os.remove(local_filename)

            convo["links"].append({
                "label": temp_name, "tg_url": tg_link, 
                "gofile_url": res[0] if not isinstance(res[0], Exception) else None,
                "fileditch_url": res[1] if not isinstance(res[1], Exception) else None,
                "tmpfiles_url": res[2] if not isinstance(res[2], Exception) else None,
                "pixel_url": res[3] if not isinstance(res[3], Exception) else None,
                "dood_url": res[4] if not isinstance(res[4], Exception) else None,
                "stape_url": res[5] if not isinstance(res[5], Exception) else None,
                "filemoon_url": res[6] if not isinstance(res[6], Exception) else None,
                "mixdrop_url": res[7] if not isinstance(res[7], Exception) else None,
                "is_grouped": True
            })

            await status_msg.edit_text(f"✅ **{temp_name}** আপলোড সম্পন্ন!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add More Link", callback_data=f"lnk_yes_{uid}"), InlineKeyboardButton("🏁 Finish", callback_data=f"lnk_no_{uid}")]]))

    except Exception as e:
        if os.path.exists(local_filename): os.remove(local_filename)
        await status_msg.edit_text(f"❌ মারাত্মক এরর: {str(e)}")
