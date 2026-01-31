import re
import time
from html import escape
from cachetools import TTLCache
from pymongo import ASCENDING

from telegram import Update, InlineQueryResultPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import InlineQueryHandler, CallbackContext
from NoxxNetwork import user_collection, collection, application, db

# Indexes (Ensure these are created only once)
def setup_indexes():
    db.characters.create_index([('id', ASCENDING)])
    db.characters.create_index([('anime', ASCENDING)])
    db.user_collection.create_index([('id', ASCENDING)])

# Caching for better speed
all_characters_cache = TTLCache(maxsize=1, ttl=3600)
user_collection_cache = TTLCache(maxsize=5000, ttl=60)

async def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    results = []

    # 1. User Collection Search (collection.USERID)
    if query.startswith('collection.'):
        parts = query.split(' ', 1)
        first_part = parts[0].split('.')
        user_id_str = first_part[1] if len(first_part) > 1 else ""
        search_query = parts[1] if len(parts) > 1 else ""

        if user_id_str.isdigit():
            user_id = int(user_id_str)
            user = user_collection_cache.get(user_id_str)
            if not user:
                user = await user_collection.find_one({'id': user_id})
                if user:
                    user_collection_cache[user_id_str] = user

            if user and 'characters' in user:
                # Unique characters based on ID
                all_characters = list({v['id']: v for v in user['characters']}.values())
                
                if search_query:
                    clean_query = re.escape(search_query) # Safe search
                    regex = re.compile(clean_query, re.IGNORECASE)
                    all_characters = [c for c in all_characters if regex.search(c['name']) or regex.search(c['anime'])]
            else:
                all_characters = []
        else:
            all_characters = []

    # 2. Global Character Search
    else:
        if query:
            clean_query = re.escape(query)
            regex = re.compile(clean_query, re.IGNORECASE)
            all_characters = await collection.find({"$or": [{"name": regex}, {"anime": regex}]}).to_list(length=100)
        else:
            if 'all' in all_characters_cache:
                all_characters = all_characters_cache['all']
            else:
                all_characters = await collection.find({}).to_list(length=100)
                all_characters_cache['all'] = all_characters

    # Pagination logic (Show 50 per page)
    current_batch = all_characters[offset:offset+50]
    next_offset = str(offset + 50) if len(all_characters) > offset + 50 else ""

    for character in current_batch:
        char_id = character['id']
        char_name = character['name']
        char_anime = character['anime']
        char_rarity = character.get('rarity', 'Unknown')
        img_url = character.get('img_url', '')

        if query.startswith('collection.'):
            # User specific counts
            user_char_count = sum(1 for c in user['characters'] if c['id'] == char_id)
            caption = (
                f"<b>Look At <a href='tg://user?id={user['id']}'>{escape(user.get('first_name', 'User'))}</a>'s Character</b>\n\n"
                f"🌸: <b>{escape(char_name)} (x{user_char_count})</b>\n"
                f"🏖️: <b>{escape(char_anime)}</b>\n"
                f"✨: <b>{char_rarity}</b>\n"
                f"🆔️: <code>{char_id}</code>"
            )
        else:
            caption = (
                f"<b>Look At This Character !!</b>\n\n"
                f"🌸: <b>{escape(char_name)}</b>\n"
                f"🏖️: <b>{escape(char_anime)}</b>\n"
                f"✨: <b>{char_rarity}</b>\n"
                f"🆔️: <code>{char_id}</code>"
            )

        results.append(
            InlineQueryResultPhoto(
                id=f"{char_id}_{time.time()}_{random.randint(100,999)}",
                photo_url=img_url,
                thumbnail_url=img_url,
                caption=caption,
                parse_mode='HTML'
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)

# Initialize indexes on startup
setup_indexes()
application.add_handler(InlineQueryHandler(inlinequery, block=False))
