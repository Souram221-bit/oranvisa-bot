import asyncio
import aiohttp
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")  # Set this in Railway

# ---------- REAL BLS ORAN SLOT CHECKER ----------
async def check_bls_oran_slots():
    """Return True if appointment slots are available in Oran."""
    url = "https://algeria.blsspainvisa.com/oran/appointment"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                html = await resp.text()
                html_lower = html.lower()
                # BLS usually shows "No slots available" or calendar disabled
                if "no slots available" in html_lower:
                    return False
                if "no appointment" in html_lower:
                    return False
                if "calendar is disabled" in html_lower:
                    return False
                # If we see a date picker with enabled dates, assume slots exist
                if 'class="ui-state-default"' in html and 'disabled' not in html:
                    return True
                # Fallback: look for any visible calendar day
                if 'class="day"' in html and 'disabled' not in html:
                    return True
                return False
    except Exception as e:
        print(f"Checker error: {e}")
        return False

# ---------- BOT COMMANDS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🇪🇸 *Spain Visa Slot Notifier (Oran)*\n\n"
        "I will send you an instant alert when an appointment slot appears.\n\n"
        "Commands:\n"
        "/subscribe – get alerts\n"
        "/unsubscribe – stop alerts\n"
        "/status – check right now",
        parse_mode="Markdown"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    context.bot_data.setdefault("subscribers", set()).add(chat_id)
    await update.message.reply_text("✅ You are subscribed! You'll be notified when slots open.")

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    context.bot_data.get("subscribers", set()).discard(chat_id)
    await update.message.reply_text("❌ Unsubscribed. No further alerts.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Checking BLS Oran right now...")
    available = await check_bls_oran_slots()
    if available:
        await update.message.reply_text("✅ *SLOTS AVAILABLE NOW!* Go to https://algeria.blsspainvisa.com/oran/appointment immediately.", parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ No slots at the moment. I'll notify you when any appear.")

# ---------- BACKGROUND MONITOR ----------
async def periodic_check(app):
    while True:
        try:
            available = await check_bls_oran_slots()
            if available:
                msg = (
                    "🚨 *NEW VISA SLOT DETECTED IN ORAN!* 🚨\n"
                    "Book now: https://algeria.blsspainvisa.com/oran/appointment\n"
                    "Slots disappear quickly – act fast!"
                )
                for chat_id in app.bot_data.get("subscribers", set()):
                    await app.bot.send_message(chat_id, msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Periodic check error: {e}")
        await asyncio.sleep(60)  # check every minute

# ---------- MAIN ----------
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("status", status))
    asyncio.create_task(periodic_check(app))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
