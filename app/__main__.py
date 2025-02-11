import json
import logging
import os
import time

import requests

from app.settings import AppSettings, get_app_settings

logger = logging.getLogger(__name__)

__APP_SETTINGS: AppSettings = get_app_settings()

params_template = {
    "OPERATION-NAME": "findItemsAdvanced",
    "SERVICE-VERSION": "1.0.0",
    "SECURITY-APPNAME": __APP_SETTINGS.app_id_prod,
    "RESPONSE-DATA-FORMAT": "JSON",
    "REST-PAYLOAD": "",
    "keywords": "",
    "sortOrder": "StartTimeNewest",
    "paginationInput.entriesPerPage": "20",
}


# Инициализировать логгер
def setup_logging(logger):
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)


# Функция для загрузки обработанных идентификаторов из файла
def load_processed_ids(filename):
    if os.path.exists(filename):
        with open(filename, encoding="utf-8") as f:
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
    with open(filename, "w", encoding="utf-8") as f:
        # Преобразуем множество в список для записи в JSON
        json.dump(list(processed_ids), f, ensure_ascii=False, indent=4)


# --- Функция отправки сообщений в Telegram ---
def send_message_to_telegram(message: str, chat_id: int):
    telegram_url = (
        f"https://api.telegram.org/bot{__APP_SETTINGS.telegram_bot_token}/sendMessage"
    )
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",  # Используется HTML-разметка, можно убрать этот параметр
    }
    try:
        response = requests.post(telegram_url, data=data)
        if response.status_code != 200:
            logger.error("Ошибка при отправке сообщения в Telegram:", response.text)
    except Exception as e:
        logger.exception("Ошибка при подключении к Telegram API:", e)


def main():
    logger.info("Запуск проверки")

    db_filename = "processed_items.json"
    processed_ids = load_processed_ids(db_filename)

    for keyword_filter in __APP_SETTINGS.keywords_filters:
        logger.info(f"Проверка по ключу: {keyword_filter}")
        params = params_template.copy()
        params["keywords"] = keyword_filter
        response = requests.get(__APP_SETTINGS.url_prod, params=params)

        if response.status_code == 200:
            data = response.json()

            response_info = data.get("findItemsAdvancedResponse", [{}])[0]
            if response_info.get("ack", [""])[0] == "Success":
                search_result = response_info.get("searchResult", [{}])[0]
                items = search_result.get("item", [])

                for item in items:
                    item_id = item.get("itemId", [""])[0]
                    if item_id not in processed_ids:
                        logger.info(f"Новое объявление: {item_id}")
                        item_title = item.get("title", [""])[0]
                        item_view_url = item.get("viewItemURL", [""])[0]
                        item_cost_amount = (
                            item.get("sellingStatus", [{}])[0]
                            .get("currentPrice", [{}])[0]
                            .get("__value__", "")
                        )
                        item_cost_currency = (
                            item.get("sellingStatus", [{}])[0]
                            .get("currentPrice", [{}])[0]
                            .get("@currencyId", "")
                        )

                        message = (
                            f"<b>Новое объявление найдено!</b>\n"
                            f"ID: {item_id}\n"
                            f"Название: {item_title}\n"
                            f"Ссылка: {item_view_url}\n"
                            f"Стоимость: {item_cost_amount} {item_cost_currency}"
                        )

                        for tg_chat_id in __APP_SETTINGS.telegram_chat_ids:
                            send_message_to_telegram(
                                message=message, chat_id=tg_chat_id
                            )

                        processed_ids.add(item_id)
            else:
                logger.error(
                    "Ошибка ответа API:",
                    response_info.get("errorMessage", "Нет подробной информации"),
                )
        else:
            logger.error("Ошибка запроса:", response.status_code)

        save_processed_ids(db_filename, processed_ids)

        time.sleep(2)

    logger.info("Окончание проверки")


if __name__ == "__main__":
    setup_logging(logger)
    main()
