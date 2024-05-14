import requests
global text_gpt
from creds import get_creds  # модуль для получения токенов

iam_token, folder_id = get_creds()  # получаем iam_token и folder_id из файлов
#from config import  folder_id #, iam_token


def ask_gpt(text):

    headers = {
        'Authorization': f'Bearer {iam_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{folder_id}/yandexgpt-lite",  # модель для генерации текста
        "completionOptions": {
            "stream": False,  # потоковая передача частично сгенерированного текста выключена
            "temperature": 0.6,  # чем выше значение этого параметра, тем более креативными будут ответы модели (0-1)
            "maxTokens": 100  # максимальное число сгенерированных токенов, очень важный параметр для экономии токенов
        },
        "messages": [
            {
                "role": "user",  # пользователь спрашивает у модели
                "text": text  # передаём текст, на который модель будет отвечать
            }
        ]
    }

    # Выполняем запрос к YandexGPT
    response = requests.post("https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                             headers=headers,
                             json=data)
    print(response)
    print(text)
    #Проверяем, не произошла ли ошибка при запросе
    if response.status_code == 200:
        # достаём ответ YandexGPT
        text_gpt = response.json()["result"]["alternatives"][0]["message"]["text"]
        print(text_gpt)
        xxx = text_gpt
    else:
        raise RuntimeError(
            'Invalid response received: code: {}, message: {}'.format(
                {response.status_code}, {response.text}
            )
        )
    return xxx