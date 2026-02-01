import importlib
import time
import random
import re
import asyncio
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters
from telegram.constants import ParseMode

from NoxxNetwork import collection, top_global_groups_collection, group_user_totals_collection, user_collection, user_totals_collection, Waifuu
from NoxxNetwork import application, LOGGER
from NoxxNetwork.modules import ALL_MODULES

# --- Global States ---
locks = {}
message_counts = {}
last_characters = {}
sent_characters = {}
first_correct_guesses = {}

# --- Modules Loading ---
for module_name in ALL_MODULES:
    importlib.import_module("NoxxNetwork.modules." + module_name)

# --- Message Counter ---
async def message_counter(update: Update, context: CallbackContext) -> None:
    if not update.effective_chat: return
    chat_id = str(update.effective_chat.id)

    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    
    async with locks[chat_id]:
        chat_data = await user_totals_collection.find_one({'chat_id': chat_id})
        frequency = chat_data.get('message_frequency', 100) if chat_data else 100

        message_counts[chat_id] = message_counts.get(chat_id, 0) + 1

        if message_counts[chat_id] % frequency == 0:
            await send_image(update, context)
            message_counts[chat_id] = 0

# --- Send Image Logic ---
async def send_image(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    try:
        all_chars = await collection.find({}).to_list(length=None)
        if not all_chars: return

        character = random.choice(all_chars)
        last_characters[chat_id] = character
        first_correct_guesses.pop(chat_id, None)

        caption = f"<b>A New Character Appeared!</b>\n\n/guess Name and add it to your harem."
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=character['img_url'],
            caption=caption,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Spawn Error: {e}")

# --- Guess Logic ---
async def guess(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if chat_id not in last_characters or chat_id in first_correct_guesses:
        return

    user_guess = ' '.join(context.args).lower().strip()
    if not user_guess: return

    correct_name = last_characters[chat_id]['name'].lower()
    
    # Simple name matching logic
    if user_guess == correct_name or any(part == user_guess for part in correct_name.split()):
        first_correct_guesses[chat_id] = user_id
        char = last_characters[chat_id]

        # Update User Database
        await user_collection.update_one(
            {'id': user_id}, 
            {'$push': {'characters': char}, '$set': {'first_name': update.effective_user.first_name}}, 
            upsert=True
        )

        await update.message.reply_text(
            f'✅ <b>{escape(update.effective_user.first_name)}</b>, You guessed it!\n'
            f'Name: <b>{char["name"]}</b>\n'
            f'Anime: <b>{char["anime"]}</b>',
            parse_mode=ParseMode.HTML
        )

# --- Start Bot ---
def main():
    application.add_handler(CommandHandler(["guess", "collect"], guess, block=False))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_counter, block=False))
    
    LOGGER.info("Bot is starting...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    Waifuu.start()
    main()
