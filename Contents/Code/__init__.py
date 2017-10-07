#
#
# NHK VIDEO ON DEMAND CHANNEL FOR PLEX
# VERSION 1.0 | 09/05/2017
# BY OSCAR KAMEOKA ~ WWW.KITSUNE.WORK ~ PROJECTS.KITSUNE.WORK/aTV/
#
#

import requests


NAME 			= 'NHK WORLD'
PREFIX 			= '/video/nhk_world'
CHANNELS 		= 'http://projects.kitsune.work/aTV/NHK/videos/NHK_LIVESTREAM.json'
PROGRAMS 		= 'http://projects.kitsune.work/aTV/NHK/videos/directory.json'
RECENTLY 		= 'http://projects.kitsune.work/aTV/NHK/videos/recently.json'
JSON_URL 		= 'http://projects.kitsune.work/aTV/NHK/videos/'

ICON 			= 'icon-default.png'
ART    			= 'art-default.jpg'
FALLBACK_THUMB  = 'http://projects.kitsune.work/aTV/NHK/art-DEFAULT.png'


def Start():
	# SET VIEW
	Plugin.AddViewGroup("Details", viewMode="InfoList", mediaType="items")

	ObjectContainer.title1 		= NAME
	ObjectContainer.art 		= R(ART)
	ObjectContainer.view_group 	= 'Details'

	DirectoryObject.art 		= R(ART)
	VideoClipObject.art 		= R(ART)

	HTTP.CacheTime = 0
	HTTP.ClearCache()

	Dict.Reset()

	load_JSON()

####################################################################################

@handler(PREFIX, NAME, ICON)
def MainMenu():

	oc 	= ObjectContainer(view_group="Details", no_cache=True)

	# ADD LIVE STREAM OBJECT FIRST
	item = Dict['channels'][0]
	oc.add(CreateVideoClipObject(
		url = item['url'],
		title = '⁍ WATCH LIVE NOW',
		thumb = R('icon-NHK.png'),
		art = R('art-NHK.jpg'),
		summary = unicode(item['summary'])
	))

	# RECENTLY ADDED VIDEOS
	oc.add(TVShowObject(
		key = Callback(Recently, title = 'RECENTLY ADDED VIDEOS', stub = 0, url = RECENTLY),
		rating_key = '⁍ RECENTLY ADDED VIDEOS',
		title = '⁍ RECENTLY ADDED VIDEOS',
		summary = 'Latest Video Aired On ' + unicode(Dict['recently'][0]['aired']),
		thumb = R('icon-NHK_VOD.png')
	))

	# EACH TV SHOW
	for pgm in Dict['programs']:
		oc.add(
			TVShowObject(
				key = Callback(Episodes, title = pgm['title'], stub = pgm['id'], url = pgm['url']),
				rating_key = pgm['id'],
				title = pgm['title'],
				thumb = Resource.ContentsOfURLWithFallback(pgm['thumb'], FALLBACK_THUMB),
				summary = pgm['summary']
			) 
		)

	return oc

####################################################################################

@route(PREFIX + '/stream')
def CreateVideoClipObject(url, title, thumb, art, summary,
						  c_audio_codec = None, c_video_codec = None,
						  c_container = None, c_protocol = None,
						  optimized_for_streaming = True,
						  include_container = False, *args, **kwargs):

	vco = VideoClipObject(
		key = Callback(CreateVideoClipObject,
					   url = url, title = title, thumb = thumb, art = art, summary = summary,
					   optimized_for_streaming = True, include_container = True),
		rating_key = url,
		title = title,
		thumb = thumb,
		art = art,
		summary = summary,
		url = url,
		items = [
			MediaObject(
				parts = [
					PartObject(
						key = HTTPLiveStreamURL(url = url)
					)
				],
				optimized_for_streaming = True
			)
		]
	)

	if include_container:
		return ObjectContainer(objects = [vco], no_cache=True)
	else:
		return vco

####################################################################################

@route(PREFIX + '/episodes', forced_episode = int)
def Episodes(title, stub, url, forced_episode = None):
	oc = ObjectContainer(view_group="Details", title2 = title, no_cache=True)
	json_data = JSON.ObjectFromString(HTTP.Request(url, cacheTime = None).content)
	#json_data = JSON.ObjectFromURL(data)
	
	for episode in json_data:
		duration = int(episode['duration']) * 1000
				
		oc.add(
			CreateVideoClipObject(
				title = episode['subTitle'],
				summary = episode['summary'],
				thumb = episode['thumb'],
				art = episode['art'],
				url = episode['url'],
			)
		)

	if len(oc) < 1:
		oc.header = "Sorry"
		oc.message = "Couldn't find any episodes for this show"

	return oc

####################################################################################

@route(PREFIX + '/latest', forced_episode = int)
def Recently(title, stub, url, forced_episode = None):
	oc = ObjectContainer(view_group="Details", title2 = title, no_cache=True)
	json_data = JSON.ObjectFromString(HTTP.Request(RECENTLY, cacheTime = None).content)
	#json_data = JSON.ObjectFromURL(data)
	
	for episode in json_data:
		duration = int(episode['duration']) * 1000
				
		oc.add(
			CreateVideoClipObject(
				title = episode['title'] + ' - ' + episode['subTitle'],
				summary = episode['summary'],
				thumb = episode['thumb'],
				art = episode['art'],
				url = episode['url'],
			)
		)

	if len(oc) < 1:
		oc.header = "Sorry"
		oc.message = "Couldn't find any latest episodes"

	return oc

####################################################################################

@route(PREFIX + '/load_list')
def load_JSON():
	HTTP.ClearCache()

	IP 		= HTTP.Request('https://plex.tv/pms/:/ip').content
	PING 	= HTML.ElementFromURL('http://projects.kitsune.work/aTV/NHK/ping.php?IP='+str(IP))

	# LOAD CHANNELS JSON
	try:
		dataA = JSON.ObjectFromString(HTTP.Request(CHANNELS, cacheTime = 0).content)
	except Exception:
		Log("NHK :: Unable to load [LIVE STREAM] JSON.")
	else:
		Dict['channels'] = dataA

	# LOAD EPISODES JSON
	try:
		dataB = JSON.ObjectFromString(HTTP.Request(PROGRAMS, cacheTime = 0).content)
	except Exception:
		Log("NHK :: Unable to load [VIDEOS] JSON file.")
	else:
		Dict['programs'] = dataB

	# LOAD RECENT SHOWS JSON
	try:
		dataC = JSON.ObjectFromString(HTTP.Request(RECENTLY, cacheTime = 0).content)
	except Exception:
		Log("NHK :: Unable to load [RECENT] JSON.")
	else:
		Dict['recently'] = dataC
	return MainMenu()

####################################################################################

@route(PREFIX + '/live')
def openLive(url):
	return Redirect(url)
