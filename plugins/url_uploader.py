import os
import time
import asyncio
import aiohttp
import re
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

# প্রফেশনাল ব্রাউজার হেডার
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def get_progress_bar(percent):
    """একটি সুন্দর প্রোগ্রেস বার তৈরি করে"""
    done = int(percent / 10)
    return "🟢" * done + "⚪" * (10 - done)

async def progress_callback(current, total, status_msg, start_time, action="ডাউনলোড"):
    """লাইভ প্রোগ্রেস আপডেট করার ফাংশন"""
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

        bar = get_progress_bar(percent)
        
        text = (
            f"🚀 **ফাইল {action} হচ্ছে...**\n\n"
            f"📊 {bar} **{percent:.1f}%**\n"
            f"💾 {hbytes(current)} / {hbytes(total)}\n"
            f"⚡ স্পিড: {hbytes(speed)}/s\n"
            f"⏱️ সময়: {int(now - start_time)}s"
        )
        try:
            await status_msg.edit_text(text)
        except:
            pass

async def download_worker(url, file_path, status_msg):
    """ইউআরএল থেকে ফাইল ডাউনলোড করার মূল ইঞ্জিন"""
    start_time = time.time()
    if os.path.exists(file_path): os.remove(file_path)
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            async with session.get(url, timeout=None, allow_redirects=True) as resp:
                if resp.status != 200:
                    return False, f"সার্ভার এরর: {resp.status} (লিংকটি হয়তো ডেড)"
                
                # কন্টেন্ট টাইপ চেক (ভিডিও কি না)
                ctype = resp.headers.get('Content-Type', '').lower()
                if 'text' in ctype or 'html' in ctype:
                    return False, "এটি সরাসরি ফাইল লিংক নয়, এটি একটি ওয়েব পেজ।"

                total_size = int(resp.headers.get('content-length', 0))
                if total_size == 0:
                    return False, "ফাইলের সাইজ পাওয়া যায়নি। লিংকটি অবৈধ হতে পারে।"

                downloaded = 0
                with open(file_path, 'wb') as f:
                    async for chunk in resp.content.iter_chunked(1024*1024): # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            await progress_callback(downloaded, total_size, status_msg, start_time, "ডাউনলোড")
                
                return True, "Success"
        except Exception as e:
            return False, f"লিংক এরর: {str(e)}"

