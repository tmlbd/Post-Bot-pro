import __main__
import asyncio
import re
import aiohttp
import xml.etree.ElementTree as ET
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ডাটাবাস কানেকশন
db = __main__.db
user_setup_col = db["user_autopost_configs"]

async def register(bot):
    # লগে দেখাবে যে এটি সচল
    print("🎬 Autopost Plugin: High Priority Active!")

    # --- ১. সেটিংস চেক করা (Priority Group -1) ---
    @bot.on_message(filters.command("myconfig") & filters.private, group=-1)
    async def check_config(client, message):
        uid = message.from_user.id
        config = await user_setup_col.find_one({"user_id": uid})
        if config:
            await message.reply_text(
                f"⚙️ **Config found for {message.from_user.first_name}:**\n\n"
                f"📢 Channel: `{config.get('channel')}`\n"
                f"🌐 Feed: {config.get('feed')}\n"
                f"🎥 Tutorial: {config.get('tutorial')}"
            )
        else:
            await message.reply_text("❌ No config found! Use `/setup` first.")

    # --- ২. সেটআপ কমান্ড (Priority Group -1) ---
    @bot.on_message(filters.command("setup") & filters.private, group=-1)
    async def setup_handler(client, message):
        try:
            parts = message.text.split(None, 3)
            if len(parts) < 4:
                return await message.reply_text("⚠️ **Format:** `/setup @channel feed_url tutorial_url`")
            
            uid = message.from_user.id
            channel, feed, tutorial = parts[1], parts[2], parts[3]

            await user_setup_col.update_one(
                {"user_id": uid},
                {"$set": {"channel": channel, "feed": feed, "tutorial": tutorial, "last_post_id": None}},
                upsert=True
            )
            await message.reply_text("✅ **Success!** Your website is now linked to your channel.")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    # --- ৩. অটো মনিটর লুপ ---
    async def monitor_feeds():
        while True:
            try:
                configs = await user_setup_col.find({}).to_list(None)
                async with aiohttp.ClientSession() as session:
                    for config in configs:
                        try:
                            f_url = config.get("feed")
                            l_id = config.get("last_post_id")
                            target_chat = config.get("channel")
                            tutorial = config.get("tutorial")
                            uid = config.get("user_id")

                            async with session.get(f_url, timeout=15) as resp:
                                if resp.status != 200: continue
                                xml_data = await resp.text()
                                root = ET.fromstring(xml_data)
                                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                                entries = root.findall('atom:entry', ns)

                                if not entries: continue
                                latest = entries[0]
                                p_id = latest.find('atom:id', ns).text

                                if p_id != l_id:
                                    title = latest.find('atom:title', ns).text
                                    link = latest.find('atom:link[@rel="alternate"]', ns).attrib['href']
                                    content = latest.find('atom:content', ns).text
                                    img_match = re.search(r'<img.*?src="(.*?)"', content)
                                    poster = img_match.group(1) if img_match else None
                                    
                                    caption = (f"🎬 **NEW POST:** {title}\n"
                                               f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                                               f"📥 **ডাউনলোড করতে নিচের বাটনে ক্লিক করুন 👇**")
                                    
                                    btns = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Download Link", url=link)],
                                                                [InlineKeyboardButton("📽️ How to Download", url=tutorial)]])
                                    
                                    if poster: await bot.send_photo(target_chat, poster, caption=caption, reply_markup=btns)
                                    else: await bot.send_message(target_chat, caption, reply_markup=btns)
                                    
                                    await user_setup_col.update_one({"user_id": uid}, {"$set": {"last_post_id": p_id}})
                        except: continue
            except: pass
            await asyncio.sleep(300) # ৫ মিনিট পর পর চেক

    asyncio.create_task(monitor_all_feeds())

# লক্ষ্য করুন: আমি আগের monitor_feeds এর নাম monitor_all_feeds করেছি যাতে কনফ্লিক্ট না হয়।
