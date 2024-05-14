BOT_TOKEN = "6849265887:AAFpuK7ve4QRJn-YH9JWwg04XCzmskPAs6I"

IAM_TOKEN = "t1.9euelZqclIqOzZaNm4-MmpGPi8_Ozu3rnpWakpCTmYmMz86MncaRz5mUi8jl8_d_F1tP-e9VOhVo_N3z9z9GWE_571U6FWj8zef1656VmpGVzsuXkZWPyMiVx5GelozL7_zF656VmpGVzsuXkZWPyMiVx5GelozLveuelZrOj5SYy5mTmYyYlJacx5WSk7XehpzRnJCSj4qLmtGLmdKckJKPioua0pKai56bnoue0oye.eZyRSYocE8T1fppDUlKlu4uZbR8TntvfJ9lJ9xdSFCpMd5tUbG1zyprJPXe5sXGvViwIc4p7kEIcTPO70WP3AQ"


FOLDER_ID = "b1gu8kb83kb7j102ttn9"

REQUEST_TIMEOUT_SECONDS = 5

headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
    }

MAX_USER_STT_BLOCKS = 10

URL_TOKENIZE = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'

MAX_USERS = 3

MAX_GPT_TOKENS = 120

COUNT_LAST_MSG = 4

MAX_USER_TTS_SYMBOLS = 5000

MAX_USER_GPT_TOKENS = 2000

LOGS = 'logs.txt'  # файл для логов

DB_FILE = 'messages.db'  # файл для базы данных

SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
                                            'Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Изображай человека'}]