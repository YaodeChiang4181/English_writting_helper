import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from src.config import TELEGRAM_BOT_TOKEN
from src.bot_handlers import start_command, peel_conv_handler, batch_process_job
from src.dummy_server import keep_alive

# Set up basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting PEEL Writing Coach Bot...")
    
    # Build application
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(peel_conv_handler)
    
    # Schedule batch processing job every 60 seconds
    if application.job_queue:
        application.job_queue.run_repeating(batch_process_job, interval=60, first=10)
    else:
        logger.warning("JobQueue is not available! Batch processing will not work.")
    
    # Start dummy web server to keep Render happy
    keep_alive()
    
    # Start polling
    logger.info("Bot is now polling...")
    application.run_polling()

if __name__ == '__main__':
    main()
