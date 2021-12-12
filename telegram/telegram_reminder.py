import json
import os
import pickle
import re
import time
import requests
import schedule
import logging

from os.path import getsize

from telegram.ext import Updater
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from message import *
from task import Task
from utils import *


my_token = os.getenv("TELEGRAM_BOT_TOKEN")
updater = Updater(token=my_token, use_context=True)
dispatcher = updater.dispatcher
holidays = []
tasks = []
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# 각 명령어 메서드 정의
# /help : 기본 도움말
def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=MSG_HELP)


# /show : 각 채팅방 리마인더 목록
def show(update: Update, context: CallbackContext):
    chatId = update.effective_chat.id
    count = 0
    taskInfo = ""

    for task in tasks:
        if task.chatId == chatId:
            count += 1
            taskInfo += task.printInfo()

    sendMsg = "총 건수 : %d 건\n" % count
    sendMsg += taskInfo.replace("\\n", "\n")

    context.bot.send_message(chat_id=chatId, text=sendMsg)


# /add : 매일 리마인더 추가(공휴일/주말 제외)
def add(update: Update, context: CallbackContext):
    chatId = update.effective_chat.id

    if len(context.args) >= 3:
        name = context.args[0]
        time = context.args[1]

        if not timeFormatCheck(time):
            context.bot.send_message(chat_id=update.effective_chat.id, text="올바르지 않은 시간 형식입니다.(HH24MM)")
            return

        if duplicateNameCheck(tasks, name, chatId):
            context.bot.send_message(chat_id=update.effective_chat.id, text="이미 존재하는 이름입니다.")
            return

        msg = update.effective_message.text.split(' ')
        del msg[0:3]
        msg = " ".join(msg)

        tasks.append(Task(chatId, name, time, msg, ""))
        sendMsg = "[%s] 추가되었습니다." % name
        context.bot.send_message(chat_id=update.effective_chat.id, text=sendMsg)


# /addWeek : 특정요일 리마인더 추가(공휴일/주말 제외)
def addWeek(update: Update, context: CallbackContext):
    chatId = update.effective_chat.id

    if len(context.args) >= 4:
        name = context.args[0]
        day = context.args[1]
        time = context.args[2]

        if not timeFormatCheck(time):
            context.bot.send_message(chat_id=update.effective_chat.id, text="올바르지 않은 시간 형식입니다.(HH24MM)")
            return

        if duplicateNameCheck(tasks, name, chatId):
            context.bot.send_message(chat_id=update.effective_chat.id, text="이미 존재하는 이름입니다.")
            return

        regex = re.compile("월?화?수?목?금?")
        m = regex.search(day).group()
        if m != day:
            context.bot.send_message(chat_id=update.effective_chat.id, text="요일을 입력해주세요[월-금]")
            return

        msg = update.effective_message.text.split(' ')
        del msg[0:4]
        msg = " ".join(msg)

        tasks.append(Task(chatId, name, time, msg, day))
        sendMsg = "[%s] 추가되었습니다." % name
        context.bot.send_message(chat_id=update.effective_chat.id, text=sendMsg)


# /remove : 리마인더 삭제
def remove(update: Update, context: CallbackContext):
    if len(context.args) == 1:
        name = context.args[0]
        chatId = update.effective_chat.id

        for idx, task in enumerate(tasks):
            if task.chatId == chatId and task.name == name:
                del tasks[idx]
                sendMsg = "%s : 삭제되었습니다." % name
                context.bot.send_message(chat_id=update.effective_chat.id, text=sendMsg)
                return

        context.bot.send_message(chat_id=update.effective_chat.id, text="삭제할 대상이 없습니다.")


# 등록된 리마인더 발송
def sendReminder():
    yymmdd = datetime.today().strftime("%Y%m%d")
    hhmm = datetime.today().strftime("%H%M")
    day = str(datetime.today().weekday())

    if not isWeekend() and not isHoliday(holidays, yymmdd):
        for task in tasks:
            if task.dayOfWeek:
                if task.sendTime == hhmm and day in task.dayToInt():
                    updater.bot.send_message(chat_id=task.chatId, text=task.msg)
            else:
                if task.sendTime == hhmm:
                    updater.bot.send_message(chat_id=task.chatId, text=task.msg)


# 공휴일 등록
def setHolidays(year):
    key = os.getenv("TELEGRAM_HOLIDAY_KEY")
    url = 'http://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo'
    params = {'serviceKey': key, 'solYear': year, 'numOfRows': '30', '_type': 'json'}
    response = requests.get(url, params)

    jsonObject = json.loads(response.content)
    items = jsonObject.get("response").get("body").get("items").get("item")

    for holiday in items:
        holidays.append(holiday.get("locdate"))


#  리마인더 리스트 파일로 저장
def saveFile():
    with open("tasks.p", "wb") as file:
        pickle.dump(tasks, file)


# 리마인더 리스트 파일 읽기
def readFile():
    file = ''
    if getsize("tasks.p") > 0:
        with open("tasks.p", "rb") as file:
            file = pickle.load(file)

    for t in file:
        tasks.append(t)


# 명령어 등록
def setHandler():
    help_handler = CommandHandler('help', help)
    show_handler = CommandHandler('show', show)
    add_handler = CommandHandler('add', add)
    addWeek_handler = CommandHandler('addWeek', addWeek)
    remove_handler = CommandHandler('remove', remove)

    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(show_handler)
    dispatcher.add_handler(add_handler)
    dispatcher.add_handler(addWeek_handler)
    dispatcher.add_handler(remove_handler)

    updater.start_polling()
    schedule.every().minute.at(":01").do(sendReminder)
    schedule.every(10).minutes.do(saveFile)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    readFile()
    setHolidays(2022)
    setHolidays(2023)
    print("공휴일 API : %d" % holidays.__len__())
    setHandler()
