from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from telegram.constants import ChatAction
from .gemini_service import review_peel_writing, review_peel_writing_batch

pending_submissions = []

async def batch_process_job(context: ContextTypes.DEFAULT_TYPE):
    if not pending_submissions:
        return
    
    # Process up to 5 submissions at a time
    batch_size = 5
    batch = pending_submissions[:batch_size]
    del pending_submissions[:batch_size]
    
    reports = await review_peel_writing_batch(batch)
    
    for i, report in enumerate(reports):
        chat_id = batch[i]['chat_id']
        
        if report.startswith("⚠️"):
            error_msg = f"{report}\n\n💡 伺服器處理失敗，請重新輸入 /write 再試一次。"
            try:
                await context.bot.send_message(chat_id=chat_id, text=error_msg, parse_mode='Markdown')
            except Exception:
                pass
            continue
            
        chunks = split_message(report)
        for chunk in chunks:
            try:
                await context.bot.send_message(chat_id=chat_id, text=chunk, parse_mode='Markdown')
            except Exception:
                await context.bot.send_message(chat_id=chat_id, text=chunk)


# Define states
POINT, EXPLANATION, EXAMPLE, LINK = range(4)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_text = (
        "👋 歡迎使用 PEEL 英文架構寫作小幫手！\n\n"
        "我會協助你依照 PEEL (Point, Explanation, Example, Link) 的架構來組織英文段落，並提供專業的審核與修改建議。\n\n"
        "請輸入 /write 開始練習，或輸入 /cancel 隨時中斷。"
    )
    await update.message.reply_text(welcome_text)

async def write_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "📝 讓我們開始吧！\n\n"
        "**第一步：Point (主張)**\n"
        "請輸入你的核心主張或主題句："
    )
    return POINT

async def receive_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['point'] = update.message.text
    await update.message.reply_text(
        "✅ 收到了！\n\n"
        "**第二步：Explanation (解釋)**\n"
        "請進一步解釋你的主張，說明為什麼這是重要的："
    )
    return EXPLANATION

async def receive_explanation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['explanation'] = update.message.text
    await update.message.reply_text(
        "✅ 很好的解釋！\n\n"
        "**第三步：Example (舉例)**\n"
        "請提供一個具體的例子來佐證你的解釋："
    )
    return EXAMPLE

async def receive_example(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['example'] = update.message.text
    await update.message.reply_text(
        "✅ 例子很棒！\n\n"
        "**最後一步：Link (結論與連結)**\n"
        "請總結這個段落，並將結論扣回你一開始的主張："
    )
    return LINK

def split_message(text, chunk_size=4000):
    chunks = []
    while len(text) > chunk_size:
        # Find the last double newline within the chunk_size
        split_at = text.rfind('\n\n', 0, chunk_size)
        if split_at == -1:
            split_at = text.rfind('\n', 0, chunk_size)
        if split_at == -1:
            split_at = chunk_size
        
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip()
    
    if text:
        chunks.append(text)
    return chunks

async def process_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    point = context.user_data.get('point', '')
    explanation = context.user_data.get('explanation', '')
    example = context.user_data.get('example', '')
    link = context.user_data.get('link', '')
    
    pending_submissions.append({
        'chat_id': update.effective_chat.id,
        'point': point,
        'explanation': explanation,
        'example': example,
        'link': link,
    })
    
    await update.message.reply_text("⏳ 你的文章已加入批次審核佇列。為了降低 API 用量，系統將定時批次處理多筆文章，請耐心等候幾分鐘...")
    
    # Clear user data since it is queued
    context.user_data.clear()
    
    return ConversationHandler.END

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['link'] = update.message.text
    return await process_submission(update, context)

async def retry_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'link' not in context.user_data:
        await update.message.reply_text("目前沒有保留的草稿喔！請輸入 /write 開始全新寫作。")
        return ConversationHandler.END
    return await process_submission(update, context)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("🚫 已取消本次寫作練習。準備好隨時輸入 /write 再次開始！")
    context.user_data.clear()
    return ConversationHandler.END

# Create the ConversationHandler
peel_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('write', write_command)],
    states={
        POINT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_point)],
        EXPLANATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_explanation)],
        EXAMPLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_example)],
        LINK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link),
            CommandHandler('retry', retry_command)
        ],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_command),
        MessageHandler(filters.COMMAND, cancel_command)
    ],
    allow_reentry=True
)
