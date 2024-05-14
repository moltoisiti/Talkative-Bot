from telebot import *
from yandex_gpt import speech_to_text, text_to_speech, count_tokens, ask_gpt
from config import BOT_TOKEN, LOGS, COUNT_LAST_MSG
from database import create_database, add_message, select_n_last_messages, insert_row
from validators import *
#from speechkit import speech_to_text

bot = TeleBot(token=BOT_TOKEN)

create_database()

@bot.message_handler(commands=["start"])
def start_command(message):
    user_name = message.from_user.first_name
    bot.send_message(message.from_user.id, text=f"Приветствую тебя, {user_name}!")



@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.from_user.id,
        text="Я твой цифровой собеседник 👾 Узнать обо мне подробнее можно командой /about",
    )


@bot.message_handler(commands=["about"])
def about_command(message):
    bot.send_message(
        message.from_user.id,
        text="Рад, что ты заинтересован_а! Мое предназначение — не оставлять тебя в одиночестве и всячески подбадривать! 🤍🤍"
        " \nС помощью GPT отвечу на Ваш вопрос в удобном формате (текстом или голосом). "
             "Нажмите кнопку /create, чтобы начать."
        " Пожалуйста, не вводите очень длинные сообщения, стоит ограничение на ввод 🖤",
    )


@bot.message_handler(commands=['stt'])
def stt_handler(message):
    create_database()
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt)

def stt(message):
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

    # Получаем статус и содержимое ответа от SpeechKit
    status, text = speech_to_text(file)  # преобразовываем голосовое сообщение в текст

    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        # Записываем сообщение и кол-во аудиоблоков в БД
        insert_row(user_id, text, 'stt_blocks', stt_blocks)
        bot.send_message(user_id, text, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, text)


@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id

        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

    # Проверка на доступность аудиоблоков
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message)
            return

    # Обработка голосового сообщения
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return

    # Запись в БД
        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])

    # Проверка на доступность GPT-токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

    # Запрос к GPT и обработка ответа
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

    # Проверка на лимит символов для SpeechKit
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

    # Запись ответа GPT в БД
        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])

        if error_message:
            bot.send_message(user_id, error_message)
            return

    # Преобразование ответа в аудио и отправка
        status_tts, voice_response = text_to_speech(answer_gpt)
        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)

    except Exception as e:
        logging.error(e)
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение")

@bot.message_handler(commands=["tts"])
def create_audio(message):
    bot.send_message(
        message.from_user.id,
        text="Пожалуйста, введите текст, который хотите перевести в аудио формат. Обратите внимание, что "
             "стоит ограничение на ввод, не отправляйте слишком длинный текст.",
    )
    if message.content_type != "text":
        bot.send_message(message.from_user.id, text="Не удалось получить корректные данные. "
                                       "Отправь промт текстовым сообщением")
        # регистрируем следующий "шаг" на эту же функцию
        bot.register_next_step_handler(message, create_audio)
        return
    bot.register_next_step_handler(message, get_prompt)


def get_prompt(message):
    # получаем сообщение, которое и будет промтом
    user_prompt = message.text
    print(user_prompt)
    count_tokens(user_prompt)

    status, reply = text_to_speech(user_prompt)
    if status:
        bot.send_voice(message.from_user.id, reply)
    else:
        bot.send_message(message.from_user.id, reply)

@bot.message_handler(commands=['debug'])
def debug(message):
    with open("logs.txt", "rb") as f:
        bot.send_document(message.chat.id, f)


@bot.message_handler(func=lambda: True)
def handler(message):
    bot.send_message(message.from_user.id, "Отправь мне голосовое или текстовое сообщение, и я тебе отвечу")



@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id

        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message)
            return

        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)

        last_messages, total_spent_tokens = select_n_last_messages(user_id, COUNT_LAST_MSG)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message)
            return

        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение")


bot.polling()