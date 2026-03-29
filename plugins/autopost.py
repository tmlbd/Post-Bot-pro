import __main__
import asyncio
import re
import aiohttp
import xml.etree.ElementTree as ET
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# মেইন ফাইল থেকে ডাটাবেস কালেকশন নেওয়া
db = __main__.db
user_setup_col = db["user_autopost_configs"]

async def register(bot):
    print("🎬 Autopost Plugin: Active and Ready!")

    # --- ১. সেটিংস চেক করার কমান্ড ---
    @bot.on_message(filters.command("myconfig") & filters.private)
    async def check_config(client, message):
        uid = message.from_user.id
        config = await user_setup_col.find_one({"user_id": uid})
        if config:
            await message.reply_text(
                f"⚙️ **আপনার বর্তমান সেটিংস:**\n\n"
                f"📢 চ্যানেল: `{config.get('channel')}`\n"
                f"🌐 ফিড: {config.get('feed')}\n"
                f"🎥 টিউটোরিয়াল: {config.get('tutorial')}"
            )
        else:
            await message.reply_text("❌ আপনার কোনো সেটিংস পাওয়া যায়নি। `/setup` করুন।")

    # --- ২. সেটআপ কমান্ড ---
    @bot.on_message(filters.command("setup") & filters.private)
    async def setup_handler(client, message):
        print(f"DEBUG: Setup triggered by {message.from_user.id}")
        try:
            parts = message.text.split(None, 3)
            if len(parts) < 4:
                return await message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/setup @channel feed_url tutorial_url`")
            
            uid = message.from_user.id
            channel, feed_url, tutorial = parts[1], parts[2], parts[3]

            await user_setup_col.update_one(
                {"user_id": uid},
                {"$set": {"channel": channel, "feed": feed_url, "tutorial": tutorial, "last_post_id": None}},
                upsert=True
            )
            await message.reply_text("✅ সেটিংস সফলভাবে সেভ হয়েছে! এখন নতুন পোস্টের জন্য অপেক্ষা করুন।")
        except Exception as e:
            await message.reply_text(f"❌ এরর: {e}")

    # --- ৩. অটো মনিটর লুপ ---
    async def monitor_feeds():
        while True:
            try:
                configs = await user_setup_col.find({}).to_list(None)
                async with aiohttp.ClientSession() as session:
                    for config in configs:
                        try:
                            f_url, l_id = config.get("feed"), config.get("last_post_id")
                            target_chat, tutorial, uid = config.get("channel"), config.get("tutorial"), config.get("user_id")

                            async with session.get(f_url, timeout=10) as resp:
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
                                    
                                    caption = (f"🎬 **NEW UPDATE: {title}**\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
                                               f"🎭 **Genre:** Movie | Series\n"
                                               f"🔊 **Audio:** Dual Audio\n"
                                               f"💎 **Quality:** 480p | 720p | 1080p\n\n"
                                               f"━━━━━━━━━━━━━━━━━━━━━━\n📥 **Watch & Download Now 👇**")
                                    
                                    btns = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Watch / Download", url=link)],
                                                                [InlineKeyboardButton("📽️ How to Download", url=tutorial)]])
                                    
                                    if poster: await bot.send_photo(target_chat, poster, caption=caption, reply_markup=btns)
                                    else: await bot.send_message(target_chat, caption, reply_markup=btns)
                                    
                                    await user_setup_col.update_one({"user_id": uid}, {"$set": {"last_post_id": p_id}})
                        except: continue
            except: pass
            await asyncio.sleep(300)

    asyncio.create_task(monitor_feeds())
