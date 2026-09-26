import logging
import json
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)

# ================== تنظیمات ==================
BOT_TOKEN = "8682124344:AAG6UX_lrAn4A4qQ3SfKFtiqFDmHCNuss_o"
ADMIN_ID = 5849215553   # آیدی عددی خودت

# ================== دیتابیس ساده (فایل JSON) ==================
USERS_FILE = "users.json"
MUSIC_FILE = "music.json"

def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_data(USERS_FILE)
music_list = load_data(MUSIC_FILE)

# ================== وضعیت مکالمه ==================
ADD_NAME, ADD_FILE = range(2)

# ================== توابع کمکی ==================
def get_greeting():
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "☀️ صبح بخیر"
    elif 12 <= hour < 17:
        return "🌤 ظهر بخیر"
    elif 17 <= hour < 21:
        return "🌆 عصر بخیر"
    else:
        return "🌙 شب بخیر"

def is_admin(user_id):
    return user_id == ADMIN_ID

def main_keyboard(user_id):
    buttons = [
        ["🎵 لیست موسیقی", "👤 پروفایل من"],
        ["📞 پشتیبانی"]
    ]
    if is_admin(user_id):
        buttons.append(["🛠 پنل مدیریت"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def admin_keyboard():
    buttons = [
        ["📊 آمار ربات", "👥 لیست کاربران"],
        ["➕ افزودن موسیقی", "❌ حذف موسیقی"],
        ["📢 ارسال پیام همگانی"],
        ["🔙 بازگشت به منوی اصلی"]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ================== دستورات ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    # ثبت کاربر جدید
    if user_id not in users:
        users[user_id] = {
            "name": user.full_name,
            "username": user.username or "ندارد",
            "join_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        save_data(USERS_FILE, users)

    greeting = get_greeting()
    text = (
        f"{greeting} <b>{user.first_name}</b> عزیز 🌹\n\n"
        f"به ربات موسیقی خوش آمدی 🎶\n"
        f"از منوی زیر می‌تونی استفاده کنی 👇"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard(user.id), parse_mode="HTML")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    info = users.get(user_id, {})
    text = (
        f"👤 <b>پروفایل شما</b>\n\n"
        f"🆔 آیدی عددی: <code>{user_id}</code>\n"
        f"📛 نام: {info.get('name', 'نامشخص')}\n"
        f"🔗 یوزرنیم: @{info.get('username', 'ندارد')}\n"
        f"📅 تاریخ عضویت: {info.get('join_date', 'نامشخص')}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def music_list_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not music_list:
        await update.message.reply_text("❌ هنوز هیچ موسیقی‌ای اضافه نشده.")
        return

    text = "🎵 <b>لیست موسیقی‌ها:</b>\n\n"
    keyboard = []
    for i, (key, val) in enumerate(music_list.items(), 1):
        text += f"{i}. {val['name']}\n"
        keyboard.append([InlineKeyboardButton(f"🎧 {val['name']}", callback_data=f"music_{key}")])

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML"
    )

async def music_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    key = query.data.replace("music_", "")
    item = music_list.get(key)

    if not item:
        await query.message.reply_text("❌ این موسیقی پیدا نشد.")
        return

    if item.get("file_id"):
        await query.message.reply_audio(
            audio=item["file_id"],
            caption=f"🎵 {item['name']}"
        )
    elif item.get("link"):
        await query.message.reply_text(f"🎵 {item['name']}\n🔗 {item['link']}")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 برای ارتباط با پشتیبانی به آیدی زیر پیام بدید:\n"
        "@YourSupportID"
    )

# ================== پنل مدیریت ==================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ شما دسترسی ندارید.")
        return
    await update.message.reply_text(
        "🛠 <b>پنل مدیریت</b>\n\nیک گزینه رو انتخاب کن:",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    text = (
        f"📊 <b>آمار ربات</b>\n\n"
        f"👥 تعداد کاربران: <b>{len(users)}</b>\n"
        f"🎵 تعداد موسیقی‌ها: <b>{len(music_list)}</b>"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not users:
        await update.message.reply_text("❌ هیچ کاربری ثبت نشده.")
        return

    text = "👥 <b>لیست کاربران:</b>\n\n"
    for i, (uid, info) in enumerate(users.items(), 1):
        text += f"{i}. {info['name']} | <code>{uid}</code>\n"

    if len(text) > 4000:
        text = text[:4000] + "\n..."

    await update.message.reply_text(text, parse_mode="HTML")

# ================== افزودن موسیقی (مکالمه) ==================
async def add_music_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "➕ <b>افزودن موسیقی جدید</b>\n\n"
        "لطفاً <b>نام موسیقی</b> رو بفرست:",
        parse_mode="HTML"
    )
    return ADD_NAME

async def add_music_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["music_name"] = update.message.text
    await update.message.reply_text(
        "🎧 حالا <b>فایل صوتی</b> یا <b>لینک</b> موسیقی رو بفرست:",
        parse_mode="HTML"
    )
    return ADD_FILE

async def add_music_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = context.user_data.get("music_name", "بدون نام")
    key = str(len(music_list) + 1)

    if update.message.audio:
        file_id = update.message.audio.file_id
        music_list[key] = {"name": name, "file_id": file_id}
        msg = f"✅ موسیقی «{name}» با موفقیت اضافه شد (فایل صوتی)."
    elif update.message.voice:
        file_id = update.message.voice.file_id
        music_list[key] = {"name": name, "file_id": file_id}
        msg = f"✅ موسیقی «{name}» با موفقیت اضافه شد (ویس)."
    elif update.message.text:
        link = update.message.text
        music_list[key] = {"name": name, "link": link}
        msg = f"✅ موسیقی «{name}» با موفقیت اضافه شد (لینک)."
    else:
        await update.message.reply_text("❌ فایل یا لینک معتبر نیست. دوباره تلاش کن.")
        return ADD_FILE

    save_data(MUSIC_FILE, music_list)
    await update.message.reply_text(msg, reply_markup=admin_keyboard())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ عملیات لغو شد.", reply_markup=admin_keyboard())
    return ConversationHandler.END

# ================== حذف موسیقی ==================
async def delete_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not music_list:
        await update.message.reply_text("❌ لیست موسیقی خالیه.")
        return

    keyboard = []
    for key, val in music_list.items():
        keyboard.append([InlineKeyboardButton(f"❌ {val['name']}", callback_data=f"del_{key}")])

    await update.message.reply_text(
        "کدوم موسیقی حذف بشه؟",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        return

    key = query.data.replace("del_", "")
    if key in music_list:
        name = music_list[key]["name"]
        del music_list[key]
        save_data(MUSIC_FILE, music_list)
        await query.edit_message_text(f"✅ موسیقی «{name}» حذف شد.")
    else:
        await query.edit_message_text("❌ پیدا نشد.")

# ================== برادکست ==================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(
        "📢 متن پیام همگانی رو بفرست:\n"
        "(برای لغو /cancel رو بزن)"
    )
    context.user_data["broadcast_mode"] = True

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("broadcast_mode"):
        return
    context.user_data["broadcast_mode"] = False

    text = update.message.text
    success = 0
    failed = 0

    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(
        f"✅ ارسال شد\n\n✔ موفق: {success}\n❌ ناموفق: {failed}"
    )

# ================== مدیریت دکمه‌ها ==================
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎵 لیست موسیقی":
        await music_list_handler(update, context)
    elif text == "👤 پروفایل من":
        await profile(update, context)
    elif text == "📞 پشتیبانی":
        await support(update, context)
    elif text == "🛠 پنل مدیریت":
        await admin_panel(update, context)
    elif text == "📊 آمار ربات":
        await stats(update, context)
    elif text == "👥 لیست کاربران":
        await user_list(update, context)
    elif text == "📢 ارسال پیام همگانی":
        await broadcast(update, context)
    elif text == "🔙 بازگشت به منوی اصلی":
        await start(update, context)
    elif context.user_data.get("broadcast_mode"):
        await send_broadcast(update, context)

# ================== main ==================
def main():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

    app = Application.builder().token(BOT_TOKEN).build()

    # مکالمه افزودن موسیقی
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ افزودن موسیقی$"), add_music_start)],
        states={
            ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_music_name)],
            ADD_FILE: [
                MessageHandler(filters.AUDIO | filters.VOICE | filters.TEXT, add_music_file)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^❌ حذف موسیقی$"), delete_music))
    app.add_handler(CallbackQueryHandler(music_callback, pattern="^music_"))
    app.add_handler(CallbackQueryHandler(delete_callback, pattern="^del_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("🤖 ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
