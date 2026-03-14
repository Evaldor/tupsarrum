import logging_config  # Must be first
import logging
from fastapi import FastAPI
from config import TELEGRAM_BOT_TOKEN
import threading
import asyncio
from telegram import Bot
from telegram.error import TelegramError
#from redis_utils import RedisStateManager
from graph_utils import GraphManager
from conversation_state import ConversationState


logger = logging.getLogger(__name__)

app = FastAPI(title="AI-tupsarrum", version="1.0.0")


graph_manager = GraphManager()
message_graph = graph_manager.create_message_graph()

def prepare_conversation_state(request_user, request_text):
    state = ConversationState()
    state['user'] = request_user
    state['incoming_message'] = request_text
    return state

def split_message(text, max_length=4096):
    """Split a long message into chunks of max_length."""
    messages = []
    while len(text) > max_length:
        # Find the last space before max_length to avoid cutting words
        cut_point = text.rfind(' ', 0, max_length)
        if cut_point == -1:
            cut_point = max_length
        messages.append(text[:cut_point])
        text = text[cut_point:].strip()
    if text:
        messages.append(text)
    return messages

async def poll_telegram():
    """Обрабатывает поток сообщений в tg Бота."""
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    try:
        await bot.delete_webhook()
    except Exception as e:
        logger.error("Failed to delete webhook", extra={"error": str(e)})
    last_update_id = 0
    while True:
        try:
            updates = await bot.get_updates(offset=last_update_id + 1, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    chat_id = update.message.chat.id
                    username = update.message.from_user.username or str(update.message.from_user.id)
                    request_text = update.message.text
                    state = prepare_conversation_state(username, request_text)
                    result = await message_graph.ainvoke(state)

                    message_text = result['phrase_ru']

                    messages = split_message(message_text)
                    for msg in messages:
                        await bot.send_message(chat_id=chat_id, text=msg)

                    logger.info("Processed TG message", extra={"chat_id": chat_id, "username": username})
                
                last_update_id = update.update_id
        except TelegramError as e:
            logger.error("Telegram error", extra={"error": str(e)})
        except Exception as e:
            logger.error("Error polling Telegram", extra={"error": str(e)})
        await asyncio.sleep(10)  # Poll every 10 seconds

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=lambda: asyncio.run(poll_telegram()), daemon=True).start()

@app.get("/health")
async def health():
    return {"status": "healthy"}