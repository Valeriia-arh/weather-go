import telepot
from telepot import delegate
from weather_answer import WeatherAnswer
from urllib import request, parse
import requests
from bs4 import BeautifulSoup
import numpy as np

URL = "https://api.telegram.org/bot%s/" % "507008666:AAEJ8TTGpJ-1idOAgF0ZVjiMnezzaaAitMY"
TOKEN = "507008666:AAEJ8TTGpJ-1idOAgF0ZVjiMnezzaaAitMY"

#https://github.com/nickoala/telepot


class WeatherGo(telepot.helper.ChatHandler):

    def __init__(self, *args, **kwargs):
        super(WeatherGo, self).__init__(*args, **kwargs)
        self.weather_answer = WeatherAnswer()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type == 'sticker':
            bot.sendMessage(chat_id, "Thank you for sticker :) It is for you:")
            handler = self.weather_answer.if_sticker()

            url = request.urlopen(next(handler))
            self.sender.sendChatAction('upload_photo')
            self.sender.sendPhoto(('kitten.png', url))
            url.close()

        elif content_type == 'text':

            if msg['text'].startswith('/start'):
                self.sender.sendMessage(text="Вы хотите узнать погоду?\n"
                                        "Для ознакомления со списком возможностей запросите /help")
            elif msg['text'].startswith('/help'):
                self.sender.sendMessage(text='''Список команд бота:\n
            /start -- приветственное слово
            /help -- вывести список команд данного бота\n
            Для получения погоды отправьте боту запрос. Бот поддерживает следующие виды запросов:\n
            * Москва
            * Погода в Москве
            * Какая погода в Москве сейчас(завтра, вчера)
            * Погода в Москве через n дней
            * Какая погода в Москве через n дней
            * Погода во вторник (и другие дни недели)
            * Москва через неделю
            * Погода в Москве через неделю
            * Вы можете отправить стикер\n
            Если вы опечатались в названии города или написали его с маленькой буквы, то правильный запрос будет выполнен\n
            Предложения по улучшению приветствуются @valeriia06''')
            else:
                handler = self.weather_answer.get_answer(msg['text'])
                self.sender.sendMessage(next(handler))

                url = request.urlopen(next(handler))

                self.sender.sendChatAction('upload_photo')
                self.sender.sendPhoto(('weather.png', url))
                url.close()

                self.sender.sendMessage(next(handler))


if __name__ == '__main__':
    bot = telepot.DelegatorBot(TOKEN, [
        delegate.pave_event_space()(delegate.per_chat_id(), delegate.create_open, WeatherGo, timeout=3600)
    ])
    bot.message_loop(run_forever='Waiting for your messages ...')
