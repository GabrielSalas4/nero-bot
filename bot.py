import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

ASESOR_CHAT_ID = "8972445796"
TOKEN = "8719440741:AAGR7YkT4RWdCJ11kXZ0ln3LQvRZFfUcqn4"


def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ ¿Qué es Nero?", callback_data="que_es")],
        [InlineKeyboardButton("2️⃣ ¿Cómo funciona?", callback_data="como_funciona")],
        [InlineKeyboardButton("3️⃣ Deseo registrarme", callback_data="registro")],
        [InlineKeyboardButton("4️⃣ Comunicarme con un asesor", callback_data="asesor")],
    ])


def volver_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Volver al menú principal", callback_data="menu")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, te saluda *Nero*.\n\nSelecciona una opción:",
        reply_markup=menu_keyboard(),
        parse_mode="Markdown",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "menu":
        await query.edit_message_text(
            "👋 Hola, te saluda *Nero*.\n\nSelecciona una opción:",
            reply_markup=menu_keyboard(),
            parse_mode="Markdown",
        )

    elif query.data == "que_es":
        await query.edit_message_text(
            "1️⃣ *¿Qué es Nero?*\n\n"
            "💳 Nero es tu aliado para acceder a préstamos, ayudándote a construir "
            "un puntaje financiero basado en tus hábitos y compromiso.",
            reply_markup=volver_keyboard(),
            parse_mode="Markdown",
        )

    elif query.data == "como_funciona":
        await query.edit_message_text(
            "2️⃣ *¿Cómo funciona?*\n\n"
            "📈 En Nero todos empiezan desde cero y construyen su puntaje financiero paso a paso.\n\n"
            "Puedes crecer de dos maneras:\n\n"
            "💰 *1. Modalidad de deuda programada*\n"
            "La forma más rápida de construir tu puntaje, demostrando disciplina y cumplimiento en pagos.\n\n"
            "📂 *2. Compartiendo información verificada*\n"
            "Puedes subir y actualizar información financiera, laboral y de residencia que validamos periódicamente. "
            "Funciona como un sistema de puntos donde tu compromiso suma, aunque toma un poco más de tiempo por el proceso de verificación.\n\n"
            "⭐ Entre mayor sea tu puntaje, mayores oportunidades tendrás de acceder a préstamos con Nero o aliados.",
            reply_markup=volver_keyboard(),
            parse_mode="Markdown",
        )

    elif query.data == "registro":
        await query.edit_message_text(
            "3️⃣ *Deseo registrarme*\n\n"
            "¡Perfecto! Completa tu registro aquí 👇\n\n"
            "🔗 https://tally.so/r/A79JR0",
            reply_markup=volver_keyboard(),
            parse_mode="Markdown",
        )

    elif query.data == "asesor":
        user = query.from_user
        nombre = user.full_name
        username = f"@{user.username}" if user.username else "sin usuario"
        user_id = user.id

        try:
            await context.bot.send_message(
                chat_id=ASESOR_CHAT_ID,
                text=(
                    f"📩 *Nuevo usuario quiere hablar con un asesor*\n\n"
                    f"👤 Nombre: {nombre}\n"
                    f"🔗 Usuario: {username}\n"
                    f"🆔 ID: `{user_id}`\n\n"
                    f"Puedes responderle abriendo su perfil en Telegram."
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(f"No se pudo notificar al asesor: {e}")

        await query.edit_message_text(
            "4️⃣ *Comunicarme con un asesor*\n\n"
            "✅ ¡Listo! Un asesor se pondrá en contacto contigo muy pronto.\n\n"
            "⏰ Nuestro horario de atención es de lunes a viernes, 8am – 6pm.",
            parse_mode="Markdown",
        )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, te saluda *Nero*.\n\nSelecciona una opción:",
        reply_markup=menu_keyboard(),
        parse_mode="Markdown",
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    logger.info("Bot Nero iniciado ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
