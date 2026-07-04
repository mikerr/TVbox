#!/usr/bin/python
#
# tvheadend player using vlc with epg overlay
#
import sys, time
import urllib.request, json
import pygame, vlc

channels = []
names = []
urls = []

tvheadend = 'http://tvheadend:9981'

def get_channels():
    # grab channel info from tvheadend
    url = tvheadend + '/playlist/channels'
    print ("Connecting to ", url)
    try: page = urllib.request.urlopen(url)
    except: 
        print ("ERR: cannot connect !")
        return 0

    playlist = page.read().decode().split('#EXT')
    print("Recieved channel list, processing")
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

numchannels = get_channels()
if numchannels == 0: sys.exit(2)

pygame.init()
#screen = pygame.display.set_mode((800,600),pygame.RESIZABLE)
#font = pygame.font.Font(pygame.font.get_default_font(), 36)
#smallfont = pygame.font.Font(pygame.font.get_default_font(), 24)

vlcInstance = vlc.Instance()
vlcInstance.log_unset()
media = vlcInstance.media_new(urls[0])
player = vlcInstance.media_player_new()

# Pass pygame window id to vlc player, so it can render its contents there.
#win_id = pygame.display.get_wm_info()['window']
#player.set_xwindow(win_id)
player.set_media(media)
#pygame.mixer.quit()
player.play()

def overlay(overlaytext,size):
    player.video_set_marquee_int(vlc.VideoMarqueeOption.Enable,1)
    player.video_set_marquee_int(vlc.VideoMarqueeOption.Size,size)
    player.video_set_marquee_int(vlc.VideoMarqueeOption.Timeout,5000)
    player.video_set_marquee_int(vlc.VideoMarqueeOption.Position,6)
    player.video_set_marquee_string(vlc.VideoMarqueeOption.Text,overlaytext)

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

        overlaytext += "\r\n\r\n" + title + "\r\n\r\n" + desc
    if num == 1 : size = 36
    else : size = 24
    overlay(overlaytext,size)


def change_channel(n):
    epg_info(names[n],1)
    media = vlcInstance.media_new(urls[n])
    player.set_media(media)
    player.play()

n = 0
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit(2)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
               n -= 1
               if n < 0 : n = numchannels - 1
               change_channel(n)

            if event.key == pygame.K_RIGHT:
               n += 1
               if n >= numchannels: n = 0
               change_channel(n)

            if event.key == pygame.K_i: epg_info(names[n],2)
            if event.key == pygame.K_q: sys.exit(2)
