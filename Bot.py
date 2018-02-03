import re
from datetime import date
from random import randint
from time import sleep

import requests

TELEGRAM_BOT_ID = 'Insert here your telegram bot ID'

LUIS_APP_KEY = 'Insert here your LUIS application key'
LUIS_SUBSCRIPTION_KEY = 'Insert here subscription key for your application'

YANDEX_WEATHER_API_KEY = 'Insert here your Yandex Weather API key'
YANDEX_TRANSLATE_API_KEY = 'Insert here your Yandex Translate API key'

GOOGLE_GEO_ENCODING_API_KEY = 'Insert here your Google Geolocation API key'

BING_API_KEY = 'Insert here your Bing API key'


class TelegramBotInterface(object):
    """
    Class providing interface of a Telegram bot.
    
    Defined methods:
    
    __init__(self, bot_id)
        Initialize bot with bot id.
        
    get_updates(self)
        Get updates from Telegram server.
        :return List of dict objects described in Telegram API help as Update.
        
    get_text_message(self, update)
        Get text message from update.
        :return String with text message.
        
    send_message(self, chat_id, text_message)
        Send text message to chat with given id.
        
    send_photo(self, chat_id, photo_url)
        Send photo taken by photo_url into a chat with given chat_id.
        
    get_chat_id(self, update)
        Get chat id from object Update.
        :return Integer representing chat id.
        
    """
    url = 'https://api.telegram.org/bot{bot_id}/'

    def __init__(self, bot_id):
        self.id = bot_id
        self.offset = 0

        self.url = self.url.format(bot_id=self.id)

    def get_updates(self):
        request_url = self.url + 'getUpdates'
        params = {
            'offset': self.offset
        }

        updates = requests.get(request_url, params)

        if updates.status_code != 200:
            updates.raise_for_status()

        try:
            self.offset = updates.json()['result'][-1]['update_id'] + 1
        except IndexError:
            pass

        return updates.json()['result']

    def get_text_message(self, update):
        return update['message']['text']

    def send_message(self, chat_id, text_message):
        request_url = self.url + 'sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text_message
        }

        return requests.post(request_url, data)

    def send_photo(self, chat_id, photo_url):
        request_url = self.url + 'sendPhoto'
        data = {
            'chat_id': chat_id,
            'photo': photo_url
        }

        return requests.post(request_url, data)

    def get_chat_id(self, update):
        return update['message']['chat']['id']


