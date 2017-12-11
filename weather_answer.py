import json
from pymorphy2 import MorphAnalyzer
import requests
from urllib import parse
import numpy as np
import datetime
from bs4 import BeautifulSoup
from re import findall


# X-Yandex-API-Key: <значение ключа>.
yandex_weather_api = "982cb0f7-f2ba-44ec-92ff-90ee399c473e"
weather_url = "https://api.weather.yandex.ru/v1/forecast?"
yandex_images = "https://yandex.ru/images/search?"
geocode_api = "ALE7KFoBAAAAxjFoSQIAQFBGrRuPnisd6EkLloUTb3eoswUAAAAAAAAAAADOD03ZsPDuCGpKozkdjv4P_1zRsQ=="
geocode_url = 'http://geocode-maps.yandex.ru/1.x/?'

# https://tech.yandex.ru/maps/doc/geocoder/desc/concepts/input_params-docpage/


class WeatherAnswer:
    """
    lat=<широта>
    lon=<долгота>
    l10n - объект расшифровок значений погодных состояний, направления ветра и фаз Луны.
    You give some place and receive latitude and longitude
    """

    def __init__(self):
        self.grammar = MorphAnalyzer()

    def find_place(self, place):
        request = requests.get(geocode_url + parse.urlencode({
                             'geocode': place,
                             'key': geocode_api,
                             'results': 1,
                             'format': 'json'}))
        js = json.loads(request.text)

        coordinates = js['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        lon = coordinates.split()[0]
        lat = coordinates.split()[1]

        return lon, lat, place

    def get_weather(self, lon, lat, time):
        weather_params = parse.urlencode({
            'lat': lat,
            'lon': lon,
            'l10n': 'true'
        })
        request = requests.get(weather_url + weather_params,
                         headers={
                             'X-Yandex-API-Key': yandex_weather_api
                         })

        js = json.loads(request.text)

        forecast = js['forecasts']
        hours = js['forecasts'][0]['hours']

        predictions = []
        for day in forecast:
            for prediction in day['hours']:
                predictions.append(prediction)

        forecast = self.the_closest(predictions, time)

        """
        Little example to show output data
        print(place) #Архангельск
        print(js['l10n'][forecast['condition']]) #небольшой снег
        print(forecast['temp'])  # -10
        print(forecast['feels_like'])  # -14
        print(forecast['humidity'])  # 89
        print(forecast['wind_speed'])  # 1
        print(forecast['pressure_mm'])  #757
        """

        description = js['l10n'][forecast['condition']]
        temp = forecast['temp']
        feels = forecast['feels_like']
        hum = forecast['humidity']
        w_speed = forecast['wind_speed']
        pres = forecast['pressure_mm']

        return description, temp, feels, hum, w_speed, pres

    def the_closest(self,predictions, time):
        """
        in prediction.txt we see that forecast changes ("hour_ts\":1512594000),
        so we need to take the most accurate prediction
        """
        timestamps = [x['hour_ts'] for x in predictions]
        difference = np.array(timestamps) - time.timestamp()
        num = (abs(difference)).argmin()
        return predictions[num]

    def get_image(self, text):
        """
        Будем искать случайную картинку по заданным параметрам (по description)
        http://modx.im/blog/questions/2495.html
        """
        if text == "ясно":
            text = "ясное небо"
        request = requests.get(yandex_images +
                               parse.urlencode({'text': text,
                                                'user-agent': 'Mozilla/5.0 '
                                                              '(compatible; '
                                                              'MSIE 9.0; Windows NT 6.1;'
                                                              'WOW64; Trident/5.0; '
                                                              'chromeframe/12.0.742.112)'}))
        images = BeautifulSoup(request.text, 'html.parser').find_all('img')
        result_image = images[np.random.randint(0, len(images))]

        image_url = 'http:' + result_image['src']
        return image_url

    def get_joke(self):
        """
        Выдает случайную шутку о погоде из подготовленного списка
        """

        with open('jokes.txt') as file:
            joke = [row.strip() for row in file]

        return joke[np.random.randint(0, len(joke))]


    with open('dictionary_for_parsing.json') as file:
        dictionary_for_parsing = json.load(file)

    def get_answer(self, text):

        place = self.get_city(text)
        time = self.get_data(text)

        lon, lat, place = self.find_place(place)
        description, temp, feels, hum, w_speed, pres = self.get_weather(lon, lat, time)

        weather_prediction = '{}, {}: {}.\nТемпература: {} °C\nПо ощущению: {} °C\n' \
                             'Влажность воздуха: {}%\nСкорость ветра: {} м/с\n' \
                             'Атмосферное давление: {} мм.рт.ст'.format(
                                                                 place,
                                                                 time.strftime('%d.%m.%Y'),
                                                                 description,
                                                                 temp,
                                                                 feels,
                                                                 hum,
                                                                 w_speed,
                                                                 pres
                             )

        yield weather_prediction

        image_url = self.get_image(description)
        yield image_url

        joke = self.get_joke()
        yield joke

    def get_city(self, text):
        place_ = text.split()[0]
        places = findall(r'[в,В] (\w+)', text)
        for place in places:
            if place.lower() not in self.dictionary_for_parsing['week_forms']:
                place_ = self.grammar.parse(place)[0].normal_form

        return place_.title()

    def get_data(self, text):

        time_now = datetime.datetime.now()
        words = text.split()

        for item, timedelta_h in self.dictionary_for_parsing['day_forms'].items():
            if item in words:
                return time_now + datetime.timedelta(hours=timedelta_h)

        for item, timedelta_h in self.dictionary_for_parsing['day_forms'].items():
            if item in words:
                return time_now.replace(hour=timedelta_h)

        for number, day in enumerate(self.dictionary_for_parsing['week_forms']):
            if day in words:
                timedelta_d = (number - time_now.weekday()) % 7
                return time_now + datetime.timedelta(days=timedelta_d)

        for number, day in enumerate(self.dictionary_for_parsing['other_forms']):
            if day in words:
                timedelta_d = (number - time_now.weekday()) % 7
                return time_now + datetime.timedelta(days=timedelta_d)

        in_week = findall(r'через неделю', text)
        if in_week:
            return time_now + datetime.timedelta(days=7)

        in_days = findall(r'через (\d+)', text)
        if in_days:
            return time_now + datetime.timedelta(days=int(in_days[0]))

        return time_now

    def if_sticker(self):
        r = requests.get(yandex_images +
                         parse.urlencode({'text': 'котики',
                                          'user-agent': 'Mozilla/5.0 '
                                                        '(compatible; '
                                                        'MSIE 9.0; Windows NT 6.1;'
                                                        'WOW64; Trident/5.0; '
                                                        'chromeframe/12.0.742.112)'}))

        images = BeautifulSoup(r.text, 'html.parser').find_all('img')
        result_image = images[np.random.randint(0, len(images))]

        image_url = 'http:' + result_image['src']
        yield image_url
