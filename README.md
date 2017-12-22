# Google Spreadsheet CRM | googlesheetsearch
Проект, позволяющий дропшипперам (удалённым розничным продавцам) быстро узнавать наличие товара у любого количества поставщиков через доступные онлайн Google Таблицы. Доступна функция уведомления по отслеживаемым поисковым фразам с помощью Telegram-бота.

Project that allow to dropshippers (remote retailers) quickly search for the product's availability that might has some of the wholesalers (who are using Google Spreadsheet to share info). Also it allow to use handy notification about changin the status of availability with a help of Telegram bot.

## С чего начать? | Getting Started

Что бы запустить приложение, нужно развернуть у себя базу данных MySQL из файла googlesheetsearch_db.sql

Open the MySQL database with this command:
```
$ mysql googlesheetseach < googlesheetsearch_db.sql
```
Установить список зависимостей

Install dependencies:
```
$ pip install -r requirements.txt
```
Создать своего бота в Телеграм или подключить существующего. Необходим токен. Полученный токен вписать в config/telebot_config.ini

Create your bot in Telegrams or connect an existing one. Token is required. The received token should be written to config / telebot_config.ini
```
...
TOKEN = 
...
```
Также в этом же файле необходимо указать настройки базы данных. Хост, пользователя, пароль, кодировку и название базы данных, которую Вы создали.

Also, in the same file, you must specify the database settings. Host, user, password, encoding and the name of the database that you created.
```
[BOT]
host = localhost
user = root
passwd = 123456789
charset = utf8mb4
db = googlesheetsearch
```
## Демонстрация работы приложения | Demonstration

![](https://i.imgur.com/1dkA9S1.gif)

Встроенный поиск позволяет сразу же добавить запрос, который не дал результатов, в таблицу базы данных, который автоматически фоново проверяет Телеграм-бот с определённой переодичностью.

The built-in search allows to immediately add a query that hadn't given any results to the database table, which is automatically checked by the Telegram-bot with a certain periodicity.

![](https://i.imgur.com/ag0nGUN.gif)

Если содержимое таблиц поменяется, бот узнает об этом (для примера он проверяет один раз в 30 секунд) и сообщит пользователю. Поэтому не нужно беспокоиться и самостоятельно проверять все интересующие запросы. Каждый запрос присылается отдельным сообщением, дабы проще было найти интересующий пункт.

If the content of the tables changed, the bot will know about this (for example, it checks once every 30 seconds) and informs the user. Therefore, you do not have to worry and independently check all the queries you are interested in. Each request is sent by a separate message, so it's easier to find the item of interest.

![](https://i.imgur.com/0TD1I2e.gif)

Для индексирования по таблицам необходимы [учётные данные OAuth](http://gspread.readthedocs.io/en/latest/oauth2.html). Таким образом можно получить сервисный адрес электронной почты, который обязательно нужно добавить в разрешённые адреса тех таблиц, по которым будет осуществляться поиск.

For table indexing, you need [OAuth credentials] (http://gspread.readthedocs.io/en/latest/oauth2.html). Thus, you can get a service e-mail address, which should be added to the allowed addresses of those tables, which will be searched.

## Сделано с помощью | Built with
* [gspread](https://github.com/burnash/gspread) - API для общения с Google Spreadsheet.

## Сделать | TODO
* Вкладку в приложении для настройки бота
* React-форму для добавления более сложных заготовок поиска (размеры, цвет, цена)