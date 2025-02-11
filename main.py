import config
from telegram.ext import Application
from utils.logger import setup_logger
from utils.handler_loader import load_handlers
from handlers.error_handler import error_handler_instance
from commands.help import get_handlers as get_help_handlers

logger = setup_logger(__name__)

def main():
    app = Application.builder().token(config.TOKEN).build()

    # Load handlers from commands and handlers
    handler_paths = ["commands", "handlers"]
    load_handlers(app, handler_paths)

    # Add error handler
    app.add_error_handler(error_handler_instance)

    # Add help handler
    app.add_handler(get_help_handlers())
    
    logger.info(f"Bot {config.BOT_USERNAME} is running!")
    # Webhook config for Railway
    # WEBHOOK_URL = f"https://{config.SERVER_DOMAIN}/webhook/{config.TOKEN}"
    # app.run_webhook(
    #     listen="0.0.0.0",
    #     port=int(config.SERVER_PORT),
    #     webhook_url=WEBHOOK_URL,
    # )
    app.run_polling(poll_interval=3)

if __name__ == "__main__":
    main()