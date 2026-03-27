import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# মেইন বটের ফাংশন ও ভ্যারিয়েবল ইমপোর্ট
try:
    from bot import (
        user_conversations, posts_col, DB_CHANNEL_ID, logger
    )
except ImportError:
    from __main__ import (
        user_conversations, posts_col, DB_CHANNEL_ID, logger
    )

@Client.on_message(filters.private & (filters.video | filters.document) & filters.incoming, group=-2)
async def duplicate_check_handler(client, message):
    uid = message.from_user.id
    
    if uid not in user_conversations: return
    convo = user_conversations[uid]
    if convo.get("state") != "wait_link_url": return

    file = message.video or message.document
    f_unique_id = file.file_unique_id
    temp_name = convo.get("temp_name", "File")

    # ডাটাবেসে চেক করা
    existing_post = await posts_col.find_one({"links.file_unique_id": f_unique_id})

    if existing_post:
        # মেইন বটের প্রসেস থামিয়ে দেওয়া
        message.stop_propagation()
        
        # আপলোড করার তারিখ বের করা
        upload_date = existing_post.get("updated_at", "Unknown Date")
        if not isinstance(upload_date, str):
            upload_date = upload_date.strftime("%d %b %Y")

        txt = (
            f"🎯 **ডুপ্লিকেট ফাইল পাওয়া গেছে!**\n\n"
            f"🎬 **নাম:** `{temp_name}`\n"
            f"📅 **আগের আপলোড:** `{upload_date}`\n\n"
            f"এই ফাইলটি আমাদের ডাটাবেসে অলরেডি আছে। আপনি কি আগের লিঙ্কগুলো ব্যবহার করবেন নাকি নতুন করে আপলোড করবেন?\n\n"
            f"⚠️ *দ্রষ্টব্য: পুরানো লিঙ্ক ব্যবহার করলে সময় বাঁচবে, তবে কিছু অস্থায়ী লিঙ্ক (যেমন Gofile) কাজ নাও করতে পারে।* "
        )
        
        btns = [
            [InlineKeyboardButton("✅ পুরানো লিঙ্ক ব্যবহার করুন (Instant)", callback_data=f"use_old_{f_unique_id}_{uid}")],
            [InlineKeyboardButton("🔄 নতুন করে আপলোড করুন (Fresh)", callback_data=f"reupload_now_{uid}")]
        ]
        
        await message.reply_text(txt, reply_markup=InlineKeyboardMarkup(btns), quote=True)
        return

# --- বাটন হ্যান্ডলার ---

@Client.on_callback_query(filters.regex("^use_old_"))
async def use_old_links(client, cb: CallbackQuery):
    _, _, f_id, uid = cb.data.split("_")
    uid = int(uid)
    
    if cb.from_user.id != uid:
        return await cb.answer("এটি আপনার জন্য নয়!", show_alert=True)

    convo = user_conversations.get(uid)
    if not convo: return await cb.answer("সেশন শেষ হয়ে গেছে।", show_alert=True)

    # আবার ডাটাবেস থেকে লিঙ্কগুলো নিয়ে আসা
    post = await posts_col.find_one({"links.file_unique_id": f_id})
    if not post: return await cb.answer("দুঃখিত, ডাটাবেসে ফাইলটি আর নেই।", show_alert=True)

    found_links = next((l for l in post["links"] if l.get("file_unique_id") == f_id), None)
    
    if found_links:
        convo["links"].append(found_links)
        await cb.message.edit_text("✅ পুরানো লিঙ্কগুলো সফলভাবে কপি করা হয়েছে!")
        
        # মেইন বটের পরবর্তী ধাপে নিয়ে যাওয়া
        if convo.get("post_id"): convo["state"] = "edit_mode"
        else: convo["state"] = "ask_links"
        
        await client.send_message(uid, "বাকি কাজ সম্পন্ন করুন:", 
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➕ Add Another Link", callback_data=f"lnk_yes_{uid}"), InlineKeyboardButton("🏁 Finish", callback_data=f"lnk_no_{uid}")]]))
    else:
        await cb.answer("লিঙ্ক খুঁজে পাওয়া যায়নি।")

@Client.on_callback_query(filters.regex("^reupload_now_"))
async def reupload_handler(client, cb: CallbackQuery):
    uid = int(cb.data.split("_")[-1])
    if cb.from_user.id != uid: return
    
    convo = user_conversations.get(uid)
    if not convo: return
    
    await cb.message.edit_text("🔄 **নতুন করে আপলোড শুরু হচ্ছে...**\nদয়া করে ফাইলটি আবার ফরওয়ার্ড করুন।")
    # মেইন বোটের প্রসেস অটোমেটিক চলবে যেহেতু এবার আর stop_propagation হবে না
