import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

DEBUG = False

APP_ID_PROD = "DaniilVa-SearchPa-PRD-ddeb947bc-786c222d"
APP_ID_SANDBOX = "DaniilVa-SearchPa-SBX-8d2870b66-4dbe940f"

URL_PROD = "https://svcs.ebay.com/services/search/FindingService/v1"
URL_SANDBOX = "https://svcs.sandbox.ebay.com/services/search/FindingService/v1"

params = {
    "OPERATION-NAME": "findItemsAdvanced",
    "SERVICE-VERSION": "1.0.0",
    "SECURITY-APPNAME": APP_ID_SANDBOX if DEBUG else APP_ID_PROD,
    "RESPONSE-DATA-FORMAT": "JSON",
    "REST-PAYLOAD": "",
    "keywords": "Focusrite 3rd gen",
    "sortOrder": "StartTimeNewest",
    "paginationInput.entriesPerPage": "10",
}

TELEGRAM_BOT_TOKEN = "7243111884:AAFEBPyXYdEpVnNPMoipxiXz2wOfl3nyvOY"
TELEGRAM_CHAT_ID = 1382740469

# Функция для загрузки обработанных идентификаторов из файла
def load_processed_ids(filename):
    if os.path.exists(filename):
        with open(filename, encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Предполагаем, что в файле хранится список идентификаторов
                return set(data)
            except json.JSONDecodeError:
                return set()
    else:
        return set()

# Функция для сохранения обработанных идентификаторов в файл
def save_processed_ids(filename, processed_ids):
    with open(filename, 'w', encoding='utf-8') as f:
        # Преобразуем множество в список для записи в JSON
        json.dump(list(processed_ids), f, ensure_ascii=False, indent=4)


# --- Функция отправки сообщений в Telegram ---
def send_message_to_telegram(message):
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"  # Используется HTML-разметка, можно убрать этот параметр
    }
    try:
        response = requests.post(telegram_url, data=data)
        if response.status_code != 200:
            print("Ошибка при отправке сообщения в Telegram:", response.text)
    except Exception as e:
        print("Ошибка при подключении к Telegram API:", e)


def main():
    db_filename = "processed_items.json"
    processed_ids = load_processed_ids(db_filename)

    response = requests.get(URL_SANDBOX if DEBUG else URL_PROD, params=params)

    if response.status_code == 200:
        data = response.json()

        response_info = data.get("findItemsAdvancedResponse", [{}])[0]
        if response_info.get("ack", [""])[0] == "Success":
            search_result = response_info.get("searchResult", [{}])[0]
            items = search_result.get("item", [])

            for item in items:
                item_id = item.get("itemId", [""])[0]
                if item_id not in processed_ids:
                    item_title = item.get("title", [""])[0]
                    item_view_url = item.get("viewItemURL", [""])[0]
                    item_cost_amount = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", "")
                    item_cost_currency = item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("@currencyId", "")

                    # print(f"id: {item_id}\ntitle: {item_title}\nurl: {item_view_url}\ncost: {item_cost_amount} {item_cost_currency}\n")

                    message = (
                        f"<b>Новое объявление найдено!</b>\n"
                        f"ID: {item_id}\n"
                        f"Название: {item_title}\n"
                        f"Ссылка: {item_view_url}\n"
                        f"Стоимость: {item_cost_amount} {item_cost_currency}"
                    )

                    send_message_to_telegram(message)

                    processed_ids.add(item_id)
        else:
            print("Ошибка ответа API:", response_info.get("errorMessage", "Нет подробной информации"))
    else:
        print("Ошибка запроса:", response.status_code)

    save_processed_ids(db_filename, processed_ids)

if __name__ == "__main__":
    main()
