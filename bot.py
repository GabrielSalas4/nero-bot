import os
import logging
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
#  CONFIGURACIÓN
# ─────────────────────────────────────────────
TOKEN = "8719440741:AAGR7YkT4RWdCJ11kXZ0ln3LQvRZFfUcqn4"
ASESOR_CHAT_ID = "8972445796"
GOOGLE_SHEETS_ID = "1tMJEUAJ1p5zjH2Z5CxWwkXPeXFhtKOzYLU_v7l7_JKw"
CREDS_FILE = "credentials.json"

# Hojas dentro del Google Sheets
HOJA_CLIENTES = "Clientes"
HOJA_PRESTAMOS = "Prestamos"
HOJA_INVERSORES = "Inversores"
HOJA_ASESORES = "Asesores"

# Estados de conversación
(
    # Registro cliente
    REG_CELULAR, REG_DIRECCION, REG_PIN, REG_AVISO_SOPORTES,
    REG_EXTRACTO1, REG_EXTRACTO2, REG_CEDULA, REG_RECIBO,
    # Login préstamo
    LOAN_CELULAR, LOAN_PIN, LOAN_PERIODICIDAD, LOAN_CONFIRMAR,
    # Inversionista
    INV_OPCION, INV_REG_CELULAR, INV_REG_DIRECCION, INV_REG_PIN,
    INV_LOGIN_CELULAR, INV_LOGIN_PIN,
    # Asesor
    ASESOR_NOMBRE, ASESOR_CELULAR,
) = range(20)


# ─────────────────────────────────────────────
#  GOOGLE SHEETS
# ─────────────────────────────────────────────
def get_sheet(nombre_hoja):
    import json
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    google_creds_env = os.environ.get("GOOGLE_CREDENTIALS")
    if google_creds_env:
        creds_dict = json.loads(google_creds_env)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEETS_ID)
    return sheet.worksheet(nombre_hoja)


def buscar_cliente(celular):
    try:
        ws = get_sheet(HOJA_CLIENTES)
        registros = ws.get_all_records()
        for i, row in enumerate(registros):
            if str(row.get("Celular", "")).strip() == str(celular).strip():
                return row, i + 2  # fila real en sheets (1 header + 1 index)
        return None, None
    except Exception as e:
        logger.error(f"Error buscando cliente: {e}")
        return None, None


def registrar_cliente(datos):
    try:
        ws = get_sheet(HOJA_CLIENTES)
        ws.append_row([
            datos["celular"],
            datos["direccion"],
            datos["pin"],
            datos["extracto1"],
            datos["extracto2"],
            datos["cedula"],
            datos["recibo"],
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ])
        return True
    except Exception as e:
        logger.error(f"Error registrando cliente: {e}")
        return False


def registrar_prestamo(datos):
    try:
        ws = get_sheet(HOJA_PRESTAMOS)
        ws.append_row([
            datos["celular"],
            datos["cupo"],
            datos["plazo"],
            datos["monto"],
            datos["periodicidad"],
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "Pendiente",
        ])
        return True
    except Exception as e:
        logger.error(f"Error registrando préstamo: {e}")
        return False


def registrar_inversor(datos):
    try:
        ws = get_sheet(HOJA_INVERSORES)
        ws.append_row([
            datos["celular"],
            datos["direccion"],
            datos["pin"],
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ])
        return True
    except Exception as e:
        logger.error(f"Error registrando inversor: {e}")
        return False


def registrar_asesor_contacto(datos):
    try:
        ws = get_sheet(HOJA_ASESORES)
        ws.append_row([
            datos["nombre"],
            datos["celular"],
            datetime.now().strftime("%Y-%m-%d %H:%M"),
        ])
        return True
    except Exception as e:
        logger.error(f"Error registrando contacto asesor: {e}")
        return False


