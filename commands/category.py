from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes, CallbackContext
from services.category_crud_service import add_category, get_categories, delete_category, update_category

async def list_categories(update: Update, context: CallbackContext):
    """Liệt kê các categories (async)"""
    user_id = update.message.from_user.id
    categories = await get_categories(user_id)  
    if not categories:
        await update.message.reply_text("Chưa có categories nào.")
    else:
        categories_text = "\n".join([f"{idx + 1}. {category}" for idx, category in enumerate(categories)])
        await update.message.reply_text(f"📂 Danh sách Categories:\n{categories_text}")

async def add_category_handler(update: Update, context: CallbackContext):
    """Thêm category mới (async)"""
    user_id = update.message.from_user.id
    category_name = " ".join(context.args)
    if not category_name:
        await update.message.reply_text("Vui lòng nhập tên category.")
        return

    result = await add_category(user_id, category_name)  
    await update.message.reply_text(result)

async def delete_category_handler(update: Update, context: CallbackContext):
    """Xóa category (async)"""
    user_id = update.message.from_user.id
    category_name = " ".join(context.args)
    if not category_name:
        await update.message.reply_text("Vui lòng nhập tên category để xóa.")
        return

    result = await delete_category(user_id, category_name)
    await update.message.reply_text(result)

async def update_category_handler(update: Update, context: CallbackContext):
    """Cập nhật tên category (async)"""
    user_id = update.message.from_user.id
    args = " ".join(context.args).split(", ")
    if len(args) < 2:
        await update.message.reply_text("Vui lòng nhập: /update_cate <tên cũ>, <tên mới>")
        return

    old_name, new_name = args[0], args[1]
    result = await update_category(user_id, old_name, new_name)
    await update.message.reply_text(result)


def get_handlers():
    return [
        CommandHandler("add_cate", add_category_handler),
        CommandHandler("list_cate", list_categories),
        CommandHandler("delete_cate", delete_category_handler),
        CommandHandler("update_cate", update_category_handler),
    ]
