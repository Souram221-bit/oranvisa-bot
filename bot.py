import asyncio
import os
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ========== PASTE YOUR TOKEN HERE ==========
TOKEN = "8689074287:AAHKshFAxpQ3zN3_0kFwJW6VQ7HJEKitAAw"
# ===========================================

# Flask app for Render
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is alive"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

# Bot handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is working! Send /subscribe")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    context.bot_data.setdefault("subs", set()).add(chat_id)
    await update.message.reply_text("✅ Subscribed! You'll get alerts.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    context.bot_data.get("subs", set()).discard(chat_id)
    await update.message.reply_text("❌ Unsubscribed.")

async def periodic_check(app):
    import random
    while True:
        subs = app.bot_data.get("subs", set())
        if subs and random.random() < 0.05:  # 5% test chance
            for chat_id in subs:
                await app.bot.send_message(chat_id, "🔔 TEST ALERT: This is a test. Real BLS monitoring coming soon.")
        await asyncio.sleep(60)

def main():
    # Start Flask thread
    Thread(target=run_flask, daemon=True).start()
    
    # Start bot
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    
    # Start background checker
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(periodic_check(app))
    
    # Run bot
    app.run_polling()

if __name__ == "__main__":
    main()
