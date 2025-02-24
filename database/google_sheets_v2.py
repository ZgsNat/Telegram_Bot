from turtle import color
import asyncio
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
sync_client = gspread.authorize(CREDS)

def get_credentials():
    """Tải Google Service Account Credentials"""
    return Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

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
    """Định dạng worksheet cho một tháng, chỉ gọi tối đa 1 lần API để tránh quá tải"""

    # ✅ Kết nối với Google Sheets
    client = await get_google_client()
    sheet = await client.open_by_key(spreadsheet_id)
    real_ws = await sheet.worksheet(ws.title)
    service_account_email = CREDS.service_account_email  # Email of the service account
    try:
        # ✅ Batch: Ghi dữ liệu, merge ô, khóa ô, và định dạng
        batch_updates = {
            "requests": [
                # Ghi dữ liệu
                {"updateCells": {
                    "range": a1_to_grid_range("A1:A1", real_ws.id),
                    "rows": [{"values": [{"userEnteredValue": {"stringValue": "Thu Chi"}}]}],
                    "fields": "userEnteredValue"
                }},
                {"updateCells": {
                    "range": a1_to_grid_range("G1:G1", real_ws.id),
                    "rows": [{"values": [{"userEnteredValue": {"stringValue": "Tiết Kiệm"}}]}],
                    "fields": "userEnteredValue"
                }},
                {"updateCells": {
                    "range": a1_to_grid_range("L1:L1", real_ws.id),
                    "rows": [{"values": [{"userEnteredValue": {"stringValue": "Hạn mức chi tiêu"}}]}],
                    "fields": "userEnteredValue"
                }},
                {"updateCells": {
                    "range": a1_to_grid_range("A3:E3", real_ws.id),
                    "rows": [{"values": [
                        {"userEnteredValue": {"stringValue": "Ngày"}},
                        {"userEnteredValue": {"stringValue": "Thu"}},
                        {"userEnteredValue": {"stringValue": "Chi"}},
                        {"userEnteredValue": {"stringValue": "Loại"}},
                        {"userEnteredValue": {"stringValue": "Mô tả"}}
                    ]}],
                    "fields": "userEnteredValue"
                }},
                {"updateCells": {
                    "range": a1_to_grid_range("G3:J3", real_ws.id),
                    "rows": [{"values": [
                        {"userEnteredValue": {"stringValue": "Ngày"}},
                        {"userEnteredValue": {"stringValue": "Tiết kiệm"}},
                        {"userEnteredValue": {"stringValue": "Loại"}},
                        {"userEnteredValue": {"stringValue": "Mô tả"}}
                    ]}],
                    "fields": "userEnteredValue"
                }},
                {"updateCells": {
                    "range": a1_to_grid_range("L3:O3", real_ws.id),
                    "rows": [{"values": [
                        {"userEnteredValue": {"stringValue": "Mục"}},
                        {"userEnteredValue": {"stringValue": "Hạn mức"}},
                        {"userEnteredValue": {"stringValue": "Đã chi"}},
                        {"userEnteredValue": {"stringValue": "Còn lại"}}
                    ]}],
                    "fields": "userEnteredValue"
                }},
                # Merge ô tiêu đề chính
                {"mergeCells": {"range": a1_to_grid_range("A1:E2", real_ws.id)}},
                {"mergeCells": {"range": a1_to_grid_range("G1:J2", real_ws.id)}},
                {"mergeCells": {"range": a1_to_grid_range("L1:O2", real_ws.id)}},
                # Khóa header (hàng 1-3)
                {"addProtectedRange": {
                    "protectedRange": {
                        "range": a1_to_grid_range("A1:O3", real_ws.id),
                        "description": "Khóa header",
                        "warningOnly": False,  # Chặn hoàn toàn, không chỉ cảnh báo
                        "editors": {
                            "users": [service_account_email]  # Allow the service account to edit
                        }
                    }
                }},
                # Định dạng header chính
                {"repeatCell": {
                    "range": a1_to_grid_range("A1:E2", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.3, "green": 0.6, "blue": 1},
                        "textFormat": {"bold": True, "fontSize": 15, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("G1:J2", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.3, "green": 0.6, "blue": 1},
                        "textFormat": {"bold": True, "fontSize": 15, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("L1:O2", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.3, "green": 0.6, "blue": 1},
                        "textFormat": {"bold": True, "fontSize": 15, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }},
                # Định dạng header phụ
                {"repeatCell": {
                    "range": a1_to_grid_range("A3:E3", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("G3:J3", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("L3:O3", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
                        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                }},
                # Định dạng dữ liệu người dùng nhập
                {"repeatCell": {
                    "range": a1_to_grid_range("A4:O500", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "textFormat": {"foregroundColor": {"red": 0, "green": 0, "blue": 0}},
                        "horizontalAlignment": 'CENTER',
                        "verticalAlignment": 'MIDDLE'
                    }},
                    "fields": "userEnteredFormat(textFormat,horizontalAlignment,verticalAlignment)"
                }},
                # Định dạng số với dấu phân cách hàng nghìn
                {"repeatCell": {
                    "range": a1_to_grid_range("B4:B500", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }},
                    "fields": "userEnteredFormat(numberFormat)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("C4:C500", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }},
                    "fields": "userEnteredFormat(numberFormat)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("M4:M500", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }},
                    "fields": "userEnteredFormat(numberFormat)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("N4:N500", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }},
                    "fields": "userEnteredFormat(numberFormat)"
                }},
                {"repeatCell": {
                    "range": a1_to_grid_range("O4:O500", real_ws.id),
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}
                    }},
                    "fields": "userEnteredFormat(numberFormat)"
                }},
                # Định dạng có điều kiện (Xanh: Thu, Đỏ: Chi)
                {"addConditionalFormatRule": {
                    "rule": {
                        "ranges": [a1_to_grid_range("B4:B500", real_ws.id)],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                            "format": {"backgroundColor": {"red": 0.6, "green": 1, "blue": 0.6}}
                        }
                    },
                    "index": 0
                }},
                {"addConditionalFormatRule": {
                    "rule": {
                        "ranges": [a1_to_grid_range("C4:C500", real_ws.id)],
                        "booleanRule": {
                            "condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
                            "format": {"backgroundColor": {"red": 1, "green": 0.6, "blue": 0.6}}
                        }
                    },
                    "index": 0
                }}
            ]
        }

        service = build("sheets", "v4", credentials=CREDS)
        response = await asyncio.to_thread(service.spreadsheets().batchUpdate, spreadsheetId=spreadsheet_id, body=batch_updates)
        response = response.execute()  # Chạy trong luồng riêng để không block event loop

        return ws

    except Exception as e:
        print(f"Error in format_month_worksheet: {e}")
        raise

