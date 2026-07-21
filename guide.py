#!/usr/bin/python
#
# tvheadend player using vlc with epg overlay
#
import os,sys, time
import urllib.request, json
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame, vlc

channels = []
names = []
urls = []

tvheadend = 'http://tvheadend:9981'

def get_channels():
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

        channels.append(number)
        names.append(name)
        urls.append(url)
    return (len(channels))

def overlay(text,size):
    screen.fill(0)

    font = pygame.font.Font(pygame.font.get_default_font(), size)
    text = text.replace("\r","")
    lines = text.split("\n")
    n = 0
    for line in lines:
        text_surface = font.render(line, False, (255, 255, 255)) 
        screen.blit(text_surface, (0,n*size))
        n += 1

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
            text_surface = font.render(line, False, (255, 255, 255)) 
            screen.blit(text_surface, (x,y + n*size))
            line = ""
            n += 1
    text_surface = font.render(line, False, (255, 255, 255)) 
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
        
def show_recs():
    api_epg = tvheadend + "/api/dvr/entry/grid_finished"
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
        #channelnum = item['channelNumber'] 
        channelName = item['channelname'] 
        title = item['disp_title']
        desc = item['disp_subtitle']
        duration = int(int(item['duration']) / 60)
        url = item['url']

        screen.fill(0)
        printtext(title + " (" + str(duration) + " min)",32, (10,0))
        printtext(desc,24, (10,40))

        
        #media = vlcInstance.media_new(tvheadend + "/" + url)

numchannels = get_channels()
if numchannels == 0: sys.exit(2)

pygame.init()
screen = pygame.display.set_mode((800,600),pygame.RESIZABLE)
pygame.display.set_caption("TV")

show_recs()

n = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit(2)
        if event.type == pygame.KEYDOWN:
            match(event.key):
                case pygame.K_LEFT | pygame.K_p:
                   n -= 1
                   if n < 0 : n = numchannels - 1
                   change_channel(n)

                case pygame.K_RIGHT | pygame.K_n:
                   n += 1
                   if n >= numchannels: n = 0
                   change_channel(n)

                case pygame.K_r: 
                    show_recs()
                case pygame.K_i: 
                    epg_info(names[n],2)
                case pygame.K_c | pygame.K_l: 
                    epg_grid()
                case pygame.K_q: 
                    sys.exit(2)
    pygame.display.update()
