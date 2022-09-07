import asyncio
import websockets
import requests
import json
import random
import csv
import time
import threading
import difflib
import re
import redis


from countdown import getCountDown 
from cleanTimetable import whoIsToday,cleanList
pool = redis.ConnectionPool(host='localhost', port=6379)
SHOW_ANS_DURATION = 15
def sendReply(message):
    requests.get('http://localhost:6500/send_group_msg?group_id=718768433&access_token=HPyuko12!!!&message='+message)

def myErrWordList(groupID,sender):
    r = redis.Redis(connection_pool=pool)
    userId = sender['user_id']
    redisErrWordListKey = 'errWordList#' + str(userId)
    wordList = r.lrange(redisErrWordListKey,0,-1)
    msg = ''
    for index,word in enumerate(wordList):
        msg = msg + str(index+1) +"、" + str(word.decode('utf8')) +"\n\n"
    startSendMsgThread(groupID,str(msg),0)

def handleMsg(groupID,recvMsg,sender):
    global currentWord,ansList
    # 如果在猜词中，则不回复
    if(currentWord != {}):
        sender['reply'] = recvMsg
        ansList.append(sender)
        return

    sendMsg = '未知指令'
    if(recvMsg.find('倒计时')!=-1):
        sendMsg = str(getCountDown())

    if(recvMsg.find('今天是谁')!=-1):
        sendMsg = str(whoIsToday())

    if(recvMsg.find('接下来')!=-1):
        sendMsg = str(cleanList())
    
    if(recvMsg.find('我的错词本')!=-1):
        sendMsg = str(myErrWordList(groupID,sender))
        return

    if(recvMsg.find('语音') != -1):
        sendMsg = '[CQ:record,file=clock@5.mp3]'

    if(recvMsg.find('指令')!=-1):
        sendMsg = '倒计时；今天是谁；接下来;我的错词本'

    startSendMsgThread(groupID,sendMsg,0)

# 加载词库
def loadWordDict():
    with open('name_ch.csv', 'r',encoding='gbk') as csv_file:
        wordDict = []
        csv_reader = csv.reader(csv_file)        
        for line in csv_reader:
            wordDict.append({'word':line[0],'mean':line[1]})
        return wordDict

def startSendMsgThread(groupID,msg,delay):
    t = threading.Thread(target=sendMsg, name='aa', args=(groupID,msg,delay))
    t.start()

def sendMsg(groupID,msg,delay):
    time.sleep(delay)
    requests.get('http://localhost:6500/send_group_msg?group_id='+str(groupID)+'&access_token=HPyuko12!!!&message='+msg)

currentWord = {}
ansList = []

