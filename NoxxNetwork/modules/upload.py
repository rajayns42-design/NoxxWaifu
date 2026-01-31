import aiohttp
from pymongo import ReturnDocument
from html import escape

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from telegram.constants import ParseMode

from NoxxNetwork import application, sudo_users, collection, db, CHARA_CHANNEL_ID, SUPPORT_CHAT

# Rarity Map ko bahar define kiya taaki code saaf rahe
RARITY_MAP = {
    1: "⚪ Common", 
    2: "🟣 Rare", 
    3: "🟡 Legendary", 
    4: "🟢 Medium", 
    5: "💮 Special Edition", 
    6: "🔮 Premium Edition", 
    7: "🎗️ Supreme"
}

WRONG_FORMAT_TEXT = f"""<b>❌ Wrong Format!</b>

<code>/upload Img_url Name Anime Rarity</code>

<b>Rarity Map:</b>
1 - Common | 2 - Rare | 3 - Legendary
4 - Medium | 5 - Special | 6 - Premium | 7 - Supreme"""

async def get_next_sequence_number(sequence_name):
    sequence_collection = db.sequences
    sequence_document = await sequence_collection.find_one_and_update(
        {'_id': sequence_name}, 
        {'$inc': {'sequence_value': 1}}, 
        upsert=True,
        return_document=ReturnDocument.AFTER
    )
    return sequence_document['sequence_value']

async def upload(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users:
        await update.message.reply_text('❌ Sudo users only.')
        return

    try:
        args = context.args
        if len(args) != 4:
            await update.message.reply_text(WRONG_FORMAT_TEXT, parse_mode=ParseMode.HTML)
            return

        img_url, name, anime, rarity_idx = args[0], args[1].replace('-', ' ').title(), args[2].replace('-', ' ').title(), int(args[3])
        
        # Validations
        if rarity_idx not in RARITY_MAP:
            await update.message.reply_text("❌ Invalid rarity index (1-7).")
            return

        # URL Check (Non-blocking)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(img_url) as resp:
                    if resp.status != 200: raise Exception
        except:
            await update.message.reply_text('❌ Invalid Image URL.')
            return

        rarity = RARITY_MAP[rarity_idx]
        new_id = str(await get_next_sequence_number('character_id')).zfill(2)

        caption = (
            f'<b>✨ Character Name:</b> {escape(name)}\n'
            f'<b>🎬 Anime Name:</b> {escape(anime)}\n'
            f'<b>💠 Rarity:</b> {rarity}\n'
            f'<b>🆔 ID:</b> {new_id}'
        )

        try:
            # Channel me bhejein
            msg = await context.bot.send_photo(
                chat_id=CHARA_CHANNEL_ID,
                photo=img_url,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
            
            character = {
                'img_url': img_url,
                'name': name,
                'anime': anime,
                'rarity': rarity,
                'id': new_id,
                'message_id': msg.message_id
            }
            await collection.insert_one(character)
            await update.message.reply_text(f'✅ Character <b>{name}</b> added with ID <code>{new_id}</code>', parse_mode=ParseMode.HTML)
        
        except Exception as e:
            await update.message.reply_text(f"❌ Error while sending to channel: {e}")

    except Exception as e:
        await update.message.reply_text(f"❌ Upload failed: {e}")

async def delete(update: Update, context: CallbackContext) -> None:
    if str(update.effective_user.id) not in sudo_users: return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Give an ID to delete.")
        return

    char_id = args[0]
    character = await collection.find_one_and_delete({'id': char_id})

    if character:
        try:
            await context.bot.delete_message(chat_id=CHARA_CHANNEL_ID, message_id=character['message_id'])
            await update.message.reply_text(f'✅ ID <code>{char_id}</code> deleted from DB & Channel.', parse_mode=ParseMode.HTML)
        except:
            await update.message.reply_text(f'✅ ID <code>{char_id}</code> deleted from DB (Channel msg not found).', parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("❌ Character not found.")

# Handlers register karein
application.add_handler(CommandHandler('upload', upload, block=False))
application.add_handler(CommandHandler('delete', delete, block=False))
