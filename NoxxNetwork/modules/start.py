import random
from html import escape 

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from NoxxNetwork import application, PHOTO_URL, SUPPORT_CHAT, UPDATE_CHAT, BOT_USERNAME, db, GROUP_ID
from NoxxNetwork import pm_users as collection 

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name
    username = update.effective_user.username

    user_data = await collection.find_one({"_id": user_id})

    if user_data is None:
        await collection.insert_one({"_id": user_id, "first_name": first_name, "username": username})
        try:
            await context.bot.send_message(chat_id=GROUP_ID, 
                                           text=f"New user Started The Bot..\n User: <a href='tg://user?id={user_id}'>{escape(first_name)}</a>", 
                                           parse_mode='HTML')
        except Exception:
            pass
    else:
        if user_data.get('first_name') != first_name or user_data.get('username') != username:
            await collection.update_one({"_id": user_id}, {"$set": {"first_name": first_name, "username": username}})

    if update.effective_chat.type == "private":
        # Safe HTML formatting instead of Markdown
        caption = (
            f"<b>Heyyyy...</b>\n\n"
            f"I am Grabbing Your Waifu Bot... Add Me in Your group.. "
            f"And I will send Random Characters After every 100 messages in Group... "
            f"Use /grab to Collect that Characters in Your Collection.. "
            f"and see Collection by using /Harem... So add in Your groups and Collect Your harem"
        )
        keyboard = [
            [InlineKeyboardButton("ADD ME", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        photo_url = random.choice(PHOTO_URL)

        await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=photo_url, 
            caption=caption, 
            reply_markup=reply_markup, 
            parse_mode='HTML' # Markdown se HTML par switch kiya
        )

    else:
        photo_url = random.choice(PHOTO_URL)
        keyboard = [
            [InlineKeyboardButton("ADD ME", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("SUPPORT", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("UPDATES", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("HELP", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_photo(
            chat_id=update.effective_chat.id, 
            photo=photo_url, 
            caption="🎴 Alive!?... \nConnect to me in PM For more information",
            reply_markup=reply_markup 
        )

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'help':
        help_text = (
            "<b>Help Section:</b>\n\n"
            "<b>/guess</b>: To Guess character (only works in group)\n"
            "<b>/fav</b>: Add Your fav\n"
            "<b>/trade</b>: To trade Characters\n"
            "<b>/gift</b>: Give any Character from Your Collection to another user..\n"
            "<b>/harem</b>: To see Your Collection\n"
            "<b>/topgroups</b>: See Top Groups\n"
            "<b>/top</b>: See Top Users\n"
            "<b>/changetime</b>: Change Character appear time"
        )
        help_keyboard = [[InlineKeyboardButton("⤾ Bᴀᴄᴋ", callback_data='back')]]
        reply_markup = InlineKeyboardMarkup(help_keyboard)
        
        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id, 
            message_id=query.message.message_id, 
            caption=help_text, 
            reply_markup=reply_markup, 
            parse_mode='HTML'
        )

    elif query.data == 'back':
        caption = (
            f"<b>Heyyyy...</b>\n\n"
            f"I am Grabbing Your Waifu Bot... Add Me in Your group.. "
            f"And I will send Random Characters After every 100 messages in Group..."
        )
        keyboard = [
            [InlineKeyboardButton("⌯ ᴀᴅᴅ ᴍᴇ ʙᴀʙʏ ⌯", url=f'http://t.me/{BOT_USERNAME}?startgroup=new')],
            [InlineKeyboardButton("📨Sᴜᴩᴩᴏʀᴛ", url=f'https://t.me/{SUPPORT_CHAT}'),
             InlineKeyboardButton("📨Uᴩᴅᴀᴛᴇ", url=f'https://t.me/{UPDATE_CHAT}')],
            [InlineKeyboardButton("ʜᴇʟᴩ", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.edit_message_caption(
            chat_id=update.effective_chat.id, 
            message_id=query.message.message_id, 
            caption=caption, 
            reply_markup=reply_markup, 
            parse_mode='HTML'
        )

application.add_handler(CallbackQueryHandler(button, pattern='^help$|^back$', block=False))
start_handler = CommandHandler('start', start, block=False)
application.add_handler(start_handler)
