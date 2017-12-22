import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import telebot
import MySQLdb
from aiotg import Bot, Chat
import pymysql
import pymysql.cursors

import configparser
config = configparser.ConfigParser()
config.read('config/telebot_config.ini')

scope =['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('product_spreadsheets.json', scope)
client = gspread.authorize(creds)

db = pymysql.connect(host=config['BOT']['host'],
                     user=config['BOT']['user'],
                     passwd=config['BOT']['passwd'],
                     charset=config['BOT']['charset'],
                     db=config['BOT']['db'],
                     cursorclass=pymysql.cursors.DictCursor)

def search(searchquery):
    products = []
    cur = db.cursor()
    result = cur.execute("SELECT * FROM customers")
    tables = cur.fetchall()
    tablenames = [i['tablename'] for i in tables]
    names = [i['name'] for i in tables]
    for tablename, name in zip(tablenames, names):
        try:
            searchobject = client.open(tablename).sheet1
            regular = re.escape(searchquery)
            criteria_re = re.compile(regular)
            cells = searchobject.findall(criteria_re)
            for cell in cells:
                appending = searchobject.row_values(cell.row)
                appending.insert(0, name)
                products.append(appending)
        except:
            continue

    return products

#Telegram bot
TOKEN = config['BOT']['TOKEN']
bot = telebot.TeleBot(TOKEN)
chatid = ""

@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    if message.text == "notify":
        chatid = message.chat.id
        bot.send_message(chatid, "Уведомления включены")
        f(f_stop, chatid=message.chat.id)
    else:
        outmessage = []
        products = search(message.text)
        for p in range(0, len(products)):
            outmessage.append(" ".join(products[p]))
            outmessage.append("--------------------------------")
        bot.send_message(message.chat.id, "\n".join(outmessage))

import threading
def f(f_stop, chatid):
    outmessage = []
    bot.send_message(chatid, "Проверяю запросы из базы")
    cur = db.cursor()
    result = cur.execute("SELECT * FROM checklist")
    checklist = cur.fetchall()
    searchquerys = [i['searchrequest'] for i in checklist]
    print(searchquerys)
    for searchquery in searchquerys:
        products = search(searchquery)
        if not products == []:
            try:
                outmessage.append("По запросу " + searchquery)
                for p in range(0, len(products)):
                    outmessage.append(" ".join(products[p]))
                    outmessage.append("--------------------------------")
                bot.send_message(chatid, "\n".join(outmessage))
                outmessage.clear()
                products.clear()
            except:
                exceptmessage = "Пока ничего по запросу " + searchquery
                bot.send_message(chatid, exceptmessage)
        else:
            exceptmessage = "Пока ничего по запросу " + searchquery
            bot.send_message(chatid, exceptmessage)
    if not f_stop.is_set():
        threading.Timer(config['BOT']['delay'], f, [f_stop, chatid]).start()

f_stop = threading.Event()

bot.polling()
