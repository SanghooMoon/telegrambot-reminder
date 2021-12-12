from datetime import datetime


def timeFormatCheck(time):
    return time.isdigit() and len(time) == 4 and 0 <= int(time) <= 2359


def duplicateNameCheck(tasks, name, chatId):
    for task in tasks:
        if task.chatId == chatId and task.name == name:
            return True

    return False


def isWeekend():
    return datetime.today().weekday() > 4


def isHoliday(holidays, sysdate):
    for holiday in holidays:
        if holiday == sysdate:
            return True

    return False
