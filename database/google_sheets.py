import gspread
from google.oauth2.service_account import Credentials
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# Kết nối với Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(CREDS)
DB_FILE = "database/user_sheets.json"  # Đặt file vào thư mục `database/`

def load_user_sheets():
    """Tải danh sách user_id ↔ sheet_id từ file JSON"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as file:
            return json.load(file)
    return {}

def save_user_sheets(data):
    """Lưu danh sách user_id ↔ sheet_id vào file JSON"""
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)  # Đảm bảo thư mục tồn tại
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)

def get_google_client():
    """Kết nối với Google Sheets API"""
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)

def create_user_sheet(user_id, username="User"):
    """Tạo Google Sheet mới nếu chưa có"""
    user_sheets = load_user_sheets()

    if str(user_id) in user_sheets:
        return user_sheets[str(user_id)]  # Trả về Sheet ID nếu đã tồn tại

    client = get_google_client()
    sheet = client.create(f"{username}_Expenses")  # Tạo Google Sheet mới
    sheet.share(None, perm_type='anyone', role='reader')  # Cho phép mọi người xem

    user_sheets[str(user_id)] = sheet.id  # Lưu user_id ↔ sheet_id
    save_user_sheets(user_sheets)

    return sheet.id  # Trả về Sheet ID mới tạo

def get_user_sheet(user_id):
    """Lấy Google Sheet ID của user"""
    user_sheets = load_user_sheets()
    return user_sheets.get(str(user_id), None)

def get_worksheet(user_id):
    """Lấy worksheet của user"""
    sheet_id = get_user_sheet(user_id)
    if not sheet_id:
        return None  # User chưa có Google Sheet

    client = get_google_client()
    sheet = client.open_by_key(sheet_id)

    # Kiểm tra xem có worksheet "Categories" chưa, nếu chưa thì tạo mới
    try:
        return sheet.worksheet("Categories")
    except gspread.exceptions.WorksheetNotFound:
        return sheet.add_worksheet(title="Categories", rows=100, cols=2)

async def send_google_sheet(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_email = update.message.from_user.username  # Sử dụng username làm tên file

    # Tạo Google Sheet nếu chưa có
    sheet_id = create_user_sheet(user_id, user_email)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    # Mở Google Sheet và chia sẻ quyền chỉnh sửa
    client = get_google_client()
    sheet = client.open_by_key(sheet_id)
    sheet.share(user_email, perm_type='user', role='writer')  # Chia sẻ quyền chỉnh sửa

    # Tạo nút "GOOGLE SHEET"
    keyboard = [[InlineKeyboardButton("📊 GOOGLE SHEET", url=sheet_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Gửi tin nhắn với nút bấm
    await update.message.reply_text("📝 Click nút dưới đây để mở Google Sheet của bạn:", reply_markup=reply_markup)
