import config
from telegram.ext import Application
from utils.logger import setup_logger
from utils.handler_loader import load_handlers

logger = setup_logger(__name__)

def main():
    app = Application.builder().token(config.TOKEN).build()

    # Load handlers từ commands và handlers
    handler_paths = ["commands", "handlers"]
    load_handlers(app, handler_paths)

    logger.info(f"Bot @{config.BOT_USERNAME} is running!")
    app.run_polling()

if __name__ == "__main__":
    main()