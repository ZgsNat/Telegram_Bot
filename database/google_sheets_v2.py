import gspread_asyncio
from google.oauth2.service_account import Credentials
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from googleapiclient.discovery import build

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

async def get_google_client():
    """Kết nối với Google Sheets API (bất đồng bộ)"""
    agcm = get_agcm()  # Lấy client manager bất đồng bộ
    return await agcm.authorize()

async def create_user_sheet(user_id, username="User"):
    """Tạo Google Sheet mới nếu chưa có, kèm 12 worksheet cho các tháng."""
    user_sheets = await load_user_sheets()

    # Đặt tên Google Sheet theo định dạng: username_2025 (năm hiện tại)
    from datetime import datetime
    current_year = datetime.now().year
    sheet_name = f"{username}_{current_year}"

    if str(user_id) in user_sheets and user_sheets[str(user_id)].get("year") == current_year:
        return user_sheets[str(user_id)]["sheet_id"]  # Đã tồn tại Google Sheet cho năm hiện tại

    client = await get_google_client()
    sheet = await client.create(sheet_name)  # Tạo Google Sheet mới

    # Tạo 12 worksheet cho các tháng
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    for month in months:
        await sheet.add_worksheet(title=month, rows=100, cols=5)
    
    # Xóa worksheet mặc định ("Sheet1")
    default_sheet = await sheet.worksheet("Sheet1")
    await sheet.del_worksheet(default_sheet)

    await sheet.share(None, perm_type='anyone', role='reader')  # Cho phép mọi người xem

    user_sheets[str(user_id)] = {
        "sheet_id": sheet.id,
        "year": current_year
    }
    await save_user_sheets(user_sheets)

    return sheet.id  # Trả về Sheet ID mới tạo

async def get_user_sheet(user_id):
    """Lấy Google Sheet ID của user"""
    user_sheets = await load_user_sheets()
    return user_sheets.get(str(user_id), None)

async def get_worksheet(user_id):
    """Lấy worksheet của user"""
    sheet_id = await get_user_sheet(user_id)
    if not sheet_id:
        return None  # User chưa có Google Sheet

    client = await get_google_client()
    sheet = await client.open_by_key(sheet_id)

    # Kiểm tra xem có worksheet "Categories" chưa, nếu chưa thì tạo mới
    try:
        return await sheet.worksheet("Categories")
    except gspread_asyncio.exceptions.WorksheetNotFound:
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