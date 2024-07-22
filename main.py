# module:    main.py
# author:    Carlos Rodriguez
# Date:      November 10, 2022
# Purpose:   Discord bot with the purpose of playing music
#            uses spotify api to search song names can also search spotify playlists
#            uses pytube to stream/download songs found


import asyncio
import datetime
import os
import json
import nacl
import time
import re
import urllib.request
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from datetime import date
import discord
import pytube
import requests
from anyascii import anyascii
from discord import FFmpegPCMAudio
from discord.ext import commands
from pytube import YouTube
from keep_alive import keep_alive
from refresh import Refresh
from secrets import spotify_user_id, playlist_id

message_play = ""
intents = discord.Intents.all()
intents.members = True
client = discord.Client(intents=intents)
url = ["", "", "", "", ""]
bot = commands.Bot(intents=intents, command_prefix='$')
watch_link = []
title = ""
str_msg_list = "PLAYLISTS: "
songs = []
artists = []
playQueue = []
video_length = 0
bot_playlist = []
next_song = []
count = 0
counter = 0
playlist_total = 0
msg = ""
song_name = ""
skip_song = False
playlist_response = ''

'''
SPOTIFY_USERNAME, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
THESE NEED PRIOR SET UP WITH THE SPOTIFY API WHICH CAN BE FOUND HERE >> https://developer.spotify.com/documentation/web-api
'''
SPOTIFY_USERNAME='31nqczrdhhi2y4o2pnyv53ihfncq'
SPOTIPY_CLIENT_ID='3c7d7773da494e2db73293f7361348b3'
SPOTIPY_CLIENT_SECRET='3b72a8bf993642869c4caf9b6af3fb11'
SPOTIPY_REDIRECT_URI='https://github.com/TEAMPOQ/DiscordBotG'

restart_time = (time.time() + 3300)                # used as a timer to restart script
playlist_ID = ''
track_id = ''

scope = 'playlist-modify-public'

token = spotipy.SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI ,scope=scope, username=SPOTIFY_USERNAME)
# Get the access token
token_info = token.get_cached_token()
spotifyObject = spotipy.Spotify(auth=token)



