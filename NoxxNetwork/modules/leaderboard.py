import os
import random
import html
import asyncio

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from NoxxNetwork import (application, PHOTO_URL, OWNER_ID,
                    user_collection, top_global_groups_collection, 
                    group_user_totals_collection)

from NoxxNetwork import sudo_users as SUDO_USERS 

# --- Global Leaderboard (Top Groups) ---
async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    try:
        cursor = top_global_groups_collection.aggregate([
            {"$project": {"group_name": 1, "count": 1}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ])
        leaderboard_data = await cursor.to_list(length=10)

        leaderboard_message = "<b>TOP 10 GROUPS WHO GUESSED MOST CHARACTERS</b>\n\n"

        for i, group in enumerate(leaderboard_data, start=1):
            # Safe HTML escape
            group_name = html.escape(group.get('group_name', 'Unknown'))
            if len(group_name) > 15:
                group_name = group_name[:15] + '...'
            count = group.get('count', 0)
            leaderboard_message += f'{i}. <b>{group_name}</b> ➾ <b>{count}</b>\n'
        
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# --- Chat Top (Top Users in current group) ---
async def ctop(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    try:
        cursor = group_user_totals_collection.aggregate([
            {"$match": {"group_id": chat_id}},
            {"$project": {"username": 1, "first_name": 1, "character_count": "$count"}},
            {"$sort": {"character_count": -1}},
            {"$limit": 10}
        ])
        leaderboard_data = await cursor.to_list(length=10)

        leaderboard_message = "<b>TOP 10 USERS IN THIS GROUP..</b>\n\n"

        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))

            if len(first_name) > 15:
                first_name = first_name[:15] + '...'
            character_count = user.get('character_count', 0)
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'
        
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text("Leaderboard is empty or error occurred.")

# --- Global User Leaderboard ---
async def leaderboard(update: Update, context: CallbackContext) -> None:
    try:
        cursor = user_collection.aggregate([
            {"$project": {"username": 1, "first_name": 1, "character_count": {"$size": {"$ifNull": ["$characters", []]}}}},
            {"$sort": {"character_count": -1}},
            {"$limit": 10}
        ])
        leaderboard_data = await cursor.to_list(length=10)

        leaderboard_message = "<b>TOP 10 USERS WITH MOST CHARACTERS</b>\n\n"

        for i, user in enumerate(leaderboard_data, start=1):
            username = user.get('username', 'Unknown')
            first_name = html.escape(user.get('first_name', 'Unknown'))

            if len(first_name) > 15:
                first_name = first_name[:15] + '...'
            character_count = user.get('character_count', 0)
            leaderboard_message += f'{i}. <a href="https://t.me/{username}"><b>{first_name}</b></a> ➾ <b>{character_count}</b>\n'
        
        photo_url = random.choice(PHOTO_URL)
        await update.message.reply_photo(photo=photo_url, caption=leaderboard_message, parse_mode='HTML')
    except Exception as e:
        await update.message.reply_text("Error loading leaderboard.")

# --- Rescue Data: Users List ---
async def send_users_document(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID and str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text('Only for Sudo users...')
        return
    
    await update.message.reply_text("Fetching users list... please wait.")
    
    cursor = user_collection.find({})
    user_list = "--- USER LIST ---\n"
    async for user in cursor:
        name = user.get('first_name', 'Unknown')
        uid = user.get('id', 'N/A')
        user_list += f"ID: {uid} | Name: {name}\n"
    
    with open('users.txt', 'w', encoding='utf-8') as f:
        f.write(user_list)
    
    with open('users.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, caption="Bot User Database Rescue")
    os.remove('users.txt')

# --- Rescue Data: Groups List ---
async def send_groups_document(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID and str(update.effective_user.id) not in SUDO_USERS:
        await update.message.reply_text('Only for Sudo users...')
        return

    cursor = top_global_groups_collection.find({})
    group_list = "--- GROUP LIST ---\n"
    async for group in cursor:
        gname = group.get('group_name', 'Unknown')
        gid = group.get('group_id', 'N/A')
        group_list += f"ID: {gid} | Group: {gname}\n"
    
    with open('groups.txt', 'w', encoding='utf-8') as f:
        f.write(group_list)
    
    with open('groups.txt', 'rb') as f:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=f, caption="Bot Group Database Rescue")
    os.remove('groups.txt')

# --- Stats Command ---
async def stats(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("You are not authorized.")
        return

    user_count = await user_collection.count_documents({})
    group_count = len(await group_user_totals_collection.distinct('group_id'))

    await update.message.reply_text(f'📊 **Bot Stats**\n\nTotal Users: {user_count}\nTotal Groups: {group_count}', parse_mode='Markdown')

# --- Handlers ---
application.add_handler(CommandHandler('ctop', ctop, block=False))
application.add_handler(CommandHandler('stats', stats, block=False))
application.add_handler(CommandHandler('TopGroups', global_leaderboard, block=False))
application.add_handler(CommandHandler('list', send_users_document, block=False))
application.add_handler(CommandHandler('groups', send_groups_document, block=False))
application.add_handler(CommandHandler('top', leaderboard, block=False))
