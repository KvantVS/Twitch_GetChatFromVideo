'''
1. GET-запрос к 'https://api.twitch.tv/v5/videos/' + videoId + '/comments'
   в заголовке: content_offset_seconds=0 и client_id
   Получаем json-список сообщений чата на 6 минут
2. В конце объекта будет объект "_next": с длиииииинным длинным ID.
   Берем этот ID
3. Для следующих сообщений делаем GET-Запрос к https://api.twitch.tv/v5/videos/205529476/comments?cursor=<ID который взяли в п.2>
(например: https://api.twitch.tv/v5/videos/205529476/comments?cursor=eyJpZCI6ImIzMWZiOWVlLWEwMDItNGY1My1iYWNiLTYzMThkZGQxZTAzNCIsImhrIjoiYnJvYWRjYXN0OjI2ODU5MTYyNzg0Iiwic2siOiJBQUFBV0E2SlNFQVUtLWFNTU1XYlFBIn0f)
'''

import time, datetime
import sys
import requests
import re
import os
from os.path import dirname, realpath, join, exists
from twitch_basic import ConvertTime, ConvertTime2, sendRequest, GetInfoAboutVideo,\
    CID_chatWriter, API_V5CLOSED, STR_CLIENT, STR_ACCEPT, HEADER_AcceptV5


ttt1 = time.time()

secondsToSplitMoments = 15 #11
non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
clientId = CID_chatWriter
V5header = {STR_ACCEPT: HEADER_AcceptV5,
            STR_CLIENT: clientId}


def getClip(slug):
    print(f'Обрабатываем {slug}...')
    url = f'https://api.twitch.tv/kraken/clips/{slug}'
    j = sendRequest(url, V5header)
    clipAuthor = j['curator']['display_name'].translate(non_bmp_map) if 'curator' in j else ''
    clipTitle = j['title'].translate(non_bmp_map) if 'title' in j else ''
    clipViews = j['views'] if 'views' in j else 0
    clipDuration = j['duration'] if 'duration' in j else 0
    if 'vod' in j:
        if j['vod'] is not None:
            if 'offset' in j['vod']:
                clipOffset = j['vod']['offset']
            else:
                clipOffset = 0
        else:
            clipOffset = 0
    else:
        clipOffset = 0
    return (clipAuthor, clipTitle, clipViews, clipOffset, clipDuration)


# https://www.twitch.tv/videos/505944491           337878165 https://www.twitch.tv/videos/321608652
videoList = ['']  #, '355484291', '355946365', '356914013'
# https://www.twitch.tv/videos/485436096 # Закрытое
# https://www.twitch.tv/videos/484963076
# https://www.twitch.tv/videos/484472706
# https://www.twitch.tv/videos/336154410 https://www.twitch.tv/videos/331621245?filter=archives&sort=time https://www.twitch.tv/videos/334080160?filter=archives&sort=timehttps://www.twitch.tv/videos/335381637?filter=archives&sort=time
# https://www.twitch.tv/videos/336628992?filter=archives&sort=time https://www.twitch.tv/videos/336631466?filter=archives&sort=time
# https://www.twitch.tv/videos/336631653?filter=archives&sort=time https://www.twitch.tv/videos/338426345?filter=archives&sort=time
# https://www.twitch.tv/videos/339270124?filter=archives&sort=time https://www.twitch.tv/videos/347247494?filter=archives&sort=time

if len(sys.argv) > 1:
    videostring = sys.argv[1]
    if videostring.endswith('.txt') or videostring.endswith('.txt"'):
        print('ЗАШЛИ')
        textVideosFile = videostring
        with open(textVideosFile, 'r') as fff:
            videoListTemp = fff.readlines()
            videoList = [i[:-1] for i in videoListTemp if i.endswith('\n')]
            videoList.append(videoListTemp[len(videoListTemp) - 1])
    else:
        videoList = videostring.split(',')
else:
    print('usage: {0} <video1id,video2id,video3id,...>'.format(sys.argv[0]))

