import logging
import asyncio
from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from app.core.config import settings
from app.agents.supervisor import run_principal_turn

logger = logging.getLogger(__name__)

# Memoria de sesión en RAM (últimos 6 turnos)
chat_histories: Dict[int, list] = {}

def get_principal_id_by_user_id(user_id: int) -> Optional[str]:
    """Identifica si el remitente es Principal A o Principal B."""
    if settings.telegram_user_id_francisco and user_id == settings.telegram_user_id_francisco:
        return "principal_a"
    if settings.telegram_user_id_esposa and user_id == settings.telegram_user_id_esposa:
        return "principal_b"
    return None

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    principal_id = get_principal_id_by_user_id(user_id)
    
    # Si no hay IDs configurados en .env, permite el acceso de prueba e informa el ID al usuario
    p_name = "Principal A" if (principal_id == "principal_a" or not principal_id) else "Principal B"
    
    await update.message.reply_text(
        f"🏛️ **Bienvenido a Ágora** (`{p_name}`)\n\n"
        f"Tu Telegram User ID es: `{user_id}`\n\n"
        "- 🖥️ Consultar estado del Homelab y Docker\n"
        "- 💼 Consultar ofertas de empleo en PulseHunter\n"
        "- 📚 Buscar y guardar notas en tu bóveda privada de Obsidian\n"
        "- 📩 Enviar mensajes y recordatorios al otro Principal\n\n"
        "¿En qué puedo ayudarte hoy?",
        parse_mode="Markdown"
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text
    
    # Determinar qué Principal está hablando
    principal_id = get_principal_id_by_user_id(user_id) or "principal_a"
    
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    history = chat_histories[user_id]
    
    # Efecto 'escribiendo...'
    await update.message.chat.send_action("typing")

    # Función auxiliar para notificaciones cruzadas
    async def peer_notify(target_principal: str, msg: str):
        target_uid = settings.telegram_user_id_esposa if target_principal == "principal_b" else settings.telegram_user_id_francisco
        if target_uid and context.bot:
            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=f"📩 **Notificación de {principal_id.upper()}**:\n{msg}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Error enviando mensaje cruzado a {target_uid}: {e}")

    try:
        response_text = await run_principal_turn(
            user_message=user_text,
            principal_id=principal_id,
            conversation_history=history[-6:],
            peer_notifier=peer_notify
        )
    except Exception as e:
        response_text = f"⚠️ Error en el procesamiento del agente: {e}"

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response_text})

    await update.message.reply_text(response_text, parse_mode="Markdown")

def start_telegram_bot_service():
    """Inicia el bot de Telegram escuchando eventos."""
    token = settings.telegram_bot_token_principal_a or settings.telegram_bot_token_principal_b
    if not token:
        print("⚠️ No hay TELEGRAM_BOT_TOKEN configurado en el archivo .env.")
        print("ℹ️ Para activar Telegram, añade tu token en /home/colls/github/agora/.env")
        return

    print("🤖 Iniciando Ágora Telegram Ingress Service...")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()
