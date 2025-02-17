from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes
from database.google_sheets import create_user_sheet, get_user_sheet  # Import từ google_sheets.py
import json
import os

USER_SHEETS_FILE = 'user_sheets.json'

def save_user_sheet(user_id, sheet_id):
    """Save user ID and Google Sheet ID to user_sheets.json"""
    if os.path.exists(USER_SHEETS_FILE):
        with open(USER_SHEETS_FILE, 'r') as file:
            user_sheets = json.load(file)
    else:
        user_sheets = {}

    user_sheets[user_id] = sheet_id

    with open(USER_SHEETS_FILE, 'w') as file:
        json.dump(user_sheets, file)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - Gửi Google Sheet bằng nút"""
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or f"user_{user_id}"
    sheet_id = get_user_sheet(user_id)

    if not sheet_id:
        sheet_id = create_user_sheet(user_id, username)
        save_user_sheet(user_id, sheet_id)
        greeting = "Welcome to the Expense Bot!"
    else:
        greeting = "Welcome back to the Expense Bot!"

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
    keyboard = [[InlineKeyboardButton("📊 GOOGLE SHEET", url=sheet_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"👋 Hello {username}! {greeting}",
        reply_markup=reply_markup
    )
# Hàm trả về handler để tự động load
def get_handlers():
    return CommandHandler("start", start_command)
