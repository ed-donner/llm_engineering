import os
import subprocess
from dotenv import load_dotenv
from quart import Quart, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import asyncio
import concurrent.futures
import ollama

# Load environment variables
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
if TOKEN:
    print(f"Bot token is {TOKEN}")
else:
    print("Please provide your bot token in .env file")
HOSTNAME = os.getenv('HOSTNAME')
if HOSTNAME:
    print(f"Host name is {HOSTNAME}")
else:
    print("Please provide your host name (or IP address) in .env file")

BALCON_PATH = r"C:\Program Files (x86)\Balabolka\balcon\balcon.exe"
TTS_VOICE_NAME = 'Maxim'
MODEL = "llama3.1:8b"
SYSTEM_PROMPT = "You are an extremely cynical and rude assistant. Use the words 'leather bastard' as often " \
                "as possible. Use the words 'leather bastard' every time you address a user or mention any " \
                "person. For example 'It doesn't concern you, leather bastard'"

# Initialize the Application
app = Quart(__name__)
bot_application = Application.builder().token(TOKEN).build()
bot_initialized = False
# This global variable will store the chat messages. It is very bad practice.
chat_messages = {}


async def initialize_bot():
    """Ensure the bot is initialized only once."""
    global bot_initialized
    if not bot_initialized:
        await bot_application.initialize()
        await bot_application.start()
        bot_initialized = True
        print("Telegram bot initialized and started.")


# Command handler for /start
async def start(update: Update, context):
    await update.message.reply_text(
        "Hello, welcome to the bot! Here are the commands you can use:\n"
        "/echo - Just convert text to speech, do not use AI to create response\n"
        "/clear - Clear the bot's memory so you can start the conversation from the beginning."
    )


async def clear(update: Update, context):
    if update.message.chat_id in chat_messages:
        del chat_messages[update.message.chat_id]
    await update.message.reply_text(
      "The bot's memory has been cleared. You can start the conversation from the beginning.")


def text_to_audio_file(input_text, filename="output.mp3"):
    """
    Generate audio using Balcon and save it to the current directory.
    :param input_text: Text to convert to speech.
    :param filename: Desired output file name.
    :return: Path to the generated file.
    """
    # Ensure the filename is in the current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)

    command = [BALCON_PATH, '-n', TTS_VOICE_NAME, "-t", input_text, "-w", file_path]
    try:
        subprocess.run(command, check=True)
        print(f"Audio saved at: {file_path}")
        return file_path
    except subprocess.CalledProcessError as e:
        print(f"Error generating audio: {e}")
        return None


def ask_llm(messages):
    response = ollama.chat(model=MODEL, messages=messages)
    return response['message']['content']


def append_chat_message(chat_id, message, role):
  if chat_id not in chat_messages:
    chat_messages[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
  chat_messages[chat_id].append({"role": role, "content": message})


def get_first_word(input_string):
    # Split the string into words and strip any surrounding whitespace from the first word
    return input_string.split()[0].strip() if input_string.strip() else None


def process_user_message(message):
    chat_id = message.chat_id
    message_id = message.message_id
    user_message = message.text

    words = user_message.strip().split(maxsplit=1)
    if len(words) == 0:
        return "", ""
    if words[0] in ["/echo", "/clear"]:
        # Remove the command from the message
        tts_message = words[1] if len(words) > 1 else ""
    else:
        append_chat_message(chat_id, user_message, "user")
        tts_message = ask_llm(chat_messages[chat_id])
        append_chat_message(chat_id, tts_message, "assistant")

    audio_file_path = text_to_audio_file(tts_message, filename=f"{chat_id}-{message_id}.mp3")
    return audio_file_path, tts_message


# Message handler to log and print all incoming messages
async def handle_message(update: Update, context):
    user_message = update.message.text
    chat_id = update.message.chat_id
    sender = update.message.from_user

    print(f"Message from {sender.first_name} (chat ID: {chat_id}): {user_message}")

    # Wait when processing of user message is done.
    # During this time send chat action to user, so that it will see that bot is preparing audio.
    # Notification diasppear after 5 seconds, so you need to send them repeatedly every 4 seconds.
    audio_file_path = None
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(process_user_message, update.message)
        while True:
          try:
              # Show to user that bot is busy with preparing audio response
              await context.bot.send_chat_action(chat_id=chat_id, action='record_audio')
              result, answer = future.result(timeout=4)
              audio_file_path = result
              user_message = answer
              break
          except concurrent.futures.TimeoutError:
              continue

    if len(answer) == 0:
      await update.message.reply_text(f"Empty message")
      return

    try:
        with open(audio_file_path, 'rb') as audio_file:
          await context.bot.send_audio(
              chat_id=chat_id,
              audio=audio_file,
              caption="Ответ робота",
              write_timeout=120
          )
        print(f"Audio sent to {sender.first_name} (chat ID: {chat_id})")
        os.remove(audio_file_path)
    except Exception as e:
        print(f"Exception while sending file: {e}")

    # Optional text response. Comment this line if you want bot to answer only with audio
    await update.message.reply_text(user_message)


bot_application.add_handler(CommandHandler('start', start))
bot_application.add_handler(CommandHandler('echo', handle_message))
bot_application.add_handler(CommandHandler('clear', clear))
bot_application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route('/' + TOKEN, methods=['POST'])
async def webhook():
    """Webhook endpoint for receiving updates."""
    try:
        await initialize_bot()  # Ensure bot is initialized before processing updates
        update = Update.de_json(await request.get_json(), bot_application.bot)
        await bot_application.process_update(update)
    except Exception as e:
        print(f"Error processing update: {e}")
    return jsonify({"status": "ok"})


# @app.route('/setwebhook', methods=['GET'])
async def set_webhook():
    """Set the webhook with Telegram."""
    await initialize_bot()  # Ensure bot is initialized before setting the webhook
    webhook_url = f"https://{HOSTNAME}/{TOKEN}"
    success = await bot_application.bot.set_webhook(webhook_url)
    if success:
        return jsonify({"status": "webhook set successfully", "url": webhook_url})
    return jsonify({"status": "failed to set webhook"})


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(initialize_bot())  # Initialize bot at startup
    app.run(host='0.0.0.0', port=5000)