for videoId in videoList:
    l_wowmoments = []
    l_wowmoments.clear()
    l_clips = []
    l_clips.clear()
    l_serials = []
    l_serials.clear()
    l_links = []
    l_links.clear()
    l_coubs = []
    l_coubs.clear()

    # url = f'{API_V5CLOSED}videos/{videoId}/comments?content_offset_seconds=0'
    # h = {STR_ACCEPT: HEADER_AcceptV5,
    #      STR_CLIENT: clientId}
    # r = requests.get(url, headers=h)
    # j = r.json()

    # формат: время_системы (время_относительно_начала_ролика)  ник: сообщение
    messFormat = '%s (%s) (%s)  %s: %s\n'
    videoTimeFormat ='%02d:%02d:%02d'

    sChannel, userId, sVideoCreated, sVideoName, sGame, jjj = GetInfoAboutVideo(
        videoId, True)
    print(jjj)
    videoDuration = jjj['length']

    # folderTemplate = join(dirname(realpath(__file__)), 'Streams', sChannel)   # dirname(realpath(__file__)) + f"\\Streams\\{sChannel}\\"
    folderTemplate = join('E:\\Streams', sChannel)   # dirname(realpath(__file__)) + f"\\Streams\\{sChannel}\\"
    #dtVideoCreated = datetime.datetime.strptime(sVideoCreated, "%Y-%m-%dT%H_%M_%SZ") #.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    #sVideoCreated = dtVideoCreated.strftime("%Y-%m-%d--%H-%M-%S").translate(non_bmp_map)
    outputFilename = join(folderTemplate, f'{sChannel}_{sVideoCreated}_{videoId}')

    print('id:', videoId)
    print('Канал:', sChannel)
    print('Видео:', sVideoName)
    print('Дата создания видео:', sVideoCreated)

    if not exists(folderTemplate):
        os.makedirs(folderTemplate)
    print('файл: ', outputFilename)

    # ==========================================================================
    h = {STR_ACCEPT: HEADER_AcceptV5,
         STR_CLIENT: clientId}
    j = sendRequest(f'{API_V5CLOSED}videos/{videoId}/comments?content_offset_seconds=0', h)

    print('Пишем чат...')
    canProduce = True
    i = 0
    with open(outputFilename + '.txt', 'wb') as chatfile:
        while canProduce:
            if 'comments' in j:
                for msg in j['comments']:
                    s_msgTime = msg['created_at']
                    s_msgText = msg['message']['body']
                    s_msgType = msg['source']
                    s_msgNickname = msg['commenter']['display_name']
                    i_timeRelative = msg['content_offset_seconds']

                    #2017-11-13T13:00:17.710599Z
                    #2017-11-13T13:00:17Z
                    s_msgTime = s_msgTime[:-1].split('.')[0]

                    dt_msgTime = datetime.datetime.strptime(s_msgTime, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
                    s_msgTime = dt_msgTime.strftime("%H:%M:%S")   #.translate(non_bmp_map)

                    i_timeRelativeSecs, i_timeRelative = ConvertTime(i_timeRelative)
                    i_timeRelativeMinutes, i_timeRelative = ConvertTime(i_timeRelative)
                    i_timeRelativeHours, i_timeRelative = ConvertTime(i_timeRelative)
                    s_timeRelative = videoTimeFormat % (i_timeRelativeHours, i_timeRelativeMinutes, i_timeRelativeSecs)  #время относительно начала ролика
                    s_msgType = s_msgType[:4]

                    message = messFormat % (s_msgTime, s_timeRelative, s_msgType, s_msgNickname, s_msgText)
                    # 04:43:15 (3:38:43) (chat)  JIucToyxuu: мне показалось или там был проигнорен глушак на пп?
                    # 04:43:15 (3:38:43) (comm)  JIucToyxuu: мне показалось или там был проигнорен глушак на пп? # комментарий добавленный ВНЕ стрима

                    chatfile.write(message.encode('utf-8'))

                    ######################################################
                    # ^([^\S]*LUL[\s]*)+$ --- for LUL LUL LUL
                    # ^([\S]+LUL[\s]*)+$ ---- blackufaLUL blackufaLUL
                    # ^[ах]+\)*[\s]*$ ---------- for ахах
                    # ^[X:;]D*\)*[\s]*$ - XD, xDDDD, :DD, ;DDDD
                    #srch = re.search('^([^\S]?(LUL|WlgLUL|PogChamp|МЛЖ|МЛГ|млг|ЭмЭлДжи|DansGame|SeemsGood|CurseLit|GTChimp|SwiftRage|CarlSmile|CoolStoryBob|blackufaCoolstory)      [\s]*)+$|^     ([\S]+LUL[\s]?)+$|                                              ^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$', s_msgText, re.IGNORECASE)
                    srch = re.search('(?i)^([^\S]?(LUL|OMEGAROLL|hyperWOW|WLGW|POG|PogChamp|WutFace|MLG|МЛЖ|МЛГ|млг|ЭмЭлДжи|DansGame|SeemsGood|CurseLit|GTChimp|SwiftRage|CarlSmile|CoolStory|pepeLaugh|KEKW|dangarLol|BSUTrolled)[\s]*)+$|^([\s]?[\S]+LUL[\s]?)+|^([\s]?[\S]+MLG[\s]?)+|^([\s]?[\S]+RAGE[\s]?)+|^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$', s_msgText, re.IGNORECASE)
                    #srchLUL = re.search('(?i)^([^\S]?(LUL|OMEGAROLL|pepeLaugh|KEKW|Lol|BSUTrolled|:D)[\s]*)+$|^([\s]?[\S]+LUL[\s]?)+|^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$', s_msgText, re.IGNORECASE)
                    #srchPOG = re.search('(?i)^([^\S]?(hyperWOW|POG|PogChamp|PagChomp)[\s]*)+$', s_msgText, re.IGNORECASE)
                    #srchMLG = re.search('(?i)^([^\S]?(MLG|МЛЖ|МЛГ|млг|ЭмЭлДжи)[\s]*)+$|^([\s]?[\S]+MLG[\s]?)+$', s_msgText, re.IGNORECASE)
                    #srchCoolStory = re.search('(?i)^([^\S]?(CarlSmile|CoolStory)[\s]*)+$|^([\s]?[\S]+CoolStory[\s]?)+$', s_msgText, re.IGNORECASE)
                    #srchRage = 
                    #srchScary = WutFace, монки всячкие DansGame

                    srch
                    # (?i)^([^\S]?(LUL|hyperWOW|PogChamp|MLG|МЛЖ|МЛГ|млг|ЭмЭлДжи|DansGame|SeemsGood|CurseLit|GTChimp|SwiftRage|CarlSmile|CoolStoryBob|blackufaCoolstory)[\s]*)+$|^([\s]?[\S]+LUL[\s]?)+|^([\s]?[\S]+MLG[\s]?)+|^([\s]?[\S]+RAGE[\s]?)+|^[ах]+\)*[\s]*$|^[X:;]D*\)*[\s]*$|^хд*\)*[\s]*$
                    # srch2 = re.search('^([^\S]?MLG[\s]*)+$|^([\S]+MLG[\s]?)+$', s_msgText, re.IGNORECASE)
                    srch3 = re.search('^клип', s_msgText, re.IGNORECASE)
                    srch_clips = re.search('(?i)^.*clips.+\/(?!create)', s_msgText, re.IGNORECASE)
                    srch_coub = re.search('(?i)^.*coub.+\/(?!welovegames)', s_msgText, re.IGNORECASE)
                    srch_serials = re.search('сериал', s_msgText, re.IGNORECASE)
                    # srch_links = re.search('http.*|https.*|', s_msgText, re.IGNORECASE)

                    if (srch or srch3):
                        s = f'{s_timeRelative} {s_msgNickname}: {s_msgText}'
                        l_wowmoments.append(s)
                        # print(len(l_wowmoments))

                    if srch_clips:
                        s = f'{s_timeRelative} {s_msgNickname}: {s_msgText}'
                        l_clips.append(s)

                    if srch_coub:
                        s = f'{s_timeRelative} {s_msgNickname}: {s_msgText}'
                        l_coubs.append(s)

                    if srch_serials:
                        s = f'{s_timeRelative} {s_msgNickname}: {s_msgText}'
                        l_serials.append(s)

                if i % 5 == 0:
                    print('%0.2f%%...' % (msg["content_offset_seconds"] / videoDuration * 100))

                i += 1
            else:
                print('Нету comments in j')
                print(j)
                canProduce = False

            if '_next' in j:
                jNext = j['_next']
                while 1:
                    try:
                        url = f"{API_V5CLOSED}videos/{videoId}/comments?cursor={jNext}"
                        r = requests.get(url, headers=h)
                        j = r.json()
                    except:
                        print('Try to sleeping 5 seconds...')
                        time.sleep(5)
                    else:
                        break
            else:
                canProduce = False
    ttt2 = time.time()

    print('100%')
    print(ttt2 - ttt1)

    ###

    ttt1 = time.time()
    momentsFilename = outputFilename + '_moments.txt'
    with open(momentsFilename, 'w', encoding='utf8') as wowFile:
        if l_wowmoments:
            print('ИТОГО кол-во моментов:', len(l_wowmoments))
            #previousDT = datetime.datetime.strptime(l_wowmoments[0][:8], '%H:%M:%S')
            # Время
            lsdt = l_wowmoments[0][:8].split(':')
            h = int(lsdt[0])
            m = int(lsdt[1])
            sec = int(lsdt[2])
            h, dayss = ConvertTime(h, 24)
            previousDT = datetime.datetime(1970, 1, 1, h, m, sec)
            previousDT = previousDT + datetime.timedelta(days=dayss)
            momentCount = 1
            wowFile.write('1\n')
            for s in l_wowmoments:
                #currentDT = datetime.datetime.strptime(s[:8], '%H:%M:%S')
                lsdt = s[:8].split(':')
                h = int(lsdt[0])
                m = int(lsdt[1])
                sec = int(lsdt[2])
                h, dayss = ConvertTime(h, 24)
                currentDT = datetime.datetime(1970, 1, 1, h, m, sec)
                currentDT = currentDT + datetime.timedelta(days=dayss)
                # --- вставляем строку если между моментами больше 15-ми секунд, для наглядности
                diff = abs((currentDT - previousDT).seconds)
                if diff > secondsToSplitMoments:
                    wowFile.write('--------\n')
                    momentCount += 1
                    wowFile.write(str(momentCount) + '\n')
                ws = s[:8] + f' (+{diff}) ' + s[9:] + '\n'
                # ws = s + '\n'
                wowFile.write(ws)
                previousDT = currentDT

        # l_slugs = []
        if l_clips:
            wowFile.write('\n = КЛИПЫ = \n')
            # set_clips = set(l_clips)
            for clip in l_clips:
                sr = re.search('^(.*clips.+\/)(\S+)', clip, re.IGNORECASE)  # можно добавить if sr:
                slug = sr.group(2)
                clipAuthor, clipTitle, clipViews, clipOffset, clipDuration = getClip(slug)
                h, m, sec = ConvertTime2(clipOffset)
                hs = '%02d:' % h if h != 0 else ''
                ms = '%02d:' % m if m != 0 else ''
                timeString = '%s%s%02d' % (hs, ms, sec)
                writestr = f'{clip} ({clipAuthor}) ({timeString} - {clipDuration})\n'
                wowFile.write(writestr)
                # l_slugs.append(slug)

        # if l_slugs:
        #     ',id='.join(l_slugs)

        if l_coubs:
            wowFile.write('\n = КОУБЫ = \n')
            for s in l_coubs:
                ws = s + '\n'
                wowFile.write(ws)

        if l_serials:
            wowFile.write('\n = СЕРИАЛЫ :) = \n')
            for s in l_serials:
                ws = s + '\n'
                wowFile.write(ws)

    ttt2 = time.time()

    print('WOW-файл готов! Это заняло', ttt2 - ttt1, 'секунд')
    import subprocess
    cmdline = '"C:\\Program Files\\Sublime Text 3\\sublime_text.exe" "' + momentsFilename + '"'
    proc = subprocess.Popen(cmdline, shell=True, stdout=subprocess.PIPE)
    out = proc.stdout.readlines()
    l_wowmoments.clear()
    l_clips.clear()
    l_coubs.clear()
    l_serials.clear()
    l_links.clear()
    
#####################
# input()
