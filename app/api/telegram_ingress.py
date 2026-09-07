import logging
import asyncio
from typing import Dict, Any, Optional
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from app.core.config import settings
from app.agents.supervisor import run_principal_turn

# Configurar logging detallado para diagnóstico en vivo
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("agora.telegram")

# Memoria de sesión en RAM (últimos 6 turnos)
chat_histories: Dict[int, list] = {}

def get_principal_id_by_user_id(user_id: int) -> Optional[str]:
    """Identifica si el remitente es Principal A o Principal B."""
    if settings.telegram_user_id_principal_a and user_id == settings.telegram_user_id_principal_a:
        return "principal_a"
    if settings.telegram_user_id_principal_b and user_id == settings.telegram_user_id_principal_b:
        return "principal_b"
    return None

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    principal_id = get_principal_id_by_user_id(user_id) or "principal_a"
    p_name = "Principal A" if principal_id == "principal_a" else "Principal B"
    logger.info(f"Comando /start recibido de {user_id} ({p_name})")
    
    await update.message.reply_text(
        f"🏛️ Bienvenido a Ágora ({p_name})\n\n"
        f"Tu Telegram User ID es: {user_id}\n\n"
        "- 🖥️ Consultar estado del Homelab y Docker\n"
        "- 💼 Consultar ofertas de empleo en PulseHunter\n"
        "- 📚 Buscar y guardar notas en tu bóveda privada de Obsidian\n"
        "- 📩 Enviar mensajes y recordatorios al otro Principal\n\n"
        "¿En qué puedo ayudarte hoy?"
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_text = update.message.text
    principal_id = get_principal_id_by_user_id(user_id) or "principal_a"
    
    logger.info(f"📩 [PROCESANDO] Mensaje recibido de [{principal_id}] (ID: {user_id}): '{user_text}'")
    
    if user_id not in chat_histories:
        chat_histories[user_id] = []
    
    history = chat_histories[user_id]
    
    # Efecto 'escribiendo...'
    try:
        await update.message.chat.send_action("typing")
    except Exception as e:
        logger.warning(f"No se pudo enviar typing action: {e}")

    async def peer_notify(target_principal: str, msg: str):
        target_uid = settings.telegram_user_id_principal_b if target_principal == "principal_b" else settings.telegram_user_id_principal_a
        if target_uid and context.bot:
            try:
                await context.bot.send_message(
                    chat_id=target_uid,
                    text=f"📩 Notificación de {principal_id.upper()}:\n{msg}"
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
        logger.info(f"🤖 [GENERADA] Respuesta para {user_id}: {response_text[:80]}...")
    except Exception as e:
        logger.error(f"Error procesando turno del agente: {e}", exc_info=True)
        response_text = f"⚠️ Error en el procesamiento del agente: {e}"

    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": response_text})

    try:
        await update.message.reply_text(response_text)
        logger.info(f"✅ [ENVIADA] Respuesta entregada con éxito a Telegram para {user_id}")
    except Exception as e:
        logger.error(f"Error enviando reply a Telegram: {e}", exc_info=True)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Captura y muestra cualquier error no controlado en los logs."""
    logger.error(f"Excepción en Telegram Bot Ingress: {context.error}", exc_info=context.error)

def start_telegram_bot_service():
    """Inicia el bot de Telegram escuchando eventos."""
    token = settings.telegram_bot_token_principal_a or settings.telegram_bot_token_principal_b
    if not token:
        print("⚠️ No hay TELEGRAM_BOT_TOKEN configurado en el archivo .env.")
        return

    print("🤖 Iniciando Ágora Telegram Ingress Service...")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_error_handler(error_handler)

    app.run_polling(drop_pending_updates=False, allowed_updates=Update.ALL_TYPES)
