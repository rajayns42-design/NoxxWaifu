from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from NoxxNetwork import user_collection, Waifuu
import html

pending_trades = {}
pending_gifts = {}

# --- TRADE COMMAND ---
@Waifuu.on_message(filters.command("trade") & filters.group)
async def trade(client, message):
    sender_id = message.from_user.id
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a user to trade!")
        return

    receiver_id = message.reply_to_message.from_user.id
    if sender_id == receiver_id:
        await message.reply_text("❌ You can't trade with yourself!")
        return

    if len(message.command) != 3:
        await message.reply_text("<b>Usage:</b>\n<code>/trade [Your_Char_ID] [Their_Char_ID]</code>", parse_mode="html")
        return

    s_char_id, r_char_id = message.command[1], message.command[2]

    # Ek hi baar fetch karein
    sender = await user_collection.find_one({'id': sender_id})
    receiver = await user_collection.find_one({'id': receiver_id})

    if not sender or not receiver:
        await message.reply_text("❌ One of the users hasn't started the bot!")
        return

    s_char = next((c for c in sender.get('characters', []) if c['id'] == s_char_id), None)
    r_char = next((c for c in receiver.get('characters', []) if c['id'] == r_char_id), None)

    if not s_char:
        await message.reply_text(f"❌ You don't have ID: {s_char_id}")
        return
    if not r_char:
        await message.reply_text(f"❌ They don't have ID: {r_char_id}")
        return

    pending_trades[(sender_id, receiver_id)] = (s_char, r_char)
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Trade", callback_data=f"tr_confirm_{sender_id}_{receiver_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"tr_cancel_{sender_id}_{receiver_id}")]
    ])

    await message.reply_text(
        f"🤝 <b>Trade Proposal</b>\n\n"
        f"👤 {message.from_user.first_name} gives: <b>{s_char['name']}</b>\n"
        f"👤 {message.reply_to_message.from_user.first_name} gives: <b>{r_char['name']}</b>\n\n"
        f"Does {message.reply_to_message.from_user.mention} accept?",
        reply_markup=keyboard,
        parse_mode="html"
    )

# --- GIFT COMMAND ---
@Waifuu.on_message(filters.command("gift") & filters.group)
async def gift(client, message):
    sender_id = message.from_user.id
    if not message.reply_to_message:
        await message.reply_text("❌ Reply to a user to gift!")
        return

    receiver_id = message.reply_to_message.from_user.id
    if sender_id == receiver_id: return

    if len(message.command) != 2:
        await message.reply_text("<b>Usage:</b> <code>/gift [Char_ID]</code>", parse_mode="html")
        return

    char_id = message.command[1]
    sender = await user_collection.find_one({'id': sender_id})
    
    char = next((c for c in sender.get('characters', []) if c['id'] == char_id), None)
    if not char:
        await message.reply_text("❌ You don't have this character!")
        return

    pending_gifts[sender_id] = {
        'receiver_id': receiver_id,
        'character': char,
        'receiver_name': message.reply_to_message.from_user.first_name
    }

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Gift", callback_data=f"gf_confirm_{sender_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data=f"gf_cancel_{sender_id}")]
    ])

    await message.reply_text(
        f"🎁 Do you really want to gift <b>{char['name']}</b> to {message.reply_to_message.from_user.first_name}?",
        reply_markup=keyboard,
        parse_mode="html"
    )

# --- CALLBACK HANDLERS ---
@Waifuu.on_callback_query(filters.regex(r"^(tr_|gf_)"))
async def handle_callbacks(client, query):
    data = query.data
    user_id = query.from_user.id

    # Trade Logic
    if data.startswith("tr_"):
        _, action, s_id, r_id = data.split("_")
        s_id, r_id = int(s_id), int(r_id)

        if user_id != r_id:
            await query.answer("❌ This trade is not for you!", show_alert=True)
            return

        trade_data = pending_trades.get((s_id, r_id))
        if not trade_data:
            await query.message.edit_text("❌ Trade expired or invalid.")
            return

        if action == "confirm":
            s_char, r_char = trade_data
            # Atomically update both
            await user_collection.update_one({'id': s_id}, {'$pull': {'characters': {'id': s_char['id']}}})
            await user_collection.update_one({'id': r_id}, {'$pull': {'characters': {'id': r_char['id']}}})
            
            await user_collection.update_one({'id': s_id}, {'$push': {'characters': r_char}})
            await user_collection.update_one({'id': r_id}, {'$push': {'characters': s_char}})
            
            await query.message.edit_text("✅ Trade Successful!")
        else:
            await query.message.edit_text("❌ Trade Cancelled.")
        pending_trades.pop((s_id, r_id), None)

    # Gift Logic
    elif data.startswith("gf_"):
        _, action, s_id = data.split("_")
        s_id = int(s_id)

        if user_id != s_id:
            await query.answer("❌ Only the sender can confirm!", show_alert=True)
            return

        gift = pending_gifts.get(s_id)
        if not gift: return

        if action == "confirm":
            await user_collection.update_one({'id': s_id}, {'$pull': {'characters': {'id': gift['character']['id']}}})
            await user_collection.update_one(
                {'id': gift['receiver_id']}, 
                {'$push': {'characters': gift['character']}}, 
                upsert=True
            )
            await query.message.edit_text(f"✅ Gifted successfully to {gift['receiver_name']}!")
        else:
            await query.message.edit_text("❌ Gift Cancelled.")
        pending_gifts.pop(s_id, None)
