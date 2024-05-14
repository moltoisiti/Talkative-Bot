import requests
import logging

from config import (
    MAX_GPT_TOKENS,
    IAM_TOKEN,
    FOLDER_ID,
    REQUEST_TIMEOUT_SECONDS,
    headers,
    URL_TOKENIZE,
    LOGS,
    SYSTEM_PROMPT
)

logging.basicConfig(filename=LOGS, level=logging.ERROR, format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s", filemode="wb")

def speech_to_text(data):


    # Указываем параметры запроса
    params = "&".join([
        "topic=general",  # используем основную версию модели
        f"folderId={FOLDER_ID}",
        "lang=ru-RU"  # распознаём голосовое сообщение на русском языке
    ])


    # Выполняем запрос
    response = requests.post(
        f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers,
        data=data
    )

    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио #!
    else:
        return False, "При запросе в SpeechKit возникла ошибка"


def text_to_speech(text: str):

    data = {
        'text': text,  # текст, который нужно преобразовать в голосовое сообщение
        'lang': 'ru-RU',  # язык текста - русский
        'voice': 'filipp',  # голос Филиппа
        'folderId': FOLDER_ID,
    }
    # Выполняем запрос
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)

    if response.status_code == 200:
        return True, response.content  # Возвращаем голосовое сообщение
    else:
        return False, "При запросе в SpeechKit возникла ошибка"


def count_tokens(text):
    """
    Функция подсчета количества токенов в тексте
    """

    headers = {  # заголовок запроса, в котором передаем IAM-токен
        "Authorization": f"Bearer {IAM_TOKEN}",  # token - наш IAM-токен
        "Content-Type": "application/json",
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt/latest",  # указываем folder_id
        "maxTokens": MAX_GPT_TOKENS,
        "text": text,  # text - тот текст, в котором мы хотим посчитать токены
    }
    try:
        return len(
            requests.post(
                url=URL_TOKENIZE,
                json=data,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            ).json()["tokens"]
        )  # здесь, после выполнения запроса, функция возвращает количество токенов в text
    except Exception:
        return MAX_GPT_TOKENS




# настраиваем запись логов в файл


# подсчитываем количество токенов в сообщениях
def count_gpt_tokens(messages):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "messages": messages
    }
    try:
        return len(requests.post(url=url, json=data, headers=headers).json()['tokens'])
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return 0

# запрос к GPT
def ask_gpt(messages):
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        'modelUri': f"gpt://{FOLDER_ID}/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": MAX_GPT_TOKENS
        },
        "messages": SYSTEM_PROMPT + messages  # добавляем к системному сообщению предыдущие сообщения
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        # проверяем статус код
        if response.status_code != 200:
            return False, f"Ошибка GPT. Статус-код: {response.status_code}", None
        # если всё успешно - считаем количество токенов, потраченных на ответ, возвращаем статус, ответ, и количество токенов в ответе
        answer = response.json()['result']['alternatives'][0]['message']['text']
        tokens_in_answer = count_gpt_tokens([{'role': 'assistant', 'text': answer}])
        return True, answer, tokens_in_answer
    except Exception as e:
        logging.error(e)  # если ошибка - записываем её в логи
        return False, "Ошибка при обращении к GPT",  None