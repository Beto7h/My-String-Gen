import pyromod
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import Config

bot = Client(
    "GeneratorBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    text = "👋 **Hola! Soy un Generador de String Session Seguro.**\n\nElige qué tipo de sesión quieres generar:"
    buttons = [
        [InlineKeyboardButton("Pyrogram V2", callback_data="pyro")],
        [InlineKeyboardButton("Telethon", callback_data="tele")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("pyro|tele"))
async def generate_session(client, callback_query):
    method = callback_query.data
    chat_id = callback_query.message.chat.id
    
    # Pedir datos al usuario
    phone_ask = await client.ask(chat_id, "📱 Envía tu número con código de país (Ej: +521234567890):")
    phone_number = phone_ask.text

    await callback_query.message.reply("⏳ Conectando con Telegram...")

    # Crear cliente temporal
    if method == "pyro":
        temp_client = Client(":memory:", api_id=Config.API_ID, api_hash=Config.API_HASH)
    else:
        temp_client = TelegramClient(StringSession(), Config.API_ID, Config.API_HASH)

    await temp_client.connect()

    try:
        if method == "pyro":
            code_data = await temp_client.send_code(phone_number)
        else:
            code_data = await temp_client.send_code_request(phone_number)
    except Exception as e:
        await client.send_message(chat_id, f"❌ **Error:** {e}")
        return

    otp_ask = await client.ask(chat_id, "📩 Envía el código OTP que te llegó (Ej: 1 2 3 4 5):")
    otp = otp_ask.text.replace(" ", "")

    try:
        if method == "pyro":
            await temp_client.sign_in(phone_number, code_data.phone_code_hash, otp)
            string_session = await temp_client.export_session_string()
        else:
            await temp_client.sign_in(phone_number, otp)
            string_session = temp_client.session.save()

        # Enviar sesión a Mensajes Guardados por seguridad
        await temp_client.send_message("me", f"✅ **Tu sesión de {'Pyrogram' if method == 'pyro' else 'Telethon'}**:\n\n`{string_session}`")
        await temp_client.disconnect()
        
        await client.send_message(chat_id, "✅ **Éxito!** La sesión ha sido enviada a tus **Mensajes Guardados** de Telegram.")
    except Exception as e:
        await client.send_message(chat_id, f"❌ **Error:** {e}")

bot.run()
