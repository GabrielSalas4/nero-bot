
import os
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN", "REEMPLAZAR_TOKEN")
ASESOR_CHAT_ID = "8972445796"
TALLY_URL = "https://tally.so/r/A79JR0"

(
    CEDULA, CAPITAL, FRECUENCIA, CUOTAS,
    ASESOR_NOMBRE, ASESOR_CELULAR
) = range(6)

def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Solicitar un préstamo", callback_data="prestamo")],
        [InlineKeyboardButton("📝 Registrarme", url=TALLY_URL)],
        [InlineKeyboardButton("🎧 Hablar con un asesor", callback_data="asesor")]
    ])

def frecuencia_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Quincenal", callback_data="quincenal"),
         InlineKeyboardButton("Mensual", callback_data="mensual")]
    ])

def autorizacion_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Autorizo", callback_data="autorizo")],
        [InlineKeyboardButton("❌ No autorizo", callback_data="no_autorizo")]
    ])

def asesor_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📄 Puntaje Nero y estado de cuenta", callback_data="puntaje")],
        [InlineKeyboardButton("⚠️ PQR", callback_data="pqr")],
        [InlineKeyboardButton("💬 Saber más de Nero", callback_data="nero")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    text = "Hola 👋, te saluda Nero tu aliado crediticio 24/7\n\nEscoge una opción:"
    if update.message:
        await update.message.reply_text(text, reply_markup=menu_keyboard())
    else:
        await update.callback_query.edit_message_text(text, reply_markup=menu_keyboard())

async def prestamo_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "Ingresa tu número de cédula sin puntos ni comas.\nEjemplo: 1001234567"
    )
    return CEDULA

async def cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cedula"] = update.message.text.strip()
    await update.message.reply_text(
        "¿Cuánto capital necesitas?\nEjemplo: 100.000"
    )
    return CAPITAL

async def capital(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["capital"] = update.message.text.strip()
    await update.message.reply_text(
        "¿Cómo prefieres tus abonos?",
        reply_markup=frecuencia_keyboard()
    )
    return FRECUENCIA

async def frecuencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["frecuencia"] = query.data.capitalize()
    await query.edit_message_text(
        "¿En cuántos meses deseas pagarlo?\nEjemplo: 6"
    )
    return CUOTAS

async def cuotas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cuotas"] = update.message.text.strip()

    pdf_path = "DOCUMENTACION NERO.pdf"
    with open(pdf_path, "rb") as doc:
        await update.message.reply_document(
            document=doc,
            caption="Documentación del préstamo Nero"
        )

    await update.message.reply_text(
        "Al seleccionar “Autorizo”, aceptas electrónicamente el préstamo, el pagaré y la carta de instrucciones, autorizando su firma electrónica sin requerir firma física posterior.",
        reply_markup=autorizacion_keyboard()
    )
    return ConversationHandler.WAITING

async def autorizacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "no_autorizo":
        await query.edit_message_text("Solicitud cancelada.")
        return ConversationHandler.END

    user = query.from_user
    data = context.user_data
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    mensaje = f"""📥 NUEVA SOLICITUD NERO

Cédula: {data.get("cedula")}
Capital: {data.get("capital")}
Frecuencia: {data.get("frecuencia")}
Cuotas: {data.get("cuotas")} meses

Firma electrónica: AUTORIZADA
Fecha: {timestamp}
Telegram: @{user.username or 'sin_usuario'}
Telegram ID: {user.id}
"""

    await context.bot.send_message(chat_id=ASESOR_CHAT_ID, text=mensaje)

    await query.edit_message_text(
        "Solicitud recibida ✅\n\nEn contados minutos un asesor se comunicará contigo para confirmar si tu solicitud fue aprobada."
    )
    return ConversationHandler.END

async def asesor_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        "¿En qué podemos ayudarte?",
        reply_markup=asesor_keyboard()
    )

async def asesor_opcion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["motivo"] = query.data
    await query.edit_message_text("Indica tu nombre completo")
    return ASESOR_NOMBRE

async def asesor_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text("Número de celular:")
    return ASESOR_CELULAR

async def asesor_celular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["celular"] = update.message.text.strip()
    d = context.user_data
    await context.bot.send_message(
        chat_id=ASESOR_CHAT_ID,
        text=f"""🎧 NUEVO CONTACTO
Motivo: {d['motivo']}
Nombre: {d['nombre']}
Celular: {d['celular']}"""
    )
    await update.message.reply_text(
        "Listo ✅ Un asesor se comunicará contigo pronto.",
        reply_markup=menu_keyboard()
    )
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_prestamo = ConversationHandler(
        entry_points=[CallbackQueryHandler(prestamo_inicio, pattern="^prestamo$")],
        states={
            CEDULA: [MessageHandler(filters.TEXT & ~filters.COMMAND, cedula)],
            CAPITAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, capital)],
            FRECUENCIA: [CallbackQueryHandler(frecuencia, pattern="^(quincenal|mensual)$")],
            CUOTAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, cuotas)],
            ConversationHandler.WAITING: [CallbackQueryHandler(autorizacion, pattern="^(autorizo|no_autorizo)$")]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    conv_asesor = ConversationHandler(
        entry_points=[CallbackQueryHandler(asesor_inicio, pattern="^asesor$")],
        states={
            ASESOR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, asesor_nombre)],
            ASESOR_CELULAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, asesor_celular)]
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_prestamo)
    app.add_handler(CallbackQueryHandler(asesor_opcion, pattern="^(puntaje|pqr|nero)$"))
    app.add_handler(conv_asesor)
    app.run_polling()

if __name__ == "__main__":
    main()