# ─────────────────────────────────────────────
#  TECLADOS
# ─────────────────────────────────────────────
def menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 ¿Qué es Nero?", callback_data="que_es")],
        [InlineKeyboardButton("🙋 Quiero un préstamo", callback_data="prestamo")],
        [InlineKeyboardButton("📈 Quiero invertir con Nero", callback_data="invertir")],
        [InlineKeyboardButton("🎧 Hablar con un asesor", callback_data="asesor")],
    ])


def volver_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Volver al menú", callback_data="menu")]
    ])


def registro_login_keyboard(prefijo):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆕 Registrarme", callback_data=f"{prefijo}_registrar")],
        [InlineKeyboardButton("🔐 Iniciar sesión", callback_data=f"{prefijo}_login")],
        [InlineKeyboardButton("🏠 Volver al menú", callback_data="menu")],
    ])


def confirmar_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirmar", callback_data="loan_si"),
            InlineKeyboardButton("❌ Cancelar", callback_data="loan_no"),
        ]
    ])


def periodicidad_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 Quincenal", callback_data="period_quincenal"),
            InlineKeyboardButton("🗓️ Mensual", callback_data="period_mensual"),
        ]
    ])


def continuar_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Sí, continuar", callback_data="reg_continuar")]
    ])


# ─────────────────────────────────────────────
#  BIENVENIDA
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    texto = (
        "👋 Hola, soy Nero.\n"
        "⚠️ Nuestro único canal oficial de comunicación es Telegram. "
        "No operamos por WhatsApp ni ningún otro medio.\n\n"
        "¿Cómo puedo ayudarte?"
    )
    if update.message:
        await update.message.reply_text(texto, reply_markup=menu_keyboard(), parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(texto, reply_markup=menu_keyboard(), parse_mode="Markdown")
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  QUÉ ES NERO
# ─────────────────────────────────────────────
async def que_es(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💳 *¿Qué es Nero?*\n\n"
        "Nero es una plataforma de préstamos DeFi — tu aliado fuera del sistema "
        "para acceder a crédito justo y seguro usando tecnología.\n\n"
        "📊 Construyes un perfil crediticio portable y verificable basado en datos reales. "
        "Entre mayor sea tu puntaje, mejores oportunidades de crédito tendrás con Nero o nuestros aliados.\n\n"
        "Sin bancos. Sin historial previo. Solo tu compromiso abriendo puertas. 🖤",
        reply_markup=volver_keyboard(),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
#  PRÉSTAMO — menú
# ─────────────────────────────────────────────
async def prestamo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["flujo"] = "cliente"
    await query.edit_message_text(
        "🙋 *Quiero un préstamo*\n\n¿Ya tienes cuenta en Nero?",
        reply_markup=registro_login_keyboard("cli"),
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────
#  REGISTRO CLIENTE
# ─────────────────────────────────────────────
async def cli_registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["registro"] = {}
    await query.edit_message_text(
        "🆕 *Registro de cliente*\n\n"
        "¿Cuál es tu número de celular con el que usas Telegram?",
        parse_mode="Markdown",
    )
    return REG_CELULAR


async def reg_celular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    celular = update.message.text.strip()
    existente, _ = buscar_cliente(celular)
    if existente:
        await update.message.reply_text(
            "⚠️ Ya existe una cuenta con ese número.\n"
            "Usa *Iniciar sesión* para continuar.",
            reply_markup=volver_keyboard(),
            parse_mode="Markdown",
        )
        return ConversationHandler.END
    context.user_data["registro"]["celular"] = celular
    await update.message.reply_text("🏠 ¿Cuál es tu dirección de residencia completa?\n_Ejemplo: Calle 72 #45-12, Barranquilla_", parse_mode="Markdown")
    return REG_DIRECCION


async def reg_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registro"]["direccion"] = update.message.text.strip()
    await update.message.reply_text(
        "🔐 Crea tu PIN de seguridad.\n"
        "Escribe 4 dígitos que recuerdes fácilmente.\n\n"
        "⚠️ No compartas tu PIN con nadie, ni con asesores de Nero."
    )
    return REG_PIN


async def reg_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()
    if not pin.isdigit() or len(pin) != 4:
        await update.message.reply_text("❌ El PIN debe ser exactamente 4 dígitos. Intenta de nuevo.")
        return REG_PIN
    context.user_data["registro"]["pin"] = pin
    await update.message.reply_text(
        "📋 En los siguientes pasos te pediremos algunos soportes. Por favor tenlos a la mano:\n\n"
        "• 📄 Extractos bancarios de los últimos 2 meses\n"
        "• 🪪 Foto de tu cédula\n"
        "• 🏠 Recibo de servicios públicos\n\n"
        "¿Estás listo?",
        reply_markup=continuar_keyboard(),
    )
    return REG_AVISO_SOPORTES


async def reg_aviso_continuar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📄 Envíame el extracto bancario del *mes 1* (foto o PDF).", parse_mode="Markdown")
    return REG_EXTRACTO1


async def reg_extracto1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        context.user_data["registro"]["extracto1"] = update.message.document.file_id
    elif update.message.photo:
        context.user_data["registro"]["extracto1"] = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("❌ Por favor envía una foto o PDF.")
        return REG_EXTRACTO1
    await update.message.reply_text("📄 Ahora el extracto bancario del *mes 2*.", parse_mode="Markdown")
    return REG_EXTRACTO2


async def reg_extracto2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.document:
        context.user_data["registro"]["extracto2"] = update.message.document.file_id
    elif update.message.photo:
        context.user_data["registro"]["extracto2"] = update.message.photo[-1].file_id
    else:
        await update.message.reply_text("❌ Por favor envía una foto o PDF.")
        return REG_EXTRACTO2
    await update.message.reply_text("🪪 Envíame una foto clara de tu *cédula*.", parse_mode="Markdown")
    return REG_CEDULA


async def reg_cedula(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["registro"]["cedula"] = update.message.photo[-1].file_id
    elif update.message.document:
        context.user_data["registro"]["cedula"] = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Por favor envía una foto de tu cédula.")
        return REG_CEDULA
    await update.message.reply_text("🏠 Por último, envíame el *recibo de servicios públicos*.", parse_mode="Markdown")
    return REG_RECIBO


async def reg_recibo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        context.user_data["registro"]["recibo"] = update.message.photo[-1].file_id
    elif update.message.document:
        context.user_data["registro"]["recibo"] = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Por favor envía una foto o PDF del recibo.")
        return REG_RECIBO

    ok = registrar_cliente(context.user_data["registro"])
    if ok:
        await update.message.reply_text(
            "✅ ¡Listo! Tus datos fueron guardados correctamente.\n"
            "Un asesor de Nero revisará tu información y se pondrá en contacto contigo pronto.\n\n"
            "¡Bienvenido a la familia Nero! 🖤",
            reply_markup=volver_keyboard(),
        )
    else:
        await update.message.reply_text(
            "⚠️ Hubo un error guardando tus datos. Por favor contacta a un asesor.",
            reply_markup=volver_keyboard(),
        )
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  LOGIN + SOLICITAR PRÉSTAMO
# ─────────────────────────────────────────────
async def cli_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["loan"] = {}
    await query.edit_message_text("🔐 *Iniciar sesión*\n\n¿Cuál es el celular con el que te registraste?", parse_mode="Markdown")
    return LOAN_CELULAR


async def loan_celular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    celular = update.message.text.strip()
    cliente, fila = buscar_cliente(celular)
    if not cliente:
        await update.message.reply_text(
            "❌ No encontramos una cuenta con ese número.\n"
            "Si aún no eres cliente, regístrate primero.",
            reply_markup=volver_keyboard(),
        )
        return ConversationHandler.END
    context.user_data["loan"]["celular"] = celular
    context.user_data["loan"]["cliente"] = cliente
    await update.message.reply_text("🔐 Ingresa tu PIN de 4 dígitos.")
    return LOAN_PIN


async def loan_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()
    cliente = context.user_data["loan"]["cliente"]

    if str(cliente.get("PIN", "")).strip() != pin:
        await update.message.reply_text("❌ PIN incorrecto. Intenta de nuevo.")
        return LOAN_PIN

    cupo = str(cliente.get("Cupo", "")).strip()
    plazo = str(cliente.get("Plazo", "")).strip()

    if not cupo or cupo == "0" or cupo == "":
        await update.message.reply_text(
            "😔 Por el momento no tienes cupo disponible en Nero.\n"
            "Sigue construyendo tu puntaje y pronto tendrás nuevas oportunidades. 🖤",
            reply_markup=volver_keyboard(),
        )
        return ConversationHandler.END

    context.user_data["loan"]["cupo"] = cupo
    context.user_data["loan"]["plazo"] = plazo
    await update.message.reply_text(
        f"🎉 ¡Tienes cupo disponible de *${cupo}* a *{plazo} días*!\n\n¿Cómo prefieres pagar?",
        reply_markup=periodicidad_keyboard(),
        parse_mode="Markdown",
    )
    return LOAN_PERIODICIDAD


async def loan_periodicidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    periodicidad = "Quincenal" if query.data == "period_quincenal" else "Mensual"
    context.user_data["loan"]["periodicidad"] = periodicidad

    cupo = float(context.user_data["loan"]["cupo"].replace(".", "").replace(",", ""))
    plazo = context.user_data["loan"]["plazo"]

    if periodicidad == "Quincenal":
        cuotas = 2
        valor_cuota = cupo / 2
        desc = f"2 cuotas quincenales de *${valor_cuota:,.0f}*"
    else:
        cuotas = int(int(plazo) / 30)
        valor_cuota = cupo / cuotas
        desc = f"{cuotas} cuota(s) mensual(es) de *${valor_cuota:,.0f}*"

    context.user_data["loan"]["monto"] = cupo
    context.user_data["loan"]["desc_cuotas"] = desc

    await query.edit_message_text(
        f"📋 *Resumen de tu solicitud:*\n\n"
        f"💰 Monto: *${cupo:,.0f}*\n"
        f"📅 Plazo: *{plazo} días*\n"
        f"🗓️ Modalidad: *{periodicidad}*\n"
        f"💵 {desc}\n\n"
        f"¿Confirmas tu solicitud?",
        reply_markup=confirmar_keyboard(),
        parse_mode="Markdown",
    )
    return LOAN_CONFIRMAR


async def loan_confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "loan_no":
        await query.edit_message_text("❌ Solicitud cancelada.", reply_markup=volver_keyboard())
        return ConversationHandler.END

    loan = context.user_data["loan"]
    ok = registrar_prestamo({
        "celular": loan["celular"],
        "cupo": loan["cupo"],
        "plazo": loan["plazo"],
        "monto": loan["monto"],
        "periodicidad": loan["periodicidad"],
    })

    if ok:
        await query.edit_message_text(
            "✅ *¡Solicitud registrada con éxito!*\n\n"
            "Nuestro equipo procesará tu desembolso pronto.\n"
            "Cualquier duda, comunícate con un asesor. 🖤",
            reply_markup=volver_keyboard(),
            parse_mode="Markdown",
        )
    else:
        await query.edit_message_text(
            "⚠️ Hubo un error registrando tu solicitud. Contacta a un asesor.",
            reply_markup=volver_keyboard(),
        )
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  INVERTIR
# ─────────────────────────────────────────────
async def invertir_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["flujo"] = "inversor"
    await query.edit_message_text(
        "📈 *Quiero invertir con Nero*\n\n¿Ya tienes cuenta en Nero?",
        reply_markup=registro_login_keyboard("inv"),
        parse_mode="Markdown",
    )


async def inv_registrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["registro_inv"] = {}
    await query.edit_message_text("🆕 *Registro de inversor*\n\n¿Cuál es tu número de celular?", parse_mode="Markdown")
    return INV_REG_CELULAR


async def inv_reg_celular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registro_inv"]["celular"] = update.message.text.strip()
    await update.message.reply_text("🏠 ¿Cuál es tu dirección de residencia completa?")
    return INV_REG_DIRECCION


async def inv_reg_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["registro_inv"]["direccion"] = update.message.text.strip()
    await update.message.reply_text(
        "🔐 Crea tu PIN de seguridad.\n"
        "Escribe 4 dígitos que recuerdes fácilmente.\n\n"
        "⚠️ No compartas tu PIN con nadie, ni con asesores de Nero."
    )
    return INV_REG_PIN


async def inv_reg_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()
    if not pin.isdigit() or len(pin) != 4:
        await update.message.reply_text("❌ El PIN debe ser exactamente 4 dígitos. Intenta de nuevo.")
        return INV_REG_PIN
    context.user_data["registro_inv"]["pin"] = pin
    ok = registrar_inversor(context.user_data["registro_inv"])
    if ok:
        await update.message.reply_text(
            "✅ ¡Registro exitoso! Un asesor de Nero se pondrá en contacto contigo pronto para darte todos los detalles. 🖤",
            reply_markup=volver_keyboard(),
        )
    else:
        await update.message.reply_text("⚠️ Error guardando datos. Contacta a un asesor.", reply_markup=volver_keyboard())
    return ConversationHandler.END


async def inv_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔐 *Iniciar sesión — Inversor*\n\n¿Cuál es tu celular registrado?", parse_mode="Markdown")
    return INV_LOGIN_CELULAR


async def inv_login_celular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    celular = update.message.text.strip()
    try:
        ws = get_sheet(HOJA_INVERSORES)
        registros = ws.get_all_records()
        for row in registros:
            if str(row.get("Celular", "")).strip() == celular:
                context.user_data["inv_login"] = {"celular": celular, "pin_correcto": str(row.get("PIN", ""))}
                await update.message.reply_text("🔐 Ingresa tu PIN de 4 dígitos.")
                return INV_LOGIN_PIN
    except Exception as e:
        logger.error(e)
    await update.message.reply_text("❌ No encontramos una cuenta con ese número.", reply_markup=volver_keyboard())
    return ConversationHandler.END


async def inv_login_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pin = update.message.text.strip()
    if pin != context.user_data["inv_login"]["pin_correcto"]:
        await update.message.reply_text("❌ PIN incorrecto. Intenta de nuevo.")
        return INV_LOGIN_PIN
    await update.message.reply_text(
        "✅ *Sesión iniciada correctamente.*\n\n"
        "Un asesor de Nero te contactará pronto con la información de tu portafolio. 🖤",
        reply_markup=volver_keyboard(),
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  HABLAR CON ASESOR
# ─────────────────────────────────────────────
async def asesor_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["asesor"] = {}
    await query.edit_message_text("🎧 Con gusto te conectamos.\n\n¿Cuál es tu nombre completo?")
    return ASESOR_NOMBRE


async def asesor_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["asesor"]["nombre"] = update.message.text.strip()
    await update.message.reply_text("📱 ¿Cuál es tu número de celular?")
    return ASESOR_CELULAR


async def asesor_celular(update: Update, context: ContextTypes.DEFAULT_TYPE):
    celular = update.message.text.strip()
    nombre = context.user_data["asesor"]["nombre"]
    context.user_data["asesor"]["celular"] = celular

    registrar_asesor_contacto({"nombre": nombre, "celular": celular})

    try:
        await context.bot.send_message(
            chat_id=ASESOR_CHAT_ID,
            text=(
                f"🎧 *Nuevo contacto solicita asesor*\n\n"
                f"👤 Nombre: {nombre}\n"
                f"📱 Celular: {celular}\n"
                f"🔗 Usuario Telegram: @{update.message.from_user.username or 'sin usuario'}\n"
                f"🆔 ID Telegram: `{update.message.from_user.id}`"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning(f"No se pudo notificar al asesor: {e}")

    await update.message.reply_text(
        "✅ ¡Listo! Un asesor de Nero te contactará muy pronto. 🖤",
        reply_markup=volver_keyboard(),
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────
#  MENSAJES DE TEXTO SUELTOS
# ─────────────────────────────────────────────
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hola, soy Nero.\n"
        "⚠️ Nuestro único canal oficial de comunicación es Telegram. "
        "No operamos por WhatsApp ni ningún otro medio.\n\n"
        "¿Cómo puedo ayudarte?",
        reply_markup=menu_keyboard(),
    )


# ─────────────────────────────────────────────
#  BOTÓN MENÚ DESDE CALLBACK
# ─────────────────────────────────────────────
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(
        "👋 Hola, soy Nero.\n"
        "⚠️ Nuestro único canal oficial de comunicación es Telegram. "
        "No operamos por WhatsApp ni ningún otro medio.\n\n"
        "¿Cómo puedo ayudarte?",
        reply_markup=menu_keyboard(),
    )


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(TOKEN).build()

    # Conversación: registro cliente
    reg_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cli_registrar, pattern="^cli_registrar$")],
        states={
            REG_CELULAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_celular)],
            REG_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_direccion)],
            REG_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_pin)],
            REG_AVISO_SOPORTES: [CallbackQueryHandler(reg_aviso_continuar, pattern="^reg_continuar$")],
            REG_EXTRACTO1: [MessageHandler(filters.PHOTO | filters.Document.ALL, reg_extracto1)],
            REG_EXTRACTO2: [MessageHandler(filters.PHOTO | filters.Document.ALL, reg_extracto2)],
            REG_CEDULA: [MessageHandler(filters.PHOTO | filters.Document.ALL, reg_cedula)],
            REG_RECIBO: [MessageHandler(filters.PHOTO | filters.Document.ALL, reg_recibo)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(menu_callback, pattern="^menu$")],
    )

    # Conversación: login + préstamo
    loan_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(cli_login, pattern="^cli_login$")],
        states={
            LOAN_CELULAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_celular)],
            LOAN_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, loan_pin)],
            LOAN_PERIODICIDAD: [CallbackQueryHandler(loan_periodicidad, pattern="^period_")],
            LOAN_CONFIRMAR: [CallbackQueryHandler(loan_confirmar, pattern="^loan_")],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(menu_callback, pattern="^menu$")],
    )

    # Conversación: registro inversor
    inv_reg_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(inv_registrar, pattern="^inv_registrar$")],
        states={
            INV_REG_CELULAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, inv_reg_celular)],
            INV_REG_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, inv_reg_direccion)],
            INV_REG_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, inv_reg_pin)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(menu_callback, pattern="^menu$")],
    )

    # Conversación: login inversor
    inv_login_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(inv_login, pattern="^inv_login$")],
        states={
            INV_LOGIN_CELULAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, inv_login_celular)],
            INV_LOGIN_PIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, inv_login_pin)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(menu_callback, pattern="^menu$")],
    )

    # Conversación: asesor
    asesor_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(asesor_inicio, pattern="^asesor$")],
        states={
            ASESOR_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, asesor_nombre)],
            ASESOR_CELULAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, asesor_celular)],
        },
        fallbacks=[CommandHandler("start", start), CallbackQueryHandler(menu_callback, pattern="^menu$")],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(reg_conv)
    app.add_handler(loan_conv)
    app.add_handler(inv_reg_conv)
    app.add_handler(inv_login_conv)
    app.add_handler(asesor_conv)
    app.add_handler(CallbackQueryHandler(que_es, pattern="^que_es$"))
    app.add_handler(CallbackQueryHandler(prestamo_menu, pattern="^prestamo$"))
    app.add_handler(CallbackQueryHandler(invertir_menu, pattern="^invertir$"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    logger.info("Bot Nero iniciado ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
