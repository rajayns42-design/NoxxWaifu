from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler
from itertools import groupby
import math
import random
from html import escape 
from NoxxNetwork import collection, user_collection, application

async def harem(update: Update, context: CallbackContext, page=0) -> None:
    # Query ya Message handle karne ke liye
    is_callback = update.callback_query is not None
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    user = await user_collection.find_one({'id': user_id})
    if not user or not user.get('characters'):
        msg = '<b>You Have Not Guessed any Characters Yet..</b>'
        if is_callback:
            await update.callback_query.answer("Empty Harem!", show_alert=True)
        else:
            await update.message.reply_text(msg, parse_mode='HTML')
        return

    # Characters sorting aur grouping
    all_characters = user['characters']
    all_characters.sort(key=lambda x: (x.get('anime', 'Unknown'), x.get('id', '')))

    # Count of each character
    character_counts = {k: len(list(v)) for k, v in groupby(all_characters, key=lambda x: x['id'])}
    
    # Unique list for pagination
    unique_characters = list({c['id']: c for c in all_characters}.values())
    
    total_pages = math.ceil(len(unique_characters) / 15)
    if page < 0 or page >= total_pages: page = 0  

    harem_message = f"<b>{escape(update.effective_user.first_name)}'s Harem</b>\n"
    harem_message += f"✨ <b>Total Characters:</b> {len(all_characters)}\n"
    harem_message += f"📖 <b>Page:</b> {page+1}/{total_pages}\n"
    harem_message += "━━━━━━━━━━━━━━━━━━━━\n"

    # Current page characters
    current_chars = unique_characters[page*15:(page+1)*15]
    
    # Group by anime
    for anime, group in groupby(current_chars, key=lambda x: x.get('anime', 'Unknown')):
        # Group list conversion to avoid iterator issues
        group_list = list(group)
        total_in_anime = await collection.count_documents({"anime": anime})
        harem_message += f'\n🎬 <b>{anime}</b> ({len(group_list)}/{total_in_anime})\n'
        
        for char in group_list:
            count = character_counts.get(char['id'], 1)
            harem_message += f'├ {char["id"]} {char["name"]} ×{count}\n'

    # Keyboard
    keyboard = [[InlineKeyboardButton(f"See Collection ({len(all_characters)})", switch_inline_query_current_chat=f"collection.{user_id}")]]

    if total_pages > 1:
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem:{page-1}:{user_id}"))
        if page < total_pages - 1: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem:{page+1}:{user_id}"))
        keyboard.append(nav)

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Image logic (Fav or Random)
    fav_id = user.get('favorites', [None])[0]
    fav_char = next((c for c in all_characters if c['id'] == fav_id), None) if fav_id else None
    display_char = fav_char if fav_char else random.choice(all_characters)
    img_url = display_char.get('img_url')

    try:
        if is_callback:
            # Sirf caption update karein taaki image baar-baar load na ho
            await update.callback_query.edit_message_caption(
                caption=harem_message, 
                reply_markup=reply_markup, 
                parse_mode='HTML'
            )
        else:
            if img_url:
                await update.message.reply_photo(photo=img_url, caption=harem_message, reply_markup=reply_markup, parse_mode='HTML')
            else:
                await update.message.reply_text(harem_message, reply_markup=reply_markup, parse_mode='HTML')
    except Exception as e:
        # Agar caption same ho toh Telegram error deta hai, use ignore karein
        if "Message is not modified" not in str(e):
            print(f"Harem Error: {e}")

async def harem_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    _, page, user_id = query.data.split(':')
    
    if query.from_user.id != int(user_id):
        await query.answer("❌ This is not your harem!", show_alert=True)
        return

    await harem(update, context, page=int(page))

# Handlers
application.add_handler(CommandHandler(["harem", "collection"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern='^harem:', block=False))