class SaveSongs:
    def _init_(self):
        self.user_id = spotify_user_id
        self.spotify_token = " "
        self.playlist_id = playlist_id
        self.playlist_total = 0
        self.tracks = [" "]
        self.song_to_search = " "
        self.alb_uri = [" ", " ", " ", " "]



    ############### GET PLAYLIST ###############
    ############################################
    def get_playlists(self):
        global str_msg_list
        global bot_playlist
        bot_playlist.clear()
        str_msg_list = "PLAYLISTS: "
        list_num = 1
        spotifyObject.set_auth(self.spotify_token)
        playlist_res = spotifyObject.current_user_playlists(limit=25, offset=0)
        print(playlist_res)
        while str(playlist_res).find("'name': ") != -1:
            num = str(playlist_res).find("'name': ")
            secondHAlf = str(playlist_res)[num:]
            bot_playlist.append(secondHAlf[9:secondHAlf.find("',")])

            str_msg_list += '\n' + str(list_num) + '. ' + secondHAlf[9:secondHAlf.find("',")]
            playlist_res = str(playlist_res)[num+9:]
            list_num += 1


    ############ GET PLAYLIST SONGS ############
    ############################################
    def get_playlists_songs(self):
        global str_msg_list, playlist_response, bot_playlist, playlist_ID, songs, artists

        str_msg_list = "SONGS: "
        list_num = 0
        playlist_songs  = spotifyObject.playlist_items(playlist_id=playlist_ID, limit=25, offset=0, market=None)
        num_tracks      = spotifyObject.playlist_items(playlist_id=playlist_ID, limit=25, offset=0, market=None, fields='total')
        song_names      = spotifyObject.playlist_items(playlist_id=playlist_ID, limit=25, offset=0, market=None, fields="items(track(name))")
        temp_str_songs = str(song_names)
        append_str = ""
        trackss = str(num_tracks)[10: -1]
        for x in range(int(trackss)-1):
            artists_names = spotifyObject.playlist_items(playlist_id=playlist_ID, limit=1, offset=int(x),
                                                         market=None, fields="items(track(artists(name)))")
            temp_str_artists = str(artists_names)
            try:
                print(playlist_songs['items'][int(list_num)]['track']['name'])
                str_msg_list += str(int(x+1)) + ". " + playlist_songs['items'][int(list_num)]['track']['name'] + " | "
                # save song names
                temp_str_songs = temp_str_songs[temp_str_songs.find("'name': '")+9:]
                songs.append(temp_str_songs[:temp_str_songs.find("'")])
                # save artists names
                print(temp_str_artists)
                temp_str_artists = temp_str_artists[temp_str_artists.find("'name': '") + 9:]
                print(temp_str_artists)
                while True:
                    append_str += temp_str_artists[0:temp_str_artists.find("'")] + " "              # string with all artists in a song
                    if temp_str_artists.find("'name': '") == -1:                                    # break condition
                        break
                    temp_str_artists = temp_str_artists[temp_str_artists.find("'name': '") + 9:]    # updating value

                print("song #"+str(int(x)) + " " + append_str)                                      # debugging purpose
                artists.append(append_str)                                                          # append artists
                append_str = ""                                                                     # clear temp string
                list_num += 1
            except:
                pass


        #print(songs)
        print(songs)
        print(artists)

    ############# SEARCH PLAYLIST ##############
    ############################################
    def search_playlist(self):
        global songs
        global artists
        global playlist_total
        global playlist_ID

        # query search
        query = "https://api.spotify.com/v1/playlists/{}?limit=25".format(playlist_ID).replace(" ", "")
        response = requests.get(query,
                                headers={"Content-Type": "application/json", "Authorization": "Bearer {}".format(self.spotify_token), "Host": "api.spotify.com"})

        response_json = response.json()
        playlist_total = response_json["tracks"]["total"]       # get playlist size
        if playlist_total > 25:                                 # if size is larger than 25 set to 25
            playlist_total = 25


        for x in range(playlist_total):                                                 # for size of playlist add the song and artist to list
            songs.append(response_json["tracks"]["items"][x]["track"]["name"])
            artists.append(response_json["tracks"]["items"][x]["track"]["album"]["artists"][0]["name"])

    ############# Create Playlist ##############
    ############################################
    def create_playlist(self, name):
        global spotifyObject
        try:
            today = date.today()                                # get today's date
            todayFormatted = today.strftime("%d/%n/%Y")         # format the date day/month/year

            # Function to create a playlist
            spotifyObject.user_playlist_create(user='31nqczrdhhi2y4o2pnyv53ihfncq', name=str(name), public=True, description=str(name))

        except Exception as err:
            print(f'An error occurred: {err}')

    ############# Select Playlist ##############
    ############################################
    def select_playlist(self, name):
        global bot_playlist
        global playlist_ID
        a.get_playlists()                                                                                           # INITIALIZE bot_playlist
        print(bot_playlist)
        index = 0                                                                                                   # KEEP TRACK OF PLAYLIST INDEX
        print(name)
        for x in bot_playlist:
            if str(x).find(str(name)) != -1:                                                                        # FIND IF PLAYLIST EXISTS
                break
            index += 1
        playlist_ID = spotifyObject.user_playlists(user=SPOTIFY_USERNAME, offset=0)['items'][index]['id']           # GRAB PLAYLIST ID

    ############# ADD TO PLAYLIST ##############
    ############################################
    def add_playlist(self, name):
        global playlist_ID
        global track_id
        a.search_song(name)                                                                                         # lookup the song by name
        print(track_id)                                                                                             # ensure the track id is correct
        spotifyObject.playlist_add_items(playlist_id=playlist_ID, items=[track_id], position=0)                     # Function to add a song to a playlist

    ############### SEARCH SONG ################
    ############################################
    def search_song(self,msg):
        global message_play, track_name, track_id, artists, songs, token

        self.song_to_search = msg  # song_to_search
        query = "http://api.spotify.com/v1/search/?type=track&q={}&include_external=audio&limit=4&market=US&limit=1".format(self.song_to_search)    # function to look up a song with spotify api

        track_name = [""]
        artist_name = [""]

        response = requests.get(query, headers={"Content-Type": "application/json", "Authorization":"Bearer {}".format(self.spotify_token)})
        response_json = response.json()

        if response_json["tracks"]["total"] <= 0:                                               # check for zero songs in list
            print("Playlist is to short")

        track_id = response_json["tracks"]["items"][0]["id"]                                    # song id
        track_name[0] = response_json["tracks"]["items"][0]["name"]                             # song name
        artist_name[0] = response_json["tracks"]["items"][0]["album"]["artists"][0]["name"]     # artist Name

        #set the urls
        message_play = "https://www.youtube.com/results?search_query={}".format(msg.replace(" ", "+").replace("&", "and"))
        print(message_play)

    ########## REFRESH SPOTIFY TOKEN ###########
    ############################################
    def call_refresh(self):
        print("Refreshing token")
        refreshCaller = Refresh()
        self.spotify_token = refreshCaller.refresh()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))



