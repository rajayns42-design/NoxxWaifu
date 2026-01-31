import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

from NoxxNetwork import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, Waifuu
from NoxxNetwork import application, SUPPORT_CHAT, UPDATE_CHAT, db, LOGGER
from NoxxNetwork.modules import ALL_MODULES

# --- Variables aur Dictionaries ---
locks = {}
message_counts = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}
last_user = {}
warned_users = {}

# --- Modules Loading ---
for module_name in ALL_MODULES:
    imported_module = importlib.import_module("NoxxNetwork.modules." + module_name)

def escape_markdown(text):
    escape_chars = r'\*_`\\~>#+-=|{}.!'
    return re.sub(r'([%s])' % re.escape(escape_chars), r'\\\1', text)

# --- Message Counter Function ---
async def message_counter(update: Update, context: CallbackContext) -> None:
    if not update.effective_chat or not update.effective_user:
        return

    chat_id = str(update.effective_chat.id)
    user_id = update.effective_user.id

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    
    async with locks[chat_id]:
        chat_frequency = await user_totals_collection.find_one({'chat_id': chat_id})
        message_frequency = chat_frequency.get('message_frequency', 100) if chat_frequency else 100

        # Spam protection (Bot crash hone se bachata hai)
        if chat_id in last_user and last_user[chat_id]['user_id'] == user_id:
            last_user[chat_id]['count'] += 1
            if last_user[chat_id]['count'] >= 10:
                if user_id in warned_users and time.time() - warned_users[user_id] < 600:
                    return
                else:
                    await update.message.reply_text(f"⚠️ Don't Spam {update.effective_user.first_name}...\nYour Messages Will be ignored for 10 Minutes...")
                    warned_users[user_id] = time.time()
                    return
        else:
            last_user[chat_id] = {'user_id': user_id, 'count': 1}

        # Message counting logic
        message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

        if message_counts[chat_id] % message_frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0

# --- Send Image Function (FIXED) ---
async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id

    try:
        all_characters = await collection.find({}).to_list(length=None)
        if not all_characters:
            return

        if chat_id not in sent_characters:
            sent_characters[chat_id] = []

        if len(sent_characters[chat_id]) >= len(all_characters):
            sent_characters[chat_id] = []

        available_chars = [c for c in all_characters if c['id'] not in sent_characters[chat_id]]
        if not available_chars:
            available_chars = all_characters

        character = random.choice(available_chars)
        sent_characters[chat_id].append(character['id'])
        last_characters[chat_id] = character

        if chat_id in first_correct_guesses:
            del first_correct_guesses[chat_id]

        # FIX: Try-Except block taaki bot 'BadRequest' error se crash na ho
        caption = f"A New {character['rarity']} Character Appeared...\n/guess Character Name and add in Your Harem"
        
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode=None  # Markdown hata diya kyunki URL characters crash kar rahe the
        )
    except Exception as e:
        LOGGER.error(f"Send Photo Error: {e}")

# --- Guess Function ---
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters:
        return

    if chat_id in first_correct_guesses:
        await update.message.reply_text(f'❌️ Already Guessed By Someone.. Try Next Time Bruhh ')
        return

    user_guess = ' '.join(context.args).lower() if context.args else ''
    
    if not user_guess:
        await update.message.reply_text("Please provide a name!")
        return

    if "()" in user_guess or "&" in user_guess:
        await update.message.reply_text("Nahh You Can't use These types of words in your guess..❌️")
        return

    name_parts = last_characters[chat_id]['name'].lower().split()

    if sorted(name_parts) == sorted(user_guess.split()) or any(part == user_guess for part in name_parts):
        first_correct_guesses[chat_id] = user_id
        
        # Database optimization using upsert
        user_data = {
            'id': user_id,
            'username': update.effective_user.username,
            'first_name': update.effective_user.first_name,
        }
        
        await user_collection.update_one(
            {'id': user_id}, 
            {'$set': {'username': user_data['username'], 'first_name': user_data['first_name']}, 
             '$push': {'characters': last_characters[chat_id]}}, 
            upsert=True
        )

        await group_user_totals_collection.update_one(
            {'user_id': user_id, 'group_id': chat_id},
            {'$set': {'username': user_data['username'], 'first_name': user_data['first_name']},
             '$inc': {'count': 1}},
            upsert=True
        )

        await top_global_groups_collection.update_one(
            {'group_id': chat_id},
            {'$set': {'group_name': update.effective_chat.title},
             '$inc': {'count': 1}},
            upsert=True
        )

        keyboard = [[InlineKeyboardButton(f"See Harem", switch_inline_query_current_chat=f"collection.{user_id}")]]

        await update.message.reply_text(
            f'<b><a href="tg://user?id={user_id}">{escape(update.effective_user.first_name)}</a></b> You Guessed a New Character ✅️ \n\n'
            f'𝗡𝗔𝗠𝗘: <b>{last_characters[chat_id]["name"]}</b> \n'
            f'𝗔𝗡𝗜𝗠𝗘: <b>{last_characters[chat_id]["anime"]}</b> \n'
            f'𝗥𝗔𝗜𝗥𝗧𝗬: <b>{last_characters[chat_id]["rarity"]}</b>\n\n'
            f'This Character added in Your harem.. use /harem To see your harem', 
            parse_mode='HTML', 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text('Please Write Correct Character Name... ❌️')

# --- Favorite Function ---
async def fav(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text('Please provide Character id...')
        return

    character_id = context.args[0]
    user = await user_collection.find_one({'id': user_id})
    
    if not user or 'characters' not in user:
        await update.message.reply_text('You have not Guessed any characters yet....')
        return

    character = next((c for c in user['characters'] if str(c.get('id')) == character_id), None)
    if not character:
        await update.message.reply_text('This Character is Not In your collection')
        return

    await user_collection.update_one({'id': user_id}, {'$set': {'favorites': [character_id]}})
    await update.message.reply_text(f'Character {character["name"]} has been added to your favorites...')

# --- Main Logic ---
def main() -> None:
    application.add_handler(CommandHandler(["guess", "protecc", "collect", "grab", "hunt"], guess, block=False))
    application.add_handler(CommandHandler("fav", fav, block=False))
    # Filter commands so counter doesn't trigger on bot commands
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_counter, block=False))

    application.run_polling(drop_pending_updates=True)
    
if __name__ == "__main__":
    Waifuu.start()
    LOGGER.info("Bot started successfully!")
    main()