def closeGame(groupID,delay,word):
    targetStr = word['mean']
    global currentWord,ansList,pool
    r = redis.Redis(connection_pool=pool)

    time.sleep(delay)
    msg = ''
    scoreMsg = '========积分榜=========\n'
    userIdList = []
    scoreListStr = []
    scoreDict = {}
    for ans in ansList:
        userIdList.append('word#' + str(ans['user_id']))

    # 整理成： {'xxx':xx分,'xxx':xx分}

    historyScoreList = r.mget(userIdList)
    for index,userId in enumerate(userIdList):
        userId = userId.replace("word#","")
        scoreDict[userId] = historyScoreList[index]

    for index,ans in enumerate(ansList):

        nickname = ans['nickname']
        userId = str(ans['user_id'])
        redisKey = 'word#' + str(userId)
        redisErrWordListKey = 'errWordList#' + str(userId)
        if(len(ans['reply']) <=1):
            msg = msg + nickname+"【作弊】，扣10分\n"
            if(scoreDict[userId] == None):
                # print("scoreDict[userId] == None",scoreDict[userId])
                scoreDict[userId] = 0
            scoreDict[userId] = float(scoreDict[userId]) - 10
            r.set(redisKey,scoreDict[userId])       
            continue
        # 当前轮次的得分
        curScore = getEqualRate(targetStr,ans['reply'])
        if(float(curScore)>=0.3):
            msg = msg + str(index+1)+"、" + nickname +'[CQ:face,id=76]，他的回答是【'+ ans['reply'] +'】，加' + str(float(curScore)) +'分\n'
            if(scoreDict[userId] == None):
                # print("scoreDict[userId] == None",scoreDict[userId])
                scoreDict[userId] = 0
            scoreDict[userId] = float(scoreDict[userId]) + float(curScore)
            r.set(redisKey,scoreDict[userId])       
        else:
            r.lpush(redisErrWordListKey,word['word']+" : "+targetStr)
            msg = msg + str(index+1)+"、" + nickname +'[CQ:face,id=77]，他的回答是【'+ ans['reply'] +'】，扣' + str(1 - float(curScore)) +'分\n'
            if(scoreDict[userId] == None):
                # print("scoreDict[userId] == None",scoreDict[userId])
                scoreDict[userId] = 0
            scoreDict[userId] = float(scoreDict[userId]) - (1-float(curScore))
            r.set(redisKey,scoreDict[userId])
    
    print(scoreDict.keys())

    sortedScoreList = []
    
    for index,ans in enumerate(ansList):
        nickname = ans['nickname']
        score = scoreDict[str(ans['user_id'])]
        sortedScoreList.append({'nickname':ans['nickname'],'score':scoreDict[str(ans['user_id'])]})

    sortedScoreList = sorted(sortedScoreList,key=lambda x: x['score'],reverse=True)
    for index,tmpItem in enumerate(sortedScoreList):
        scoreMsg = scoreMsg + str(index+1)+"、" + tmpItem['nickname'] + ": " + str(format(tmpItem['score'],'.2f'))+"\n"

    sendMsg(groupID,str(msg)+"\n"+str(scoreMsg),0)
    

    currentWord = {}
    ansList = []

def handlePokeMsg(groupID,wordDict):
    global currentWord
    if(currentWord!={}):
        return
    # 获取随机单词
    word = random.choice(wordDict)
    sendMsg_1 = word['word']  + '   猜猜是什么意思？   '+str(SHOW_ANS_DURATION)+'秒后公布'
    sendMsg_2 = word['mean'] 
    sendVoice = '[CQ:record,file=https://cdns.qdu.life/a4/listen/'+word['word']+'@6.mp3]'
    currentWord = word
    startSendMsgThread(groupID,sendMsg_1,0)
    startSendMsgThread(groupID,sendVoice,SHOW_ANS_DURATION)
    startSendMsgThread(groupID,sendMsg_2,SHOW_ANS_DURATION)
    t = threading.Thread(target=closeGame, name='aa', args=(groupID,SHOW_ANS_DURATION+1,word))
    t.start()

async def echo(websocket, path):  
    wordDict = loadWordDict()
    async for message in websocket:
        messageJson = json.loads(message)
        print(messageJson)
        # poke
        if(messageJson['post_type'] == 'notice' and messageJson['target_id']==640016689 and messageJson['sub_type'] == 'poke'):
            groupID = messageJson['group_id']
            handlePokeMsg(groupID,wordDict)

        if(messageJson['post_type'] == 'message' and messageJson['message_type']=='group' and (messageJson['message'].find('@小助手')!=-1 or messageJson['message'].find('[CQ:at,qq=640016689]')!=-1)):
            groupID = messageJson['group_id']
            content = messageJson['message'].replace("[CQ:at,qq=640016689]","")
            sender = messageJson['sender']
            handleMsg(groupID,content.strip(),sender)



def getEqualRate(targetStr, inputStr):
    score = 0
    totalScore = 0
    strArr = re.split('[，|；]',targetStr)
    for singleStr in strArr:
        score = score + difflib.SequenceMatcher(None, singleStr, inputStr).quick_ratio()
        totalScore = totalScore + difflib.SequenceMatcher(None, singleStr, singleStr).quick_ratio()
    return format(score,'.2f')

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(websockets.serve(echo, 'localhost', 6900))
    asyncio.get_event_loop().run_forever()