async def remove_all_protected_ranges(ws):
    """Xóa toàn bộ các vùng bảo vệ trên sheet hiện tại."""
    service = build("sheets", "v4", credentials=CREDS)
    sheet_id = ws.spreadsheet.id
    sheet_name = ws.title  # Lấy tên sheet để debug

    # Lấy danh sách tất cả các vùng bảo vệ
    try:
        response = await asyncio.to_thread(
            lambda: service.spreadsheets().get(spreadsheetId=sheet_id, fields="sheets(protectedRanges,properties)").execute()
        )
    except Exception as e:
        return f"⚠ Lỗi khi lấy danh sách vùng bảo vệ trên {sheet_name}: {e}"

    # Debug: In ra response để xem API có trả đúng dữ liệu không
    # print(f"📜 Response từ Google Sheets API: {response}")

    # Tìm danh sách protectedRanges của sheet hiện tại
    protected_ranges = []
    for sheet in response.get("sheets", []):
        sheet_properties = sheet.get("properties", {})
        if sheet_properties.get("sheetId") == ws.id and "protectedRanges" in sheet:
            protected_ranges = sheet["protectedRanges"]
            break  # Tìm thấy sheet phù hợp thì thoát vòng lặp

    if not protected_ranges:
        return f"🟢 Không có vùng bảo vệ nào trên {sheet_name} để xóa."

    # Xây dựng request để xóa từng protectedRange
    requests = [
        {"deleteProtectedRange": {"protectedRangeId": pr["protectedRangeId"]}}
        for pr in protected_ranges
    ]

    # Gửi request xóa
    try:
        await asyncio.to_thread(
            lambda: service.spreadsheets().batchUpdate(spreadsheetId=sheet_id, body={"requests": requests}).execute()
        )
        return f"🗑 Đã xóa {len(protected_ranges)} vùng bảo vệ trên {sheet_name}."
    except Exception as e:
        return f"⚠ Lỗi khi xóa vùng bảo vệ trên {sheet_name}: {e}"


