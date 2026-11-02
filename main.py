import telebot
import yt_dlp
import subprocess
import os
from dotenv import load_dotenv

# Гирифтани маълумот аз .env
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')

if not API_TOKEN:
    raise ValueError("Хатогӣ: Дар файли .env BOT_TOKEN ёфт нашуд!")

bot = telebot.TeleBot(API_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Ассалому алайкум! Ссылкаи (пайванд) видеои YouTube-ро равон кунед.")
    user_data[message.chat.id] = {}

@bot.message_handler(func=lambda message: message.text and ('youtube.com' in message.text or 'youtu.be' in message.text))
def ask_start_time(message):
    user_data[message.chat.id] = {'url': message.text}
    msg = bot.reply_to(message, "Вақти оғозро ворид кунед (масалан: 03:24 ё 00:24):")
    bot.register_next_step_handler(msg, process_start_time)

def process_start_time(message):
    user_data[message.chat.id]['start'] = message.text
    msg = bot.reply_to(message, "Вақти анҷомро ворид кунед (масалан: 04:56):")
    bot.register_next_step_handler(msg, process_end_time)

def process_end_time(message):
    chat_id = message.chat.id
    user_data[chat_id]['end'] = message.text
    
    url = user_data[chat_id]['url']
    start_time = user_data[chat_id]['start']
    end_time = user_data[chat_id]['end']
    
    status_msg = bot.send_message(
        chat_id, 
        "🔄 <b>Қадами 1/3:</b> Зеркашии видео аз YouTube...\n\n<i>(Илтимос интизор шавед)</i>", 
        parse_mode='HTML'
    )
    
    input_vid = f"input_{chat_id}.mp4"
    output_vid = f"output_{chat_id}.mp4"
    
    try:
        # 1. Зеркашии видео ва садо бо пайвастшавии худкор ба MP4
        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4]/best', 
            'outtmpl': input_vid,
            'noplaylist': True,
            'socket_timeout': 60,
            'merge_output_format': 'mp4'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        bot.edit_message_text(
            "✂️ <b>Қадами 2/3:</b> Буридани қисмати интихобшуда ва табдил ба формати 9:16...\n\n<i>⏳ Ин амал тахминан 1 дақиқа вақт мегирад.</i>", 
            chat_id, 
            status_msg.message_id,
            parse_mode='HTML'
        )
        
        # 2. Буриши дақиқ бо вақтҳои ирсолшуда ва табдил ба формати 9:16
        vid_command = [
            'ffmpeg', '-y', 
            '-ss', start_time, 
            '-to', end_time, 
            '-i', input_vid, 
            '-vf', 'crop=ih*9/16:ih', 
            '-c:v', 'libx264', 
            '-c:a', 'aac', 
            output_vid
        ]
        subprocess.run(vid_command, check=True)
        
        bot.edit_message_text(
            "🚀 <b>Қадами 3/3:</b> Видео омода шуд! Ба Telegram бор карда истодаем...", 
            chat_id, 
            status_msg.message_id,
            parse_mode='HTML'
        )
        
        # 3. Фиристодани видео ба корбар
        with open(output_vid, 'rb') as video:
            bot.send_video(chat_id, video, timeout=300)
            
        bot.edit_message_text("✅ Видео муваффақиятнок фиристода шуд!", chat_id, status_msg.message_id)
            
    except subprocess.CalledProcessError as e:
        bot.send_message(chat_id, f"Хатогӣ ҳангоми буридани видео. Лутфан дурустии фосилаи вақтро санҷед.\nХато: {e}")
    except Exception as e:
        bot.send_message(chat_id, f"Хатогии ғайричашмдошт рух дод:\n{e}")
        
    finally:
        # 4. Тоза кардани файлҳои муваққатӣ аз хотира
        for file in [input_vid, output_vid]:
            if os.path.exists(file):
                os.remove(file)

if __name__ == '__main__':
    print("Бот ба кор даромад...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)