############ GETS RAN EVERYTIME  ############
############ A MESSAGE IS SENT   ############


@client.event
async def on_message(ctx):
    global playlist_total, counter, msg, skip_song, video_length, str_msg_list, restart_time, songs, artists, token

    # ensures a new token
    if int(time.time()) > int(restart_time):    # timer check
        a.call_refresh()                        # call refresh token or else Spotify api timeout
        restart_time = time.time() + 3300       # update token refresh timer

    if ctx.author == client.user:               # checks to see if the message was sent by a bot
        return
    msg = ctx.content                           # gets the content of the message
    channel = ctx.author.voice.channel          # gets channel to the channel that the author is in
    voice = ctx.channel.guild.voice_client      # used to check if voice is active

    ############################ USER COMMANDS #############################
    ########################################################################
    ########################################################################

    ########### FORCE TOKEN REFRESH ############
    ############################################
    if msg.lower().startswith('$refresh'):
        #Refresh.refresh(ctx)
        #token = spotipy.SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
        #                             redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope, username=SPOTIFY_USERNAME)
        #spotifyObject = spotipy.Spotify(auth_manager=token)
        a.call_refresh()
        restart_time = time.time() + 3300  # update token refresh timer

    ############ LIST ALL PLAYLIST #############
    ############################################
    if msg.lower().startswith('$p list'):
        a.get_playlists()
        await sendMsg(ctx, str_msg_list)

    ######## LIST ALL SONG IN PLAYLIST #########
    ############################################
    if msg.lower().startswith('$p songs'):
        a.get_playlists_songs()
        await sendMsg(ctx, str_msg_list)

    ########### CREATE A  PLAYLIST #############
    ############################################
    if msg.lower().startswith('$p create'):
        a.create_playlist(msg[10:])                #send command to create a new playlist

    ########### SELECT A  PLAYLIST #############
    ############################################
    if msg.lower().startswith('$p select'):
        a.select_playlist(msg[10:])                #send command to create a new playlist

    ############## ADD A PLAYLIST ##############
    ############################################
    if msg.lower().startswith('$p add'):
        if len(playlist_ID) < 1:
            await sendMsg('SELECT A PLAYLIST BEFORE ADDING A SONG-__-')
        else:
            a.add_playlist(msg[7:])

    ############# PLAY A  PLAYLIST #############
    ############################################
    if msg.lower().startswith('$p play'):
        songs.clear()
        artists.clear()
        await playlistplay(ctx)



    ################ SKIP SONG ################
    ###########################################
    if msg.lower().startswith('$skip'):
        try:
            playlist_total -= 1                         # adjust for list total
            counter += 1                                # adjust for index
            await stop(ctx)
            skip_song = True
            print(asyncio.get_event_loop())

        except:
            print("Event loop stopped before Future completed")

    ############## SKIP PLAYLIST ##############
    ###########################################
    if msg.lower().startswith('$p skip'):
        try:
            songs.clear()                               # clear playlist data
            artists.clear()                             # clear playlist data
            await stop(ctx)                             # stop audio stream
            await reset()                               # reset all variables

        except:
            print("Error skipping playlist")

    ################ PLAY A SONG ##############
    ###########################################
    if msg.lower().startswith('$play'):
        try:
            await play(ctx, msg[6:])
        except os.error as e:
            print("error playing song: " + e)

        await reset()  # call to reset variable

    ################ SPAM A USER ##############
    ###########################################
    if msg.lower().startswith('$spam'):
        #try:
        username_spam = msg[6:]                 # username were going to spam
        #await spamUser(ctx, username_spam)     # commented it out abuse potential to high a.k.a dont trust moe

    ################ CONNECT BOT TO CHANNEL #############
    #####################################################
    if msg.lower().startswith('$connect'):
        await connect(ctx)


    ############## PRINT LIST OF FUNCTIONS ##############
    #####################################################
    if msg.lower().startswith('$help'):
        await help(ctx)



