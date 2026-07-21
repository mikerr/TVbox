#!/usr/bin/python3
#
# tvheadend player using vlc with epg overlay
#
import os,sys, time
import urllib.request, json
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, vlc

pygame.init()
screen = pygame.display.set_mode((800,600),pygame.RESIZABLE)
pygame.display.set_caption("TiVo")
pygame.key.set_repeat(500,100)

pic = pygame.image.load("img/blank.jpg").convert()
bgpic = pygame.transform.scale(pic, (800, 600))

tvheadend = 'http://tvheadend:9981'

def get_channels():
    channels = []
    # grab channel info from tvheadend
    url = tvheadend + '/playlist/channels'
    #print ("Connecting to ", url)
    try: page = urllib.request.urlopen(url)
    except: 
        print ("ERR: cannot connect !")
        return 0

    playlist = page.read().decode().split('#EXT')
    #print("Recieved channel list, processing")
    for chaninfo in playlist:
        info = chaninfo.split(',')
        if len(info) < 2: continue
        number  = info[0].split('"')[3]
        channel = info[1].split('\n')

        name = channel[0]
        url  = channel[1]

        channels.append(number + "," + name + "," + url)
    return (channels)

def epg_info(channelname,num):
    api_epg = tvheadend + "/api/epg/events/grid?limit=" + str(num) + "&channel="
    try: page = urllib.request.urlopen(api_epg + urllib.parse.quote(channelname))
    except: 
        print ("tvheadend http error", url)
        return
    playlist = page.read().decode()
    data = json.loads(playlist)
    epg = data["entries"]

    overlaytext = channelname
    for i in range(len(epg)):
        title = epg[i]["title"]
        desc  = epg[i]["subtitle"]

        overlaytext += "\n" + title + "\n" + desc
    if num == 1 : size = 36
    else : size = 24
    overlay(overlaytext,size)

def change_channel(n):
    epg_info(names[n],1)

def get_timestring(timestamp):
    local_time = time.gmtime(timestamp)
    timestring = (time.strftime("%H:%M", local_time)) 
    return timestring

def printtext(text,size,pos):

    x,y = pos
    #chop long text to lines
    words = text.split()

    font = pygame.font.Font(pygame.font.get_default_font(), size)
    n = 0 
    line = ""
    for word in words:
        line += word + " "
        while len (line) > 60:
            text_surface = font.render(line, False, "grey")
            screen.blit(text_surface, (x,y + n*size))
            line = ""
            n += 1
    text_surface = font.render(line, False, "grey")
    screen.blit(text_surface, (x,y + n*size))

def epg_grid():

    api_epg = tvheadend + "/api/epg/events/grid?"
    try: page = urllib.request.urlopen(api_epg)
    except: 
        print ("tvheadend http error")
        return
    playlist = page.read().decode()
    data = json.loads(playlist)
    epg = data["entries"]

    for item in epg:
        starttime = get_timestring(int(item["start"]))
        endtime = get_timestring(int(item["stop"]))
        channelnum = item['channelNumber'] 
        channelName = item['channelName'] 
        title = item['title']
        desc = item['subtitle']

        screen.fill(0)
        printtext(title,36, (0,0))
        printtext(desc,24, (0,40))
        
def get_epg():
    api_epg = tvheadend + "/api/epg/events/grid?"
    try: page = urllib.request.urlopen(api_epg)
    except: 
        print ("tvheadend http error")
        return
    playlist = page.read().decode()
    data = json.loads(playlist)
    epg = data["entries"]

    return(epg)

def get_recs():
    api_epg = tvheadend + "/api/dvr/entry/grid_finished"
    try: page = urllib.request.urlopen(api_epg)
    except: 
        print ("tvheadend http error")
        return
    playlist = page.read().decode()

    data = json.loads(playlist)
    recs = data["entries"]
    return recs

        #starttime = get_timestring(int(item["start"]))
        #endtime = get_timestring(int(item["stop"]))
        #channelnum = item['channelNumber'] 
        #channelName = item['channelname'] 
        #title = item['disp_title']
        #desc = item['disp_subtitle']
        #duration = int(int(item['duration']) / 60)
        #url = item['url']

        #media = vlcInstance.media_new(tvheadend + "/" + url)

y = 0
offset = 0
recs = get_recs()
channels = get_channels()
epg = get_epg()

menutitle = "Recordings"

if menutitle == "Recordings":
    # recordings
    items = []
    for rec in recs:
        items.append(rec['disp_title'])

if menutitle == "Channels":
    # channel list
    items = []
    for ch in channels:
        items.append(ch.split(",")[1])

if menutitle == "TV Guide":
    # now on tv guide
    items = []
    for e in epg:
        num = e['channelNumber']
        if (len(num) < 2) : num = "0" + num;
        items.append(num + "," + e['channelName'] + " " + e['title'])
    items.sort();

def draw_ui(title, items):
    global offset

    if offset < 0 : offset = 0
    if offset > len(items) - 8 : offset -= 1

    screen.fill((0,0,120))
    screen.blit(bgpic,(0,0))
    printtext(title,48,(140,40))

    if offset > 0:
        pygame.draw.polygon(screen,"grey",((55,135),(75,135),(65,120)))
    if offset < len(items) - 8 :
        pygame.draw.polygon(screen,"grey",((55,550),(75,550),(65,565)))

    w = 760
    h = 50
    for i in range(8):
       dy = 140 + i * h
       if (i == y):
           #pill highlight
           pygame.draw.rect(screen, "black", (10, dy,w, h))
           pygame.draw.rect(screen, "grey", (10, dy, w, h), 4)
           pygame.draw.ellipse(screen, "black", (w-20, dy, h, h))
           pygame.draw.ellipse(screen, "grey", (w-20, dy, h, h),2)
           pygame.draw.rect(screen, "black", (10, dy+2, w, h - 4))

       text = items[i+offset]
       printtext ( text,32,(65,dy + 8))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit(2)
        if event.type == pygame.KEYDOWN:
            match(event.key):
                case pygame.K_DOWN:
                    if y < 7 : y += 1
                    else: offset += 1
                case pygame.K_UP:
                    if y > 0 : y -= 1
                    else: offset -= 1
                case pygame.K_q:
                    sys.exit(2)
    draw_ui(menutitle,items)
    pygame.display.update()