async def protect_range(ws, cell_range):
    """Khóa phạm vi ô để tránh chỉnh sửa (Async)"""
    sheet_id = ws.spreadsheet.id
    owner_email = CREDS.service_account_email  # Email của chủ sở hữu (Service Account)

    # Lấy danh sách các email có quyền chỉnh sửa
    service = build("drive", "v3", credentials=CREDS)
    permissions = await asyncio.to_thread(service.permissions().list, fileId=sheet_id, fields="permissions(emailAddress, role)")
    permissions = permissions.execute()  # Chạy trong luồng riêng tránh block

    editors = [perm['emailAddress'] for perm in permissions.get('permissions', []) if perm['role'] == 'writer']

    # Convert A1 notation to grid range
    grid_range = a1_to_grid_range(cell_range, ws.id)
    
    body = {
        "requests": [
            {
                "addProtectedRange": {
                    "protectedRange": {
                        "range": grid_range,  # Use the converted grid range
                        "description": "Chặn chỉnh sửa header",
                        "warningOnly": False,  # Chặn hoàn toàn, không chỉ cảnh báo
                        "editors": {
                            "users": editors  # Cho phép tất cả các email có quyền chỉnh sửa
                        }
                    }
                }
            }
        ]
    }

    # ✅ Thay thế cách lấy Google Sheets API
    service = build("sheets", "v4", credentials=CREDS)
    
    response = await asyncio.to_thread(service.spreadsheets().batchUpdate, spreadsheetId=sheet_id, body=body)
    response = response.execute()  # Chạy trong luồng riêng để không block event loop

    return response  # Trả về kết quả từ API (hoặc return True nếu không cần)

def a1_to_grid_range(a1_range, sheet_id):
    """
    Convert A1 notation to GridRange object for Google Sheets API.
    """
    from gspread.utils import a1_range_to_grid_range
    grid_range = a1_range_to_grid_range(a1_range)
    grid_range['sheetId'] = sheet_id
    return grid_range

def apply_conditional_format(ws, col_range, condition, value, color):
    """Áp dụng định dạng có điều kiện (bắt đầu từ dòng 3, không format header)"""
    
    # Chuyển đổi condition thành định dạng hợp lệ
    condition_map = {
        ">": "NUMBER_GREATER",
        ">=": "NUMBER_GREATER_THAN_EQ",
        "<": "NUMBER_LESS",
        "<=": "NUMBER_LESS_THAN_EQ",
        "==": "NUMBER_EQ",
        "!=": "NUMBER_NOT_EQ"
    }

    if condition not in condition_map:
        raise ValueError(f"Điều kiện không hợp lệ: {condition}")

    # Convert A1 notation to grid range
    grid_range = a1_to_grid_range(col_range, ws.id)

    rules = get_conditional_format_rules(ws)
    rule = ConditionalFormatRule(
        ranges=[grid_range],  # Use the converted grid range
        booleanRule=BooleanRule(
            condition=BooleanCondition(condition_map[condition], [value]),
            format=CellFormat(backgroundColor=color)
        )
    )
    rules.append(rule)
    rules.save()  # Lưu lại rule vào Google Sheets

    # Apply number format with thousand separator
    apply_number_format(ws, col_range)

def apply_number_format(ws, col_range):
    """Áp dụng định dạng số với dấu phân cách hàng nghìn"""
    # Convert A1 notation to grid range
    grid_range = a1_to_grid_range(col_range, ws.id)

    number_format = CellFormat(
        numberFormat=NumberFormat(type="NUMBER", pattern="#,##0")
    )
    format_cell_range(ws, grid_range, number_format)  # Use the converted grid range

async def create_or_get_worksheet(spreadsheet_id, title):
    """Tạo hoặc lấy worksheet theo tiêu đề"""
    sheet = sync_client.open_by_key(spreadsheet_id)
    try:
        ws = sheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = sheet.add_worksheet(title=title, rows="100", cols="20")
    return ws

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