############################ BOT FUNCTIONS #############################
########################################################################
########################################################################



############# LIST ALL FUNCTIONS    #############
#################################################
async def help(ctx):
    music_channel = client.get_channel(965814271063781396)
    await music_channel.send('$p add [song name] - adds a song top playlist'
                             '\n$connect - connects bot to channel'
                             '\n$p create [name] - creates a playlist'
                             '\n$p list - will list all playlists'
                             '\n$play [song name] - will play a song'
                             '\n$p play - plays a playlist(must select a playlist)'
                             '\n$p select [name of playlist] - selects a playlist'
                             '\n$skip - skips a song'
                             '\n$spam [@user] - spams @\'s a user'
                             '\n$p songs - lists all songs in selected playlist'
                             '\n$p skip - skips all songs in the playlist')


############### SEND A MSG FUNCTION #############
#################################################
async def sendMsg(ctx, str_msg):                                # takes in a msg
    music_channel = client.get_channel(965814271063781396)      # this is a static id you would have to change it manually
    await music_channel.send(str_msg)                           # send the message to the text channel


################ SPAM USER FUNCTION #############
#################################################
@client.event
async def spamUser(ctx, username):
    channel = ctx.author.voice.channel
    text_channels = ctx.channel.guild.text_channels
    text_channel = text_channels[0]

    mentions = discord.AllowedMentions(everyone=True, users=True, roles=True, replied_user=True)
    for x in range(1000):
        await asyncio.sleep(2)
        await channel.send(username, allowed_mentions=mentions)
        x += 1


################ PLAY PLAYLIST FUNCTION #############
#####################################################
@client.event
async def playlistplay(ctx):
    global playlist_total
    global playlist_ID
    global counter
    global msg
    global skip_song
    global video_length
    global songs
    global artists

    counter = 0

    if ctx.author == client.user:                                       # checks to see if the message was sent by a bot
        return

    a.get_playlists_songs()                                             # search playlist function call with spotify api

    for x in songs:
        try:
            temp = str(songs[int(counter)] + " " + artists[int(counter)])
            print(temp)
            await play(ctx, temp)
            # play song function
        except:
            print('error with play')

        test = asyncio.get_running_loop()                           # wait for song to finish
        end = test.time() + video_length                            # calculate the end of the current song
        counter += 1

        while True:                                                 # while song is playing do
            print(datetime.datetime.now())                          # print time stamp
            if (test.time() + 1.0) >= end or skip_song is True:     # loop break condition
                skip_song = False                                   # reset skip condition
                break
            await asyncio.sleep(1)                                  # timeout

        print("playlist error")                                         # catch any execution errors with playlist
    discord.player.VoiceClient.stop(ctx)                                # force stop voice client


################ DOWNLOAD SONG FUNCTION #############
#####################################################
@client.event
async def download(ctx):
    global watch_link, title, video_length, count, song_name

    music_channel = client.get_channel(965814271063781396)
    channel = ctx.author.voice.channel
    voice = ctx.author.voice
    out_file = None

    print('1')                                                              # debug purposes
    yt = YouTube(str(watch_link))                                           # url input from user

    print('2!')
    try:
        # get the audio stream
        #audio = yt.streams.filter(only_audio=True, abr='160kbps').first()   # get stream

        # Filter audio-only streams and sort by bitrate in descending order
        audio_streams = yt.streams.filter(only_audio=True).order_by('abr').desc()
        # Get the highest bitrate audio stream
        audio = audio_streams.first()

        # download the audio stream to a file
        print('passed  audio = yt.streams.filter')
        audio.download(output_path='./', filename='song.mp3')               # download
    except Exception as e:
        print(e)
        print("download failed")
        pass
    await music_channel.send(song_name + " will begin shortly!") # send in discord chat


