import os
import re
from telegram import Update, ChatPermissions
from telegram.ext import (
Application,
CommandHandler,
MessageHandler,
ContextTypes,
ChatMemberHandler,
filters,
)

TOKEN = os.getenv("BOT_TOKEN")
link_filter = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.effective_message.reply_text(
"سلام! 💜 من آریا هستم.\nبرای دستورها /help را بزن."
)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.effective_message.reply_text(
"📋 راهنمای آریا\n"
"/start - شروع\n"
"/help - راهنما\n"
"/rules - قوانین\n"
"/filter_on - فعال‌کردن فیلتر لینک\n"
"/filter_off - خاموش‌کردن فیلتر لینک\n"
"برای مدیریت اعضا، روی پیام عضو پاسخ بده و /ban یا /mute بزن."
)

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.effective_message.reply_text(
"📜 قوانین گروه:\n۱. احترام به اعضا\n۲. ارسال‌نکردن پیام مزاحم\n۳. رعایت قوانین مدیران"
)

async def is_admin(update, context):
user = update.effective_user
chat = update.effective_chat
if not user or not chat:
return False
member = await context.bot.get_chat_member(chat.id, user.id)
return member.status in ("administrator", "creator")

async def filter_on(update, context):
if not await is_admin(update, context):
await update.effective_message.reply_text("⛔ فقط مدیران گروه.")
return
link_filter.add(update.effective_chat.id)
await update.effective_message.reply_text("✅ فیلتر لینک فعال شد.")

async def filter_off(update, context):
if not await is_admin(update, context):
await update.effective_message.reply_text("⛔ فقط مدیران گروه.")
return
link_filter.discard(update.effective_chat.id)
await update.effective_message.reply_text("🔓 فیلتر لینک خاموش شد.")

async def moderation(update, context, action):
message = update.effective_message
if not await is_admin(update, context):
await message.reply_text("⛔ فقط مدیران گروه.")
return
if not message.reply_to_message:
await message.reply_text("روی پیام عضو پاسخ بده و دستور را بفرست.")
return

target = message.reply_to_message.from_user
if target.is_bot:
    await message.reply_text("این دستور روی ربات اجرا نمی‌شود.")
    return

try:
    chat_id = update.effective_chat.id
    if action == "ban":
        await context.bot.ban_chat_member(chat_id, target.id)
        answer = "🚫 عضو مسدود شد."
    elif action == "mute":
        await context.bot.restrict_chat_member(
            chat_id, target.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
        answer = "🔇 عضو ساکت شد."
    elif action == "unmute":
        await context.bot.restrict_chat_member(
            chat_id, target.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        answer = "🔊 سکوت عضو برداشته شد."
    else:
        await context.bot.unban_chat_member(
            chat_id, target.id, only_if_banned=True
        )
        answer = "✅ مسدودیت برداشته شد."
    await message.reply_text(answer)
except Exception:
    await message.reply_text("❌ انجام نشد؛ دسترسی‌های مدیریتی آریا را بررسی کن.")

async def delete_links(update, context):
message = update.effective_message
chat = update.effective_chat
user = update.effective_user
if not message or not chat or not user or chat.id not in link_filter:
return
member = await context.bot.get_chat_member(chat.id, user.id)
if member.status in ("administrator", "creator"):
return
text = message.text or message.caption or ""
if re.search(r"(https?://|www.|t.me/|telegram.me/)", text, re.I):
try:
await message.delete()
except Exception:
pass

async def welcome(update, context):
data = update.chat_member
if not data:
return
if data.old_chat_member.status in ("left", "kicked") and data.new_chat_member.status in ("member", "restricted"):
await context.bot.send_message(
data.chat.id,
f"سلام {data.new_chat_member.user.first_name}! 💜 به گروه خوش اومدی."
)

async def ban(update, context):
await moderation(update, context, "ban")

async def unban(update, context):
await moderation(update, context, "unban")

async def mute(update, context):
await moderation(update, context, "mute")

async def unmute(update, context):
await moderation(update, context, "unmute")

def main():
if not TOKEN:
raise RuntimeError("متغیر محرمانه BOT_TOKEN تنظیم نشده است.")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("rules", rules))
app.add_handler(CommandHandler("filter_on", filter_on))
app.add_handler(CommandHandler("filter_off", filter_off))
app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("unban", unban))
app.add_handler(CommandHandler("mute", mute))
app.add_handler(CommandHandler("unmute", unmute))
app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, delete_links))
print("Aria is running!")
app.run_polling()

if __name__ == "__main__":
    main()
