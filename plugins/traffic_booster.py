import os
import urllib.parse
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# আপনার ওয়েবসাইটের লিঙ্ক
YOUR_WEBSITE_URL = "https://banglaflix4k.blogspot.com" 

# ডাটাবেস ইমপোর্ট
try:
    from bot import posts_col, user_conversations
except ImportError:
    from __main__ import posts_col, user_conversations

# 🔥 গ্রুপ নম্বর -১০ (সবার আগে মুভি চেক করবে)
@Client.on_message(filters.private & filters.text & filters.incoming, group=-10)
async def website_traffic_handler(client, message):
    uid = message.from_user.id
    query = message.text.strip()
    
    # ১. কমান্ড (যেমন /start, /post) হলে এটি কাজ করবে না
    if query.startswith("/"):
        return

    # ২. ইউজার যদি মুভি পোস্ট করার মাঝপথে থাকে, তবে এটি ডিস্টার্ব করবে না
    if uid in user_conversations:
        return

    # ৩. অন্তত ৩ অক্ষরের মুভির নাম হতে হবে (ছোট টেক্সট ইগনোর করবে)
    if len(query) < 3:
        return

    # ৪. অন্য সব প্লাগিনকে এই মেসেজটি প্রসেস করতে বাধা দিবে (Stop Propagation)
    message.stop_propagation()

    # ৫. ডাটাবেসে মুভিটি আছে কিনা চেক করা
    post = await posts_col.find_one({
        "$or": [
            {"details.title": {"$regex": query, "$options": "i"}},
            {"details.name": {"$regex": query, "$options": "i"}}
        ]
    })

    if post:
        # ✅ মুভি পাওয়া গেলে ওয়েবসাইটের কার্ড দিবে
        title = post['details'].get('title') or post['details'].get('name')
        year = str(post['details'].get('release_date') or post['details'].get('first_air_date') or "----")[:4]
        rating = post['details'].get('vote_average', 0)
        
        # ব্লগার সার্চ ইউআরএল তৈরি
        exact_search_term = f"{title} {year}"
        search_query = urllib.parse.quote(exact_search_term)
        final_website_link = f"{YOUR_WEBSITE_URL}/search?q={search_query}"

        text = (
            f"🎬 **{title} ({year})**\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⭐ **রেটিং:** {rating}/10\n\n"
            f"✅ মুভিটি আমাদের ওয়েবসাইটে পাওয়া গেছে!\n\n"
            f"নিচের বাটনে ক্লিক করে সরাসরি ওয়েবসাইট থেকে ডাউনলোড করে নিন। 👇"
        )
        
        btns = [[InlineKeyboardButton("🌐 সরাসরি ওয়েবসাইট থেকে দেখুন", url=final_website_link)]]
        
        await message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns), quote=True)
        
    else:
        # ❌ মুভি না পাওয়া গেলে ইউজারকে ওয়ার্নিং দিবে
        not_found_text = (
            f"🔍 **দুঃখিত!**\n\n"
            f"আপনার সার্চ করা মুভি: **'{query}'**\n"
            f"আমাদের ডাটাবেসে বা ওয়েবসাইটে এখনও আপলোড করা হয়নি। 😔\n\n"
            f"💡 **টিপস:** মুভির নামের বানান ঠিকভাবে লিখে পুনরায় ট্রাই করুন অথবা মুভিটির জন্য এডমিনকে রিকোয়েস্ট করুন।"
        )
        
        btns = [
            [InlineKeyboardButton("🏠 ওয়েবসাইটের হোমপেজে যান", url=YOUR_WEBSITE_URL)],
            [InlineKeyboardButton("💬 মুভি রিকোয়েস্ট করুন", url="https://t.me/CineZoneBDBot")] # <--- আপনার ইউজারনেম দিন
        ]
        
        await message.reply_text(not_found_text, reply_markup=InlineKeyboardMarkup(btns), quote=True)
