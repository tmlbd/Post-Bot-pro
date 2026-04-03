# plugins/multi_paste_backup.py
import __main__
import aiohttp
import io
import logging
# সরাসরি pyrogram থেকে প্রয়োজনীয় জিনিস ইমপোর্ট করছি যাতে মেইন ফাইলের এরর না আসে
from pyrogram import filters, handlers
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

# --- 🚀 উন্নত মাল্টি-সার্ভার পেস্ট লজিক ---
async def enhanced_paste_service(content):
    """এটি dpaste ফেল করলে অন্য সার্ভারে চেষ্টা করবে"""
    if not content:
        return None

    async with aiohttp.ClientSession() as session:
        # ১. dpaste.com (Primary)
        try:
            url = "https://dpaste.com/api/"
            data = {"content": content, "syntax": "html", "expiry_days": 14}
            async with session.post(url, data=data, timeout=12) as resp:
                if resp.status in [200, 201]:
                    link = await resp.text()
                    return link.strip()
        except:
            logger.error("dpaste failed, switching to backup...")

        # ২. paste.rs (Backup 1)
        try:
            async with session.post("https://paste.rs", data=content.encode('utf-8'), timeout=12) as resp:
                if resp.status in [200, 201]:
                    return await resp.text()
        except:
            logger.error("paste.rs failed, switching to backup...")

        # ৩. spaceb.in (Backup 2)
        try:
            payload = {"content": content, "extension": "html"}
            async with session.post("https://spaceb.in/api/v1/documents", json=payload, timeout=12) as resp:
                if resp.status in [200, 201]:
                    res_json = await resp.json()
                    return f"https://spaceb.in/{res_json['payload']['id']}"
        except:
            logger.error("spaceb.in failed.")

    return None

# --- 🛠️ প্যাচ করা হ্যান্ডলার লজিক ---
async def patched_get_code(client, cb):
    try:
        _, _, uid = cb.data.rsplit("_", 2)
        uid = int(uid)
    except:
        return
        
    # মেইন ফাইলের কনভারসেশন ডেটা এক্সেস করা
    data = __main__.user_conversations.get(uid)
    if not data or "final" not in data:
        return await cb.answer("❌ সেশন পাওয়া যায়নি! আবার পোস্ট করুন।", show_alert=True)
    
    await cb.answer("⏳ জেনারেট হচ্ছে (ব্যাকআপ সার্ভার ব্যবহার করা হচ্ছে)...", show_alert=False)
    
    html_code = data["final"]["html"]
    link = await enhanced_paste_service(html_code)
    
    if link:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 ওপেন কোড লিংক", url=link)],
            [InlineKeyboardButton("📁 ফাইল হিসেবে নিন", callback_data=f"send_file_only_{uid}")]
        ])
        await cb.message.reply_text(
            f"✅ **কোড রেডি (Backup System)!**\n\n"
            f"🔗 **লিংক:** `{link}`\n\n"
            f"💡 _লিংক কাজ না করলে নিচের বাটন থেকে ফাইল ডাউনলোড করুন।_",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    else:
        # সব সার্ভার ফেল করলে অটো ফাইল পাঠানো
        file = io.BytesIO(html_code.encode('utf-8'))
        file.name = f"blogger_code_{uid}.txt"
        await client.send_document(
            cb.message.chat.id, 
            file, 
            caption="⚠️ **সব পেস্ট সার্ভার ডাউন!**\n\nএখানে আপনার পোস্টের কোড ফাইল আকারে দেওয়া হলো।"
        )

# --- 📁 ফাইল হ্যান্ডলার ---
async def send_file_handler(client, cb):
    uid = int(cb.data.split("_")[-1])
    data = __main__.user_conversations.get(uid)
    if data and "final" in data:
        file = io.BytesIO(data["final"]["html"].encode('utf-8'))
        file.name = "post_code.html"
        await client.send_document(cb.message.chat.id, file, caption="📄 আপনার ব্লগার পোস্টের HTML কোড।")
        await cb.answer("ফাইল পাঠানো হয়েছে!")

# ==========================================================
# 🔥 প্লাগইন রেজিস্ট্রেশন
# ==========================================================
async def register(bot):
    # মেইন ফাইলের create_paste_link ফাংশন বদলে দেওয়া
    __main__.create_paste_link = enhanced_paste_service
    
    # নতুন হ্যান্ডলার গ্রুপ -১ এ রেজিস্টার করা যাতে এটি মেইন কোডের আগে কাজ করে
    bot.add_handler(
        handlers.CallbackQueryHandler(patched_get_code, filters.regex("^get_code_")),
        group=-1
    )
    
    # ফাইল পাঠানোর হ্যান্ডলার
    bot.add_handler(
        handlers.CallbackQueryHandler(send_file_handler, filters.regex("^send_file_only_")),
        group=-1
    )
    
    print("✅ Multi-Paste Backup Plugin: High Priority Patch Applied!")