class MessageHandler(object):
    """
    Class containing methods for parsing and processing incoming messages.
    
    Defined methods:
    
    __init__(self, luis_app, luis_subscription, yandex_weather, yandex_translate, google_geo, bing)
        Initialize a new message handler. To gain full functionality all keys must be provided.
        
    __call__(self, text_message)
        Handle the message :)
        :return Object of class Response with filled fields.
        
    analyze_message(self, text_message)
        Analyze given message via LUIS system.
        :return Dict object with intention and entities.
        
    translate_text(self, text_message)
        Translate text from any language into English via Yandex Transalte.
        :return String containing translated message.
        
    get_weather(self, city, time)
        Make weather request to Yandex Weather.
        :return Dict object with weather data.
    
    get_picture(self, search_request)
        Make search request to Bing API.
        :return URL linking to random chosen picture from top eight of Bing response.
        
    get_poem(self, weather)
        Not implemented.
        
    """
    help_string = 'This multilanguage bot is to provide you information about current ' \
                  'weather or weather forecast in a region whatever you want. The bot ' \
                  'does not require any specific form of requests and it' \
                  'completely understands all messages including city and date/time. ' \
                  'If information about time have not been given, it will return you ' \
                  'current weather in a region. The Moscow is considered to be default city.' \
                  '\nDue to usage of Yandex Weather API it is possible to show weahter ' \
                  'forecasts only for ten days in advance.' \
                  '\n/help'

    greetings = [
        'Hi there!',
        'Hi!',
        'Hello)'
    ]

    partings = [
        'Bye(',
        'Good luck!',
        'Goodbye!',
        'Have a nice day!'
    ]

    if_none = [
        'I do not know what to say...',
        'Please specify your request.',
        'I do not really understand what you meant by that.'
    ]

    luis_api_url = 'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/{app_key}'

    yandex_translate_url = 'https://translate.yandex.net/api/v1.5/tr.json/translate'
    yandex_weather_url = 'https://api.weather.yandex.ru/v1/forecast'

    bing_api_url = 'https://api.cognitive.microsoft.com/bing/v7.0/images/search?%s'

    google_geo_encoding_url = 'https://maps.googleapis.com/maps/api/geocode/json'

    class LocationNotFound(Exception):
        pass

    class Response(object):
        def __init__(self, text, photo=None, poem=None):
            self.text = text
            self.photo = photo
            self.poem = poem

    def __init__(self, luis_app, luis_subscription, yandex_weather,
                 yandex_translate, google_geo, bing):
        self.luis_app_key = luis_app
        self.luis_subscription_key = luis_subscription
        self.yandex_weather_api_key = yandex_weather
        self.yandex_translate_api_key = yandex_translate
        self.google_geo_encoding_api_key = google_geo
        self.bing_api_key = bing

        self.luis_api_url = self.luis_api_url.format(app_key=self.luis_app_key)

    def analyze_message(self, text_message):
        params = {
            'subscription-key': self.luis_subscription_key,
            'q': text_message
        }

        response = requests.get(self.luis_api_url, params)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def translate_text(self, text_message):
        params = {
            'key': self.yandex_translate_api_key,
            'text': text_message,
            'lang': 'en'
        }

        response = requests.get(self.yandex_translate_url, params)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()['text'][0]

    def get_weather(self, city, time):

        params = {
            'address': city,
            'key': self.google_geo_encoding_api_key
        }
        response = requests.get(self.google_geo_encoding_url, params)

        if response.status_code != 200:
            response.raise_for_status()

        try:
            location = response.json()['results'][0]['geometry']['location']
        except IndexError:
            raise self.LocationNotFound

        headers = {
            'X-Yandex-API-Key': self.yandex_weather_api_key
        }

        params = {
            'lat': location['lat'],
            'lng': location['lng'],
            'limit': time,
            'l10n': 'true'
        }

        response = requests.get(params=params, headers=headers)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def get_picture(self, search_request):
        headers = {
            'Ocp-Apim-Subscription-Key': self.bing_api_key,
        }

        params = {
            'q': search_request,
            'count': '10',
            'offset': '0',
            'mkt': 'en-us',
            'safeSearch': 'Moderate',
        }

        response = requests.get(
            self.bing_api_url,
            params=params,
            headers=headers
        )

        if response.status_code != 200:
            response.raise_for_status()

        try:
            picture_url = response.json()['value'][randint(0, 7)]['thumbnailUrl']
        except IndexError or KeyError:
            try:
                picture_url = response.json()['value'][0]['thumbnailUrl']
            except IndexError or KeyError:
                picture_url = None

        return picture_url

    def get_poem(self, weather):
        raise NotImplementedError

    def __call__(self, text_message):
        if text_message.strip() == '/help':
            return self.Response(self.help_string)
        translated_message = self.translate_text(text_message)
        sense_of_message = self.analyze_message(translated_message)
        if sense_of_message['topScoringIntent']['intent'] == 'Greeting':
            return self.Response(self.greetings[randint(0, len(self.greetings) - 1)])
        elif sense_of_message['topScoringIntent']['intent'] == 'Parting':
            return self.Response(self.partings[randint(0, len(self.partings) - 1)])
        elif sense_of_message['topScoringIntent']['intent'] == 'Weather':
            city, time = None, None
            for entity in sense_of_message['entities']:
                if entity['type'] == 'City':
                    city = entity['entity']
                if entity['type'] == 'Time':
                    time = entity['entity']

            if city is None:
                return self.Response('Please specify the location.')
            in_city = ' in {}'.format(city.capitalize())

            days_to = {
                'monday': 1,
                'tuesday': 2,
                'wednesday': 3,
                'thursday': 4,
                'friday': 5,
                'saturday': 6,
                'sunday': 7
            }
            today_int = days_to[date.today().strftime('%A').lower()]
            days_to['tomorrow'] = today_int + 1
            days_to['day after tomorrow'] = today_int + 2
            days_to['after the day after tomorrow'] = today_int + 3

            if time is not None:
                if time in days_to:
                    forecast_date = time
                    time = str((days_to[time] + 7 - days_to[date.today().strftime('%A').lower()]) % 7 + 1)
                else:
                    time = ''
            else:
                time = ''

            try:
                weather_api_ans = self.get_weather(city, time)
            except self.LocationNotFound:
                return self.Response('Location not found.')

            if time is '':
                forecast_date = re.search('\d{4}-\d{2}-\d{2}', weather_api_ans['now_dt']).group()
                forecast_date = date(*list(map(int, forecast_date.split('-'))))
                forecast_date = forecast_date.strftime('%A %d %B')

            in_time = ' for {}'.format(forecast_date.capitalize())

            weather_description_template = 'The weather forecast{in_city}{in_time}:' \
                                           '\nDuring the day temperature is going to be about ' \
                                           '{temp} degrees, but ' \
                                           'it feels like {feels_like} degrees. ' \
                                           '{obs}.' \
                                           '\n{pressure_str}' \
                                           '\nHumidity - {humidity}%'

            pressure_str_if_eq = 'Pressure is the same as normal and equals {curr_pressure}'
            pressure_str_if_diff = 'Pressure is {pressure_comp} than normal ' \
                                   'for {pressure_diff} mmHg and makes up {curr_pressure}.'

            day_forecast = weather_api_ans['forecasts'][-1]['parts']['day_short']
            curr_pressure = day_forecast['pressure_mm']
            pressure_diff = curr_pressure - weather_api_ans['info']['def_pressure_mm']

            if pressure_diff < 0:
                pressure_str = pressure_str_if_diff.format(
                    pressure_comp='lower',
                    pressure_diff=abs(pressure_diff),
                    curr_pressure=curr_pressure
                )
            elif pressure_diff > 0:
                pressure_str = pressure_str_if_diff.format(
                    pressure_comp='upper',
                    pressure_diff=abs(pressure_diff),
                    curr_pressure=curr_pressure
                )
            else:
                pressure_str = pressure_str_if_eq.format(curr_pressure=curr_pressure)

            weather_description = weather_description_template.format(
                in_city=in_city,
                in_time=in_time,
                pressure_str=pressure_str,
                temp=day_forecast['temp'],
                feels_like=day_forecast['feels_like'],
                humidity=day_forecast['humidity'],
                obs=self.translate_text(
                    'Наблюдается ' + weather_api_ans['l10n'][day_forecast['condition']]
                )
            )

            try:
                picture = self.get_picture(
                    city + self.translate_text(weather_api_ans['l10n'][day_forecast['condition']])
                )
            except IndexError:
                picture = None

            return self.Response(weather_description, picture)
        elif sense_of_message['topScoringIntent']['intent'] == 'None':
            return self.Response(self.if_none[randint(0, len(self.if_none) - 1)])


if __name__ == '__main__':
    bot_interface = TelegramBotInterface(TELEGRAM_BOT_ID)

    handler = MessageHandler(
        LUIS_APP_KEY,
        LUIS_SUBSCRIPTION_KEY,
        YANDEX_WEATHER_API_KEY,
        YANDEX_TRANSLATE_API_KEY,
        GOOGLE_GEO_ENCODING_API_KEY,
        BING_API_KEY
    )

    while True:
        updates = bot_interface.get_updates()
        for update in updates:
            text_message = bot_interface.get_text_message(update)
            response_message = handler(text_message)
            bot_interface.send_message(chat_id=bot_interface.get_chat_id(update),
                                       text_message=response_message.text)
            if response_message.photo is not None:
                bot_interface.send_photo(chat_id=bot_interface.get_chat_id(update),
                                         photo_url=response_message.photo)
            if response_message.poem is not None:
                pass
        sleep(2)
