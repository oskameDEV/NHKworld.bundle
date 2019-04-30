#
	#
		# NHK LIVE & VIDEO ON DEMAND CHANNEL FOR PLEX
		# VERSION 1.2 | 04/30/2019
		# BY OSCAR KAMEOKA ~ WWW.KITSUNE.WORK ~ PROJECTS.KITSUNE.WORK/aTV/
	#
#

import time
import requests
import urllib
import re


NAME 			= 'NHK WORLD'
PREFIX 			= '/video/nhk_world'
CHANNELS 		= 'http://projects.kitsune.work/aTV/NHK/schedule.php'
PROGRAMS 		= 'http://projects.kitsune.work/aTV/NHK/videos/directory.json'
RECENTLY 		= 'http://projects.kitsune.work/aTV/NHK/videos/recently.json'
JSON_URL 		= 'http://projects.kitsune.work/aTV/NHK/videos/'

ICON 			= 'icon-default.png'
ART    			= 'art-default.jpg'
FALLBACK_THUMB  = 'http://projects.kitsune.work/aTV/NHK/art-DEFAULT.png'


def Start():
	ObjectContainer.title1 		= NAME
	ObjectContainer.art 		= R(ART)

	DirectoryObject.art 		= R(ART)
	VideoClipObject.art 		= R(ART)

	HTTP.CacheTime = 1
	HTTP.ClearCache()

	Dict.Reset()

	load_JSON()

####################################################################################

@handler(PREFIX, NAME, ICON)
def MainMenu():

	oc 	= ObjectContainer()

	# USER PREFS
	force_HD 	= Prefs['force_HD']

	# ADD LIVE STREAM OBJECT FIRST
	item = Dict['channels'][0]
	# SET URL
	# IF USER WANTS HD
	liveURL = item['url']
	# v1.2 :: TEMPORARILY TURNED OFF, MAIN STREAM = HD TOO
	#if force_HD:
	#	liveURL = 'https://b-nhkwtvglobal-i.akamaihd.net/hls/live/'+re.findall(r"\D(\d{6})\D", liveURL)[0]+'-b/nhkwtvglobal/index_2100.m3u8'

	oc.add(CreateVideoClipObject(
		url = liveURL,
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
		return ObjectContainer(objects = [vco])
	else:
		return vco

####################################################################################

@route(PREFIX + '/episodes', forced_episode = int)
def Episodes(title, stub, url, forced_episode = None):
	oc = ObjectContainer(title2 = title)
	json_data = JSON.ObjectFromString(HTTP.Request(url, cacheTime = 1).content)
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
	HTTP.ClearCache()

	oc = ObjectContainer(title2 = title)
	json_data = JSON.ObjectFromString(HTTP.Request(RECENTLY, cacheTime = 1).content)
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
	HTTP.CacheTime = 1
	HTTP.ClearCache()

	# GENERATE RANDOM HEX TO ENSURE JSON IS FRESH
	ID 		= HTTP.Request('https://plex.tv/pms/:/ip').content
	RNG 	= HTTP.Request('http://projects.kitsune.work/aTV/NHK/ping.php?IP='+str(ID)).content

	# LOAD CHANNELS JSON
	is_dst 		= time.daylight and time.localtime().tm_isdst > 0
	utc_offset 	= - (time.altzone if is_dst else time.timezone)
	try:
		dataLIVE = JSON.ObjectFromString(HTTP.Request(CHANNELS+'?tz='+str(utc_offset)+'&v='+RNG, cacheTime = 1).content)
	except Exception:
		Log("NHK :: Unable to load [LIVE STREAM] JSON.")
	else:
		Dict['channels'] = dataLIVE

	# LOAD EPISODES JSON
	try:
		dataPrograms = JSON.ObjectFromString(HTTP.Request(PROGRAMS+'?v='+RNG, cacheTime = 1).content)
	except Exception:
		Log("NHK :: Unable to load [VIDEOS] JSON file.")
	else:
		Dict['programs'] = dataPrograms

	# LOAD RECENT SHOWS JSON
	try:
		dataRecently = JSON.ObjectFromString(HTTP.Request(RECENTLY+'?v='+RNG, cacheTime = 1).content)
	except Exception:
		Log("NHK :: Unable to load [RECENT] JSON.")
	else:
		Dict['recently'] = dataRecently
	return MainMenu()

####################################################################################

# @route(PREFIX + '/live')
# def openLive(url):
# 	return Redirect(url)