@Client.on_message(filters.private & filters.text & filters.incoming, group=-1)
async def url_upload_handler(client, message):
    uid = message.from_user.id
    text = message.text.strip()
    
    # শুধুমাত্র পোস্ট মেকিং এর লিংক দেওয়ার স্টেজে কাজ করবে
    if uid not in user_conversations:
        return
    
    convo = user_conversations[uid]
    if convo.get("state") != "wait_link_url" or not text.startswith("http"):
        return

    # মেইন বোটের প্রসেস থামিয়ে দেওয়া
    message.stop_propagation()

    temp_name = convo.get("temp_name", "Remote File")
    status_msg = await message.reply_text("🔍 **লিংকটি পরীক্ষা করা হচ্ছে...**", quote=True)
    
    # লোকাল ফাইল নেম (ভিডিও হিসেবে ডিফল্ট)
    local_filename = f"remote_{uid}_{int(time.time())}.mp4"
    
    try:
        async with upload_semaphore:
            # ডাউনলোড শুরু
            success, error_msg = await download_worker(text, local_filename, status_msg)
            
            if not success:
                # যদি সরাসরি ডাউনলোড না হয়, তবে এরর মেসেজ দিয়ে সাধারণ লিংক হিসেবে সেভ করবে
                await status_msg.edit_text(f"❌ **ডাউনলোড করা সম্ভব হয়নি!**\n\n**কারণ:** {error_msg}\n\nএটি এখন সাধারণ লিংক হিসেবে সেভ হবে।")
                convo["links"].append({"label": temp_name, "url": text, "is_grouped": False})
                
                # পরবর্তী স্টেপে নিয়ে যাওয়া
                if convo.get("post_id"): convo["state"] = "edit_mode"
                else: convo["state"] = "ask_links"
                
                await message.reply_text("✅ মুভি পোস্টের কাজ চালিয়ে যান:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Another Link", callback_data=f"lnk_yes_{uid}"), InlineKeyboardButton("🏁 Finish", callback_data=f"lnk_no_{uid}")]]))
                return

            # ডাউনলোড সফল হলে আপলোড প্রসেস শুরু
            await status_msg.edit_text("⏳ **ডাউনলোড সফল! এখন মাল্টি-সার্ভার আপলোড শুরু হচ্ছে...**")

            # ১. টেলিগ্রাম ডাটাবেসে সেভ (টেলিগ্রামের জন্য প্রোগ্রেস বার কাজ করে না কপি মেসেজে, তাই সরাসরি মেসেজ দেওয়া হলো)
            await status_msg.edit_text("📡 **১/৩: টেলিগ্রাম সার্ভারে ব্যাকআপ হচ্ছে...**")
            tg_msg = await client.send_document(
                chat_id=DB_CHANNEL_ID, 
                document=local_filename,
                caption=f"🎥 **Remote Uploaded:** {temp_name}"
            )
            bot_username = (await client.get_me()).username
            tg_link = f"https://t.me/{bot_username}?start=get-{tg_msg.id}"

            # ২. মিরর সার্ভারে আপলোড (প্যারালাল)
            await status_msg.edit_text("📡 **২/৩: এক্সটার্নাল মিরর সার্ভারে মিররিং হচ্ছে...**\n_(GoFile, Dood, MixDrop, Streamtape etc.)_")
            
            # সার্ভারগুলোতে এক সাথে আপলোড শুরু হবে (প্যারালাল)
            mirror_results = await asyncio.gather(
                upload_to_gofile(local_filename), upload_to_fileditch(local_filename), 
                upload_to_tmpfiles(local_filename), upload_to_pixeldrain(local_filename), 
                upload_to_doodstream(local_filename), upload_to_streamtape(local_filename),
                upload_to_filemoon(local_filename), upload_to_mixdrop(local_filename), 
                return_exceptions=True
            )

            # লোকাল ফাইল ডিলিট করে স্টোরেজ খালি করা
            if os.path.exists(local_filename): os.remove(local_filename)

            # সব লিংক ডাটাবেসে অ্যাড করা
            convo["links"].append({
                "label": temp_name, "tg_url": tg_link, 
                "gofile_url": mirror_results[0] if not isinstance(mirror_results[0], Exception) else None,
                "fileditch_url": mirror_results[1] if not isinstance(mirror_results[1], Exception) else None,
                "tmpfiles_url": mirror_results[2] if not isinstance(mirror_results[2], Exception) else None,
                "pixel_url": mirror_results[3] if not isinstance(mirror_results[3], Exception) else None,
                "dood_url": mirror_results[4] if not isinstance(mirror_results[4], Exception) else None,
                "stape_url": mirror_results[5] if not isinstance(mirror_results[5], Exception) else None,
                "filemoon_url": mirror_results[6] if not isinstance(mirror_results[6], Exception) else None,
                "mixdrop_url": mirror_results[7] if not isinstance(mirror_results[7], Exception) else None,
                "is_grouped": True
            })

            # সম্পন্ন মেসেজ
            final_text = f"✅ **{temp_name}** সফলভাবে ডাউনলোড ও মিরর করা হয়েছে!"
            if convo.get("post_id"):
                convo["state"] = "edit_mode"
                await status_msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add More Link", callback_data=f"add_lnk_edit_{uid}"), InlineKeyboardButton("✅ Finish", callback_data=f"gen_edit_{uid}")]]))
            else:
                convo["state"] = "ask_links"
                await status_msg.edit_text(final_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add More Link", callback_data=f"lnk_yes_{uid}"), InlineKeyboardButton("🏁 Finish", callback_data=f"lnk_no_{uid}")]])
            )

    except Exception as e:
        logger.error(f"Ultimate Uploader Error: {e}")
        if os.path.exists(local_filename): os.remove(local_filename)
        await status_msg.edit_text(f"❌ **মারাত্মক এরর:** `{str(e)}`")
