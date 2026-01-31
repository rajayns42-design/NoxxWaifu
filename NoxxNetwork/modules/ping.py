import time
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from NoxxNetwork import application, sudo_users

async def ping(update: Update, context: CallbackContext) -> None:
    # Sudo check (String comparison safety ke saath)
    user_id = str(update.effective_user.id)
    if user_id not in sudo_users:
        await update.message.reply_text("❌ Nouu.. only Sudo users can use this command.")
        return

    start_time = time.time()
    
    # Initial message send
    message = await update.message.reply_text('🏓 Pinging...')
    
    end_time = time.time()
    elapsed_time = round((end_time - start_time) * 1000, 2)
    
    try:
        # Edit karke final latency dikhayein
        await message.edit_text(f'<b>🏓 Pong!</b>\n<code>Latency: {elapsed_time}ms</code>', parse_mode='HTML')
    except Exception:
        # Agar message edit na ho paye
        await update.message.reply_text(f'<b>🏓 Pong!</b>\n<code>Latency: {elapsed_time}ms</code>', parse_mode='HTML')

# Handler add karein
application.add_handler(CommandHandler("ping", ping, block=False))
