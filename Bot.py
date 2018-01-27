import re
from datetime import date
from random import randint
from time import sleep

import requests

TELEGRAM_BOT_ID = 'Insert here your bot ID'

LUIS_APP_KEY = ''
LUIS_SUBSCRIPTION_KEY = ''

YANDEX_WEATHER_API_KEY = ''
YANDEX_TRANSLATE_API_KEY = ''

OPEN_WEATHER_MAP_KEY = ''

GOOGLE_GEO_ENCODING_API_KEY = ''

BING_API_KEY = ''


class TelegramBotInterface(object):
    url = 'https://api.telegram.org/bot{bot_id}/{method}'

    def __init__(self, bot_id):
        self.id = bot_id
        self.offset = 0

    def get_updates(self):
        request_url = self.url.format(bot_id=TELEGRAM_BOT_ID, method='getUpdates')
        params = {'offset': self.offset}

        updates = requests.get(request_url, data=params)

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
        params = {
            'bot_id': TELEGRAM_BOT_ID,
            'method': 'sendMessage'
        }
        request_url = self.url.format(**params)

        data = {
            'chat_id': chat_id,
            'text': text_message
        }
        return requests.post(request_url, data)

    def send_photo(self, chat_id, photo_url):
        params = {
            'bot_id': TELEGRAM_BOT_ID,
            'method': 'sendPhoto'
        }
        request_url = self.url.format(**params)

        data = {
            'chat_id': chat_id,
            'photo': photo_url
        }
        return requests.post(request_url, data)

    def get_chat_id(self, update):
        return update['message']['chat']['id']


class MessageHandler(object):
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

    yandex_weather_url = 'https://api.weather.yandex.ru/v1/forecast?' \
                         'lat={lat}&lon={lng}&limit={limit}&l10n=true'

    luis_api_url = 'https://westus.api.cognitive.microsoft.com/luis/v2.0/apps/' \
                   '{app_key}?subscription-key={subscription_key}&q={query}'

    yandex_translate_url = 'https://translate.yandex.net/api/v1.5/' \
                           'tr.json/translate?' \
                           'key={key}' \
                           '&text={text}' \
                           '&lang={lang_to}'

    open_weather_map_url = 'http://api.openweathermap.org/data/2.5/weather?q={query}&APPID={api_key}'

    google_geo_encoding_url = 'https://maps.googleapis.com/maps/api/geocode/json?' \
                              'address={address}&key={api_key}'

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

    def parse_message(self, text_message):
        params = {
            'app_key': LUIS_APP_KEY,
            'subscription_key': LUIS_SUBSCRIPTION_KEY,
            'query': text_message
        }

        request_url = self.luis_api_url.format(**params)
        response = requests.get(request_url)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def translate_text(self, text_message):
        params = {
            'key': self.yandex_translate_api_key,
            'text': text_message,
            'lang_to': 'en'
        }

        request_url = self.yandex_translate_url.format(**params)
        response = requests.get(request_url)

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()['text'][0]

    def get_weather(self, city, time):

        params = {
            'address': city,
            'api_key': self.google_geo_encoding_api_key
        }
        response = requests.get(self.google_geo_encoding_url.format(**params))

        if response.status_code != 200:
            response.raise_for_status()

        try:
            location = response.json()['results'][0]['geometry']['location']
        except IndexError:
            raise self.LocationNotFound

        headers = {
            'X-Yandex-API-Key': self.yandex_weather_api_key
        }

        response = requests.get(self.yandex_weather_url.format(**location, limit=time), headers=headers)

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
            "https://api.cognitive.microsoft.com/bing/v7.0/images/search?%s",
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
        pass

    def __call__(self, text_message):
        if text_message.strip() == '/help':
            return self.Response(self.help_string)
        translated_message = self.translate_text(text_message)
        sense_of_message = self.parse_message(translated_message)
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
                                           '\nHumidity - {humidity}%' \

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
                obs=self.translate_text('Наблюдается '
                                        + weather_api_ans['l10n'][day_forecast['condition']])
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
        try:
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
        except Exception:
            pass
        sleep(2)