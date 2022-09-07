import datetime
peopleGroup = [["黄鹏宇","李梓赫"],["张宇晨","赵文钦"],["辛鹏辉","王延庆"],["柳炳辰","刘庆斌"]]
def whoIsToday():
	a = datetime.datetime.now()  # 实施时间
	b = datetime.datetime(2022, 8,30)  # 自己设置的研究生考试时间
	countDown = (a-b).days  # 倒计时
	return '今天由【' + ",".join(peopleGroup[countDown%len(peopleGroup)]) + '】打扫卫生\n'+'明天由【' + ",".join(peopleGroup[(countDown+1)%len(peopleGroup)]) + '】打扫卫生\n'

def cleanList():
	a = datetime.datetime.now()  # 实施时间
	b = datetime.datetime(2022, 8,30)  # 自己设置的研究生考试时间
	countDown = (b - a).days  # 倒计时
	text = ""
	for i in range(1,6):
		text = text + get_date(i)[0] +"："+ get_date(i)[1] +"\n"

	return '接下来五天为\n' + text

def get_date(addDays):
	dateFormat = "%m-%d"
	timeNow = datetime.datetime.now()
	startTime = datetime.datetime(2022, 8,30)  # 自己设置的研究生考试时间

	if (addDays!=0):
		anotherTime = timeNow + datetime.timedelta(days=addDays)
	else:
		anotherTime = timeNow
	countDown = (anotherTime - startTime).days
	return (anotherTime.strftime(dateFormat),",".join(peopleGroup[countDown%len(peopleGroup)]))


if __name__ == '__main__':
	print(whoIsToday())
	print(cleanList())