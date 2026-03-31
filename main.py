import pyromod
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient
from telethon.sessions import StringSession
from config import Config

# --- SERVIDOR WEB PARA KOYEB ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_web_server():
    server = HTTPServer(('0.0.0.0', 8000), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# --- CLIENTE PRINCIPAL DEL BOT ---
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
        [InlineKeyboardButton("Pyrogram V2 (Recomendado)", callback_data="pyro")],
        [InlineKeyboardButton("Telethon", callback_data="tele")]
    ]
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@bot.on_callback_query(filters.regex("pyro|tele"))
async def generate_session(client, callback_query):
    method = callback_query.data
    chat_id = callback_query.message.chat.id
    
    try:
        phone_ask = await client.ask(chat_id, "📱 Envía tu número con código de país (Ej: +521234567890):", timeout=300)
    except:
        return
        
    phone_number = phone_ask.text
    await callback_query.message.reply("⏳ Conectando con Telegram...")

    # --- CAMBIO IMPORTANTE AQUÍ ---
    if method == "pyro":
        # Usamos in_memory=True y un device_model moderno para evitar baneos y errores de constructor
        temp_client = Client(
            "temp_session",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            in_memory=True,
            device_model="PC 64bit",
            system_version="Windows 11"
        )
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

    try:
        otp_ask = await client.ask(chat_id, "📩 Envía el código OTP que te llegó (Ej: 1 2 3 4 5):", timeout=300)
    except:
        return
        
    otp = otp_ask.text.replace(" ", "")

    try:
        if method == "pyro":
            try:
                await temp_client.sign_in(phone_number, code_data.phone_code_hash, otp)
            except Exception as e:
                if "SESSION_PASSWORD_NEEDED" in str(e):
                    pwd_ask = await client.ask(chat_id, "🔐 Tu cuenta tiene **Verificación en Dos Pasos**. \n\nPor favor, envía tu contraseña de seguridad:", timeout=300)
                    await temp_client.check_password(pwd_ask.text)
                else:
                    raise e
            string_session = await temp_client.export_session_string()
        
        else:
            try:
                await temp_client.sign_in(phone_number, otp)
            except Exception as e:
                if "SessionPasswordNeededError" in str(e) or "SESSION_PASSWORD_NEEDED" in str(e):
                    pwd_ask = await client.ask(chat_id, "🔐 Tu cuenta tiene **Verificación en Dos Pasos**. \n\nPor favor, envía tu contraseña de seguridad:", timeout=300)
                    await temp_client.sign_in(password=pwd_ask.text)
                else:
                    raise e
            string_session = temp_client.session.save()

        # Enviar sesión a Mensajes Guardados
        await temp_client.send_message("me", f"✅ **Tu sesión de {'Pyrogram' if method == 'pyro' else 'Telethon'}**:\n\n`{string_session}`\n\n⚠️ __No compartas este código con nadie.__")
        await temp_client.disconnect()
        
        await client.send_message(chat_id, "✅ **¡Éxito!** La sesión ha sido enviada a tus **Mensajes Guardados** en Telegram.")

    except Exception as e:
        await client.send_message(chat_id, f"❌ **Error:** {e}")

bot.run()
