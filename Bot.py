import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler
import xml.etree.ElementTree as ET
from datetime import datetime

# Вставьте сюда ваш API ключ от CoinMarketCap
COINMARKETCAP_API_KEY = '8d2c415b-35e9-4189-8383-34792ca3f11f'

# Словарь для хранения предыдущих цен криптовалют и временных меток
previous_prices = {}


# Функция для получения курса доллара к рублю
def get_usd_to_rub() -> float:
    url = 'https://www.cbr.ru/scripts/XML_daily.asp'
    response = requests.get(url)
    if response.status_code == 200:
        tree = ET.ElementTree(ET.fromstring(response.content))
        root = tree.getroot()
        for currency in root.findall('Valute'):
            if currency.find('CharCode').text == 'USD':
                return float(currency.find('Value').text.replace(',', '.'))
    raise Exception('Не удалось получить курс доллара к рублю')


# Функция для получения цены криптовалюты
def get_crypto_price(crypto: str) -> str:
    url = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    parameters = {'symbol': crypto}
    headers = {'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY}
    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()
    if response.status_code == 200:
        price_usd = data['data'][crypto]['quote']['USD']['price']
        usd_to_rub = get_usd_to_rub()
        price_rub = price_usd * usd_to_rub
        return price_usd, price_rub
    else:
        raise Exception('Не удалось получить данные. Попробуйте позже.')


# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [
            InlineKeyboardButton("TON", callback_data='TON'),
            InlineKeyboardButton("USDT", callback_data='USDT')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите криптовалюту:', reply_markup=reply_markup)


# Обработчик для кнопок
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    crypto = query.data

    try:
        new_price_usd, new_price_rub = get_crypto_price(crypto)

        # Получение предыдущих цен и временной метки
        previous_data = previous_prices.get(crypto, (None, None, None))
        previous_price_usd = previous_data[0]
        previous_price_rub = previous_data[1]
        previous_timestamp = previous_data[2]

        # Сохранение новых цен и временной метки
        current_timestamp = datetime.now().strftime('%d.%m.%Y %H:%M')
        previous_prices[crypto] = (new_price_usd, new_price_rub, current_timestamp)

        # Формирование сообщения с предыдущими и новыми ценами
        price_message = ""

        if previous_price_usd is not None and previous_price_rub is not None and previous_timestamp is not None:
            price_message += f'Прошлая цена {crypto} на {previous_timestamp} : ${previous_price_usd:.2f} USD ({previous_price_rub:.2f} RUB)\n\n'

        price_message += f'НОВАЯ цена {crypto} на {current_timestamp} : ${new_price_usd:.2f} USD ({new_price_rub:.2f} RUB)'

        await query.message.reply_text(text=price_message, reply_markup=query.message.reply_markup)

    except Exception as e:
        await query.message.reply_text(text=str(e), reply_markup=query.message.reply_markup)


# Главная функция
def main() -> None:
    # Вставьте сюда ваш токен API от Telegram
    TELEGRAM_API_TOKEN = '7323908364:AAFuu1qVvbIMBMCWx6Do7474-hp_SYLTK5c'

    # Создание объекта Application и передача ему вашего токена API
    application = Application.builder().token(TELEGRAM_API_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))

    # Запуск бота
    application.run_polling()


if __name__ == '__main__':
    main()
