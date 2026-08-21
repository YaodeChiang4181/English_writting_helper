from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
from telegram.constants import ChatAction
from .gemini_service import review_peel_writing

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

async def receive_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['link'] = update.message.text
    
    await update.message.reply_chat_action(ChatAction.TYPING)
    await update.message.reply_text("⏳ 感謝你的輸入！AI 教練正在仔細審核你的文章，請稍候...")
    
    point = context.user_data.get('point', '')
    explanation = context.user_data.get('explanation', '')
    example = context.user_data.get('example', '')
    link = context.user_data.get('link', '')
    
    report = await review_peel_writing(point, explanation, example, link)
    
    try:
        await update.message.reply_text(report, parse_mode='Markdown')
    except Exception:
        # Fallback to plain text if markdown parsing fails
        await update.message.reply_text(report)
    
    # Clear user data
    context.user_data.clear()
    
    return ConversationHandler.END

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
        LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_link)],
    },
    fallbacks=[CommandHandler('cancel', cancel_command)],
)
