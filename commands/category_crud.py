from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes

# List of categories (placeholder, will be replaced with Excel operations)
CATEGORIES = []

async def add_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a new category."""
    if len(context.args) == 0:
        await update.message.reply_text("Please enter the category name after the /add_category command.")
        return

    category_name = " ".join(context.args)
    if category_name in CATEGORIES:
        await update.message.reply_text(f"Category '{category_name}' already exists.")
        return

    CATEGORIES.append(category_name)
    await update.message.reply_text(f"Category '{category_name}' has been successfully added!")

async def list_categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all categories."""
    category_list = "\n".join(CATEGORIES) if CATEGORIES else "No categories available."
    await update.message.reply_text(f"Current list of categories:\n{category_list}")

async def delete_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a category."""
    if len(context.args) == 0:
        await update.message.reply_text("Please enter the category name after the /delete_category command.")
        return

    category_name = " ".join(context.args)
    if category_name not in CATEGORIES:
        await update.message.reply_text(f"Category '{category_name}' does not exist.")
        return

    CATEGORIES.remove(category_name)
    await update.message.reply_text(f"Category '{category_name}' has been successfully deleted!")

async def update_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update a category."""
    if len(context.args) < 2:
        await update.message.reply_text("Please enter the old and new category names after the /update_category command.")
        return

    old_category = context.args[0]
    new_category = " ".join(context.args[1:])

    if old_category not in CATEGORIES:
        await update.message.reply_text(f"Category '{old_category}' does not exist.")
        return

    if new_category in CATEGORIES:
        await update.message.reply_text(f"Category '{new_category}' already exists.")
        return

    CATEGORIES[CATEGORIES.index(old_category)] = new_category
    await update.message.reply_text(f"Category '{old_category}' has been updated to '{new_category}'!")

def get_handlers():
    return [
        CommandHandler("add_category", add_category_command),
        CommandHandler("list_categories", list_categories_command),
        CommandHandler("delete_category", delete_category_command),
        CommandHandler("update_category", update_category_command),
    ]
