import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

# =========================
# تنظیمات
# =========================

TOKEN = "8682124344:AAHTdQw4EpaPrEEjxff1QoQS-6X6s-j-ypA"
ADMIN_ID = 5849215553
FILE = "replies.json"

ADD_KEY, ADD_ANSWER = range(2)


# =========================
# فایل جواب‌ها
# =========================

def load_replies():
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_replies(replies):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(
            replies,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================
# بررسی ادمین
# =========================

def is_admin(update):
    return (
        update.effective_user
        and update.effective_user.id == ADMIN_ID
    )


# =========================
# منوی اصلی
# =========================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "➕ افزودن جواب",
                callback_data="add"
            ),
            InlineKeyboardButton(
                "📋 لیست جواب‌ها",
                callback_data="list"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 حذف جواب",
                callback_data="delete"
            ),
            InlineKeyboardButton(
                "🆔 شناسه من",
                callback_data="myid"
            )
        ]
    ])


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام 👋\n"
        "ربات فعاله ✅\n\n"
        "از منوی زیر انتخاب کن:",
        reply_markup=main_keyboard()
    )


# =========================
# HELP
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 راهنما:\n\n"
        "/start - منوی اصلی\n"
        "/help - راهنما\n"
        "/myid - شناسه شما\n"
        "/list - لیست جواب‌ها\n"
        "/add - افزودن جواب\n"
        "/delete کلمه - حذف جواب\n"
        "/cancel - لغو عملیات"
    )


# =========================
# MY ID
# =========================

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 شناسه شما:\n{update.effective_user.id}"
    )


# =========================
# افزودن جواب
# =========================

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.callback_query.answer(
            "⛔ اجازه دسترسی ندارید.",
            show_alert=True
        )
        return ConversationHandler.END

    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "➕ افزودن جواب\n\n"
        "🔤 اول کلمه یا عبارت را بفرست:"
    )

    return ADD_KEY


async def receive_key(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return ConversationHandler.END

    key = update.message.text.strip().lower()

    if not key:
        await update.message.reply_text(
            "❌ کلمه نمی‌تواند خالی باشد."
        )
        return ADD_KEY

    context.user_data["new_key"] = key

    await update.message.reply_text(
        "✅ کلمه دریافت شد.\n\n"
        "💬 حالا جواب این کلمه را بفرست:"
    )

    return ADD_ANSWER


async def receive_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        return ConversationHandler.END

    answer = update.message.text.strip()
    key = context.user_data.get("new_key")

    if not key:
        await update.message.reply_text(
            "❌ خطا: کلمه پیدا نشد."
        )
        return ConversationHandler.END

    if not answer:
        await update.message.reply_text(
            "❌ جواب نمی‌تواند خالی باشد."
        )
        return ADD_ANSWER

    replies = load_replies()

    replies[key] = answer

    save_replies(replies)

    context.user_data.pop("new_key", None)

    await update.message.reply_text(
        f"✅ ذخیره شد!\n\n"
        f"🔤 کلمه: {key}\n"
        f"💬 جواب: {answer}",
        reply_markup=main_keyboard()
    )

    return ConversationHandler.END


async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data.pop("new_key", None)

    await update.message.reply_text(
        "❌ عملیات لغو شد.",
        reply_markup=main_keyboard()
    )

    return ConversationHandler.END


# =========================
# لیست جواب‌ها
# =========================

async def list_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ اجازه دسترسی ندارید."
        )
        return

    replies = load_replies()

    if not replies:
        await update.message.reply_text(
            "📭 هنوز جوابی ثبت نشده."
        )
        return

    text = "📋 جواب‌های ثبت‌شده:\n\n"

    for key, answer in replies.items():
        text += f"🔹 {key} → {answer}\n"

    await update.message.reply_text(text)


# =========================
# حذف جواب
# =========================

async def delete_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not is_admin(update):
        await update.message.reply_text(
            "⛔ اجازه دسترسی ندارید."
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ مثال:\n/delete سلام"
        )
        return

    key = " ".join(context.args).strip().lower()

    replies = load_replies()

    if key not in replies:
        await update.message.reply_text(
            "❌ چنین جوابی وجود ندارد."
        )
        return

    del replies[key]

    save_replies(replies)

    await update.message.reply_text(
        f"🗑 جواب «{key}» حذف شد.",
        reply_markup=main_keyboard()
    )


# =========================
# دکمه‌ها
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "⛔ دسترسی ندارید.",
            show_alert=True
        )
        return

    await query.answer()

    # لیست
    if query.data == "list":

        replies = load_replies()

        if not replies:
            await query.message.reply_text(
                "📭 هنوز جوابی ثبت نشده."
            )
            return

        text = "📋 جواب‌های ثبت‌شده:\n\n"

        for key, answer in replies.items():
            text += f"🔹 {key} → {answer}\n"

        await query.message.reply_text(text)

    # حذف
    elif query.data == "delete":

        await query.message.reply_text(
            "🗑 برای حذف جواب بنویس:\n\n"
            "/delete سلام"
        )

    # شناسه
    elif query.data == "myid":

        await query.message.reply_text(
            f"🆔 شناسه شما:\n"
            f"{query.from_user.id}"
        )


# =========================
# جواب خودکار
# =========================

async def reply_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message or not update.message.text:
        return

    text = update.message.text.strip().lower()

    replies = load_replies()

    if text in replies:

        await update.message.reply_text(
            replies[text]
        )


# =========================
# ساخت ربات
# =========================

def main():

    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .pool_timeout(30)
        .build()
    )

    # دستورات
    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("help", help_command)
    )

    app.add_handler(
        CommandHandler("myid", myid)
    )

    app.add_handler(
        CommandHandler("list", list_replies)
    )

    app.add_handler(
        CommandHandler("delete", delete_reply)
    )

    # افزودن جواب
    add_conversation = ConversationHandler(

        entry_points=[
            CallbackQueryHandler(
                add_start,
                pattern="^add$"
            )
        ],

        states={

            ADD_KEY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_key
                )
            ],

            ADD_ANSWER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_answer
                )
            ],
        },

        fallbacks=[
            CommandHandler(
                "cancel",
                cancel_add
            )
        ],
    )

    app.add_handler(add_conversation)

    # سایر دکمه‌ها
    app.add_handler(
        CallbackQueryHandler(button_handler)
    )

    # جواب خودکار پیام‌ها
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            reply_message
        )
    )

    print("🤖 Bot is running...")

    app.run_polling()


# =========================
# اجرای برنامه
# =========================

if __name__ == "__main__":
    main()
