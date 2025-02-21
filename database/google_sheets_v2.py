from turtle import color
import gspread_asyncio
import gspread  # ✅ Import gspread để xử lý exceptions
from gspread_formatting import *
from google.oauth2.service_account import Credentials
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime


# Kết nối với Google Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file"
]
CREDS = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
DB_FILE = "user_sheets.json"

def get_drive_service():
    """Kết nối với Google Drive API."""
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def get_agcm():
    """Tạo Google Sheets Client Manager bất đồng bộ"""
    agc = gspread_asyncio.AsyncioGspreadClientManager(lambda: CREDS)
    return agc

async def get_google_client():
    """Kết nối với Google Sheets API (bất đồng bộ)"""
    agcm = get_agcm()  # Lấy client manager bất đồng bộ
    return await agcm.authorize()

async def load_user_sheets():
    """Tải danh sách user_id ↔ sheet_id từ file JSON"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as file:
            return json.load(file)
    return {}

async def save_user_sheets(data):
    """Lưu danh sách user_id ↔ sheet_id vào file JSON"""
    directory = os.path.dirname(DB_FILE)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)  # Đảm bảo thư mục tồn tại
    with open(DB_FILE, "w") as file:
        json.dump(data, file, indent=4)

async def get_user_sheet_for_current_year(user_id, username="User", update: Update = None):
    """
    Lấy Google Sheet ID của user cho năm hiện tại.
    Nếu chưa có thì tạo mới.
    """
    user_sheets = await load_user_sheets()
    current_year = str(datetime.now().year)

    # Kiểm tra user đã có sheet cho năm hiện tại chưa
    if str(user_id) in user_sheets and current_year in user_sheets[str(user_id)]:
        return user_sheets[str(user_id)][current_year]

    # Nếu chưa có thì tạo mới
    await update.message.reply_text("⏳ Đang tạo Google Sheet... Xin hãy chờ!")
    sheet_id = await create_user_sheet(user_id, username, current_year)

    # Lưu lại vào database
    if str(user_id) not in user_sheets:
        user_sheets[str(user_id)] = {}

    user_sheets[str(user_id)][current_year] = sheet_id
    await save_user_sheets(user_sheets)

    return sheet_id

async def create_user_sheet(user_id, username="User", year=None):
    """Tạo Google Sheet mới với 12 tháng, định dạng bảng ngay từ đầu."""
    if not year:
        year = str(datetime.now().year)
    sheet_name = f"{username}_{year}"

    client = await get_google_client()
    sheet = await client.create(sheet_name)

    # Tạo 12 worksheet với format bảng
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    for month in months:
        ws = await sheet.add_worksheet(title=month, rows=500, cols=20)
        await format_month_worksheet(ws, sheet.id)  # Áp dụng format luôn

    # Xóa worksheet mặc định ("Sheet1")
    default_sheet = await sheet.worksheet("Sheet1")
    await sheet.del_worksheet(default_sheet)

    return sheet.id

async def format_month_worksheet(ws, spreadsheet_id):
    """Định dạng worksheet cho một tháng"""
    
    # ✅ Lấy Google Sheets client đồng bộ
    sync_creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    sync_client = gspread.authorize(sync_creds)  # 👉 Dùng gspread đồng bộ

    # ✅ Mở spreadsheet bằng client đồng bộ
    sheet = sync_client.open_by_key(spreadsheet_id)

    # ✅ Lấy worksheet dưới dạng gspread.Worksheet (đồng bộ)
    real_ws = sheet.worksheet(ws.title)

    # Định nghĩa header
    headers = [
        ["Ngày", "Thu", "Chi", "Loại", "Mô tả", "", 
         "Ngày", "Tiết kiệm", "Loại", "Mô tả", "", 
         "Mục", "Hạn mức", "Đã chi", "Còn lại"]
    ]
    
    # ✅ Vẫn dùng async để update nội dung
    await ws.update('A1:O1', headers)

    # Định dạng màu header
    header_fmt = CellFormat(
        backgroundColor=Color(0.5, 0.2, 0.6),  # Màu tím
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1)),  # Chữ trắng
        horizontalAlignment='CENTER'
    )

    # ✅ Dùng real_ws để format
    format_cell_range(real_ws, "A1:O1", header_fmt)

    # Căn giữa toàn bộ dữ liệu
    align_fmt = CellFormat(horizontalAlignment='CENTER')
    format_cell_range(real_ws, "A:O", align_fmt)

    # Định dạng màu cho từng loại giao dịch
    fmt_red = CellFormat(backgroundColor=Color(1, 0.6, 0.6))  # Chi tiêu (đỏ nhạt)
    fmt_green = CellFormat(backgroundColor=Color(0.6, 1, 0.6))  # Tiết kiệm (xanh nhạt)

    # Áp dụng Conditional Formatting
    apply_conditional_format(real_ws, "C:C", "Chi tiêu", fmt_red)
    apply_conditional_format(real_ws, "H:H", "Tiết kiệm", fmt_green)

    return ws

def apply_conditional_format(ws, col_range, criteria, cell_format):
    """Áp dụng định dạng có điều kiện cho một cột dựa trên tiêu chí"""
    rules = get_conditional_format_rules(ws)
    rule = ConditionalFormatRule(
        ranges=[GridRange.from_a1_range(col_range, ws)],
        booleanRule=BooleanRule(
            condition=BooleanCondition('TEXT_EQ', [criteria]),
            format=cell_format
        )
    )
    rules.append(rule)
    rules.save()  # ✅ Lưu lại rules vào Google Sheets


async def get_worksheet(user_id):
    """Lấy worksheet của user"""
    sheet_id = await get_user_sheet_for_current_year(user_id)
    if not sheet_id:
        return None  # User chưa có Google Sheet

    client = await get_google_client()
    sheet = await client.open_by_key(sheet_id)

    # Kiểm tra xem có worksheet "Categories" chưa, nếu chưa thì tạo mới
    try:
        return await sheet.worksheet("Categories")
    except gspread.WorksheetNotFound:  # ✅ Đổi sang gspread.WorksheetNotFound
        return await sheet.add_worksheet(title="Categories", rows=100, cols=2)

async def list_permissions(sheet_id):
    """Liệt kê các email có quyền chỉnh sửa Google Sheet."""
    agcm = get_agcm()  # Lấy client manager bất đồng bộ
    client = await agcm.authorize()
    sheet = await client.open_by_key(sheet_id)
    permissions = await sheet.list_permissions()

    return [perm['emailAddress'] for perm in permissions if 'emailAddress' in perm]

async def delete_email_permission(sheet_id, user_email):
    """Xóa quyền chỉnh sửa của email khỏi Google Sheet (trừ Service Account)."""
    service = get_drive_service()
    service_account_email = CREDS.service_account_email  # Email service account

    try:
        permissions = service.permissions().list(
            fileId=sheet_id, 
            fields="permissions(id, emailAddress)"
        ).execute()

        for perm in permissions.get('permissions', []):
            email = perm.get('emailAddress')
            # Không xóa nếu là service account
            if email and email == user_email and email != service_account_email:
                service.permissions().delete(
                    fileId=sheet_id, 
                    permissionId=perm['id']
                ).execute()
                return True
    except Exception as e:
        print(f"Error deleting permission: {e}")
    
    return False


async def send_google_sheet(update: Update, context: CallbackContext, sheet_id: str, user_email: str):
    """Send Google Sheet link to the user (using Google Drive API for sharing)"""
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    # Mở Google Sheet và chia sẻ quyền chỉnh sửa qua Drive API
    service = get_drive_service()  # Lấy dịch vụ Google Drive
    try:
        # Chia sẻ quyền chỉnh sửa với email người dùng
        service.permissions().create(
            fileId=sheet_id,
            body={
                'type': 'user',
                'role': 'writer',
                'emailAddress': user_email
            }
        ).execute()

        # Tạo nút "GOOGLE SHEET"
        keyboard = [[InlineKeyboardButton("📊 GOOGLE SHEET", url=sheet_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Gửi tin nhắn với nút bấm
        await update.message.reply_text(f"Email của bạn đã được thêm! 📝 Click nút dưới đây để mở Google Sheet của bạn:", reply_markup=reply_markup)

    except HttpError as error:
        await update.message.reply_text(f"❌ Lỗi khi chia sẻ quyền: {error}")