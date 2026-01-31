from pymongo import ReturnDocument
from pyrogram.enums import ChatMemberStatus
from NoxxNetwork import user_totals_collection, Waifuu
from pyrogram import Client, filters
from pyrogram.types import Message

# Admin check ke liye status list
ADMINS = [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]

@Waifuu.on_message(filters.command("changetime") & filters.group)
async def change_time(client: Client, message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    try:
        # Check karein ki user admin hai ya nahi
        member = await client.get_chat_member(chat_id, user_id)
        if member.status not in ADMINS:
            await message.reply_text("<b>❌ Aap admin nahi hain!</b>", parse_mode="HTML")
            return

        # Arguments check karein
        args = message.command
        if len(args) != 2:
            await message.reply_text("<b>Usage:</b> <code>/changetime 100</code>", parse_mode="HTML")
            return

        # Frequency validate karein
        try:
            new_frequency = int(args[1])
        except ValueError:
            await message.reply_text("<b>❌ Please ek sahi number daalein!</b>", parse_mode="HTML")
            return

        if new_frequency < 100:
            await message.reply_text("<b>⚠️ Frequency kam se kam 100 honi chahiye.</b>", parse_mode="HTML")
            return

        # Database update karein
        await user_totals_collection.find_one_and_update(
            {'chat_id': str(chat_id)},
            {'$set': {'message_frequency': new_frequency}},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        await message.reply_text(f"<b>✅ Done!</b>\nAb har <b>{new_frequency}</b> messages ke baad character aayega.", parse_mode="HTML")

    except Exception as e:
        # Crash se bachne ke liye safe error handling
        await message.reply_text(f"<b>❌ Error:</b> <code>{str(e)}</code>", parse_mode="HTML")
