class Task:
    def __init__(self, chatId, name, sendTime, msg, dayOfWeek):
        self.chatId = chatId
        self.name = name
        self.sendTime = sendTime
        self.msg = msg
        self.dayOfWeek = dayOfWeek

    def printInfo(self):
        infoMsg = "[이름=%s" % self.name

        if self.dayOfWeek != "":
            infoMsg += ", 요일=%s" % self.dayOfWeek
        infoMsg += ", 요청시간=%s시%s분]\n%s\n\n" % (self.sendTime[:2], self.sendTime[2:], self.msg)

        return infoMsg

    def dayToInt(self):
        day = self.dayOfWeek
        dayToInt = ""

        for d in day:
            if d == "월":
                dayToInt += "0"
            elif d == "화":
                dayToInt += "1"
            elif d == "수":
                dayToInt += "2"
            elif d == "목":
                dayToInt += "3"
            elif d == "금":
                dayToInt += "4"

        return dayToInt
