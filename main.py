import sqlite3
import telebot
from telebot import types
import spichkit
import gpt
global user_id
import database
from database import insert_row, count_all_symbol, count_all_blocks
import math
import logging
from creds import get_bot_token  # модуль для получения bot_token
from  config import srcogg, LOGS

#
bot = telebot.TeleBot(get_bot_token())  # создаём объект бота
token = get_bot_token()
#from config import TOKEN
#bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
    encoding='windows-1251'
)


connection = sqlite3.connect('speech_kit.db')
cursor = connection.cursor()
database.create_table()
logging.info("База данных создана")

MAX_USER_TTS_SYMBOLS = 2000
MAX_TTS_SYMBOLS = 2000
MAX_USER_STT_BLOCKS = 30
MAX_TOKENS = 2000


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup()
    markup.add(types.KeyboardButton('/stt'), types.KeyboardButton('/tts'))
    bot.send_message(message.from_user.id,
                     "Привет! Отправь мне голосовое сообщение или текст, и я тебе отвечу! Если хоче просто перевести голос в текст нажимай /stt или если текст в голос /tts", reply_markup=markup)


# Просто перевод текста в голос и обратно без обращения к Y-GPT---------------------------------------------------------
@bot.message_handler(commands=['stt'])
def stt_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt_no_gpt)

# Переводим голосовое сообщение в текст после команды stt
def stt_no_gpt(message):
    user_id = message.from_user.id

    # Проверка, что сообщение действительно голосовое
    if not message.voice:
        return

    # Считаем аудиоблоки и проверяем сумму потраченных аудиоблоков
    stt_blocks = is_stt_block_limit(message, message.voice.duration)
    if not stt_blocks:
        return

    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение



    src = srcogg #'C:/tmp/audio.ogg'
    with open(src, 'wb') as new_file:
        new_file.write(file)

    # Получаем статус и содержимое ответа от SpeechKit
    status, text = spichkit.speech_to_text(file)  # преобразовываем голосовое сообщение в текст

    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        bot.send_message(user_id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, text)

    # Укажи путь к аудиофайлу, который хочешь распознать
    audio_file_path = src

    # Открываем аудиофайл в бинарном режиме чтения
    with open(audio_file_path, "rb") as audio_file:
        audio_data = audio_file.read()

    # Вызываем функцию распознавания речи
    success, result = spichkit.speech_to_text(audio_data)

    # Проверяем успешность распознавания и выводим результат
    if success:
        print("Распознанный текст: ", result)
    else:
        print("Ошибка при распознавании речи: ", result)


@bot.message_handler(commands=['tts'])
def tts_handler_no_gpt(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщеним текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts_no_gpt)


def tts_no_gpt(message):
    user_id = message.from_user.id
    text = message.text

    # Проверка, что сообщение действительно текстовое
    if message.content_type != 'text':
        bot.send_message(user_id, 'Отправь текстовое сообщение')
        return

        # Считаем символы в тексте и проверяем сумму потраченных символов
    text_symbol = is_tts_symbol_limit(message, text)
    if text_symbol is None:
        return

    # Получаем статус и содержимое ответа от SpeechKit
    status, content = spichkit.text_to_speech(text)

    # Если статус True - отправляем голосовое сообщение, иначе - сообщение об ошибке
    if status:
        bot.send_voice(user_id, content)
    else:
        bot.send_message(user_id, content)


@bot.message_handler(commands=['debug'])
def debug(msg):
    bot.send_document(msg.chat.id, open(LOGS))


# тут уже обращение к Y-GPT---------------------------------------------------------------------------------------------
@bot.message_handler(content_types=['text'])
def text_handler(message):

    msg = message.text

    conn = sqlite3.connect('speech_kit.db')
    user_id = message.from_user.id
    cursor = conn.cursor()
    # Считаем, сколько аудиоблоков использовал пользователь
    cursor.execute('''SELECT SUM(tokens) FROM messages WHERE user_id=?''', (user_id,))
    data = cursor.fetchone()
    print(data[0])
    if data[0] == None:
        all_tokens = 0
    else:
        all_tokens = int(data[0])

    tokens = len(msg)
    if all_tokens > MAX_TOKENS:
        bot.send_message(message.from_user.id, "Превышен лимит токенов")
    else:

        vopros = gpt.ask_gpt(msg)
        logging.info("отправка ответа GPT")
        bot.send_message(message.from_user.id, vopros)
        insert_row(user_id, msg, vopros, '', '', tokens)


@bot.message_handler(content_types=['voice'])
def voice_handler(message):
    user_id = message.from_user.id

    stt_blocks = is_stt_block_limit(message, message.voice.duration)
    if not stt_blocks:
        return

    file_id = message.voice.file_id  # получаем id голосового сообщения
    file_info = bot.get_file(file_id)  # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path)  # скачиваем голосовое сообщение


    src = srcogg #'C:/tmp/audio.ogg'
    with open(src, 'wb') as new_file:
        new_file.write(file)

    status, text = spichkit.speech_to_text(file)
    logging.info("Голос пользователя переведен в текст")

    if status == True:
        msg = text
        vopros = gpt.ask_gpt(msg)
        insert_row(user_id, msg,'',stt_blocks,'', '')
        logging.info("Текст пользователя отправлен к GPT")


        # Считаем символы в тексте и проверяем сумму потраченных символов
        text_symbol = is_tts_symbol_limit(message, text)
        if text_symbol is None:
            return

        # Записываем сообщение и кол-во символов в БД


        status, golos_gpt = spichkit.text_to_speech(vopros)
        logging.info("Ответ GPT переведен из текстав голос")
        insert_row(user_id, msg, vopros, stt_blocks, text_symbol, '')
        if status == True:
            bot.send_voice(user_id, golos_gpt)
            logging.info("Ответ GPT отправлен в виде голосового сообщения")

        else:
            bot.send_message(user_id, "упс что-то пошло не так")

    else:
        bot.send_message(user_id, "упс что-то пошло не так")


def is_tts_symbol_limit(message, text):
    user_id = message.from_user.id
    text_symbols = len(text)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_symbol(user_id) + text_symbols
    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= MAX_USER_TTS_SYMBOLS:
        msg = f"Превышен общий лимит SpeechKit TTS {MAX_USER_TTS_SYMBOLS}. Использовано: {all_symbols} символов. Доступно: {MAX_USER_TTS_SYMBOLS - all_symbols}"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем количество символов в тексте с максимальным количеством символов в тексте
    if text_symbols >= MAX_TTS_SYMBOLS:
        msg = f"Превышен лимит SpeechKit TTS на запрос {MAX_TTS_SYMBOLS}, в сообщении {text_symbols} символов"
        bot.send_message(user_id, msg)
        return None
    return len(text)


def is_stt_block_limit(message, duration):
    user_id = message.from_user.id

    # Переводим секунды в аудиоблоки
    audio_blocks = math.ceil(duration / 15) # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = count_all_blocks(user_id) + audio_blocks

    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        msg = "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"
        bot.send_message(user_id, msg)
        return None

    # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks >= MAX_USER_STT_BLOCKS:
        msg = f"Превышен общий лимит SpeechKit STT {MAX_USER_STT_BLOCKS}. Использовано {all_blocks} блоков. Доступно: {MAX_USER_STT_BLOCKS - all_blocks}"
        bot.send_message(user_id, msg)
        return None

    return audio_blocks



bot.polling()