################ CONNECT BOT TO CHANNEL #############
#####################################################
async def connect(ctx):
    voice = ctx.author.voice
    channel = ctx.author.voice.channel
    try:
        await channel.connect()
    except:
        pass

    print("connected{0.user}".format(client))


################ PLAY SONG FUNCTION #################
#####################################################
@client.event
async def play(ctx, song):
    channel = ctx.author.voice.channel          # get voice channel of author
    voice = ctx.channel.guild.voice_client

    print('1')                                  # used for debugging
    a.search_song(song)                         # call the search song function to search spotify for the song
    print('2@')
    await getYoutubeUrls()                      # get url link for the desired song
    print('3')
    print('4')
    try:
        print('5')
        await download(ctx)                     # attempt to download the song
        # play song function
    except:
        print('error with download')
    try:
        if voice is None:
            voice = await channel.connect()         # connects if to channel if not already connected
        else:
            await voice.move_to(channel)            # moves to the same channel at the author
            voice.stop()

        source = FFmpegPCMAudio("song.mp3")
        player = voice.play(source)                 # play the song that was downloaded
    except os.error as e:
        print("error playing song: " + e)


############### DISCONNECT BOT FUNCTION #############
#####################################################
@client.event
async def leave(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_connected():
        await voice.disconnected()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


################ PAUSE SONG FUNCTION ################
#####################################################
@client.event
async def pause(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
    else:
        await ctx.send("Currently no audio is playing.")


################ ESUME SONG FUNCTION ###############
#####################################################
@client.event
async def resume(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice.is_paused():
        voice.resume()
    else:
        await ctx.send("The audio is not paused.")

################# STOP SONG FUNCTION ################
#####################################################
async def stop(ctx):
    voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
    voice.stop()


################ GET VIDEO DURATION #################
#####################################################
async def GetDuration():
    global watch_link, video_length
    info = requests.get(watch_link)                         # get request of youtube url video
    info = info.text                                        # set info to the source
    info = info[info.find('approxDurationMs":"')+19:]       # grab the video duration in milliseconds
    info = info[:info.find('"')]                            # cut off unneeded text
    video_length = (int(info)/1000)                         # convert milliseconds to seconds
    print(video_length)

############# GET URL FOR SONG FUNCTION #############
#####################################################
@client.event
async def getYoutubeUrls():
    global message_play
    global watch_link
    global video_length
    global song_name
    video_ids = []

    print('1y')
    html = urllib.request.urlopen(anyascii(message_play))           # get request
    print('2y')
    response = html.read()                                          # response text
    print('3y')
    video_ids = re.findall(r"watch\?v=(\S{11})", str(response))     # find all occurrences of text watch\?v= response save as the video id's
    print('4y')
    watch_link = "https://www.youtube.com/watch?v=" + video_ids[1]  # attach video id to link to get complete video url
    print('5y')
    try:
        vid = pytube.YouTube(watch_link)                                # using pytube set vid to YouTube video with desired url
        song_name = vid.title                                           # grab video title with .title function
        print(video_ids)

    except os.error as e:
        print(e)

    print('6y')
    await GetDuration()                                             # I believe pytube has a get duration function however it broke one time so I create one
    print(watch_link)

############# RESET VARIABLES FUNCTION ##############
#####################################################
@client.event
async def reset():
    global watch_link, url, title, songs, artists, count, counter, playlist_total, msg, skip_song, playlist_ID, bot_playlist, song_name, playlist_response, track_id, message_play
    url = ["", "", "", "", ""]
    watch_link = []
    title = ""
    songs = []
    artists = []
    count = 0
    counter = 0
    playlist_total = 0
    msg = ""
    playlist_ID = ""
    skip_song = False
    message_play = ""
    url = ["", "", "", "", ""]
    watch_link = []
    title = ""
    songs.clear()
    artists.clear()
    bot_playlist = []
    song_name = ""
    playlist_response = ''
    track_id = ''



a = SaveSongs()
a.call_refresh()
keep_alive()
client.run("ODk5NTYxMDIyOTI5NjQ5Njg0.GqU9AO.zXI-3u5j9xclASBq9zdVamlqlaZl_BDQ7mx_JA")        # Put Discord token

