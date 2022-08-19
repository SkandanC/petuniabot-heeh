from random import randrange
from typing import List
from requests import request
from datetime import datetime
import discord
from discord_slash import SlashCommand
from discord.ext.commands import Context
import requests
import youtube_dl
import asyncio
from asyncpraw import Reddit


token = 'token'   # bot token

# next 3 lines are needed to be able to log when members leave
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

slash = SlashCommand(client, sync_commands=True)

# delete logs
del_channel: List[discord.TextChannel] = []
del_user: List[discord.Member] = []
del_time: List[datetime] = []
del_message_logs: List[discord.Message] = []
time = datetime.now()
ctx: Context = None

@client.event
async def on_ready():

    """
    Prints bot status in the bot test server. Sets bot activity.
    """

    await client.change_presence(activity=discord.Game('Being cute and derpy'))
    print('Bot Ready')
    channel = client.get_channel(929854932650184747) # id = 929854932650184747 is the id of the general channel in the bot test server
    await channel.send("bot ready")


@slash.slash(name="hug", description="give hugs!")
async def hug(ctx: Context, member: discord.Member):

    """
    Prints randomized hug message by calling the hug() method.
    """

    sender = ctx.author.id  # id of "hug sender"
    reciever = member.id    # id of "hug reciever"
    message = hugs(sender, reciever)    # retrieve randomized hug message
    await ctx.send(str(message))


@slash.slash(name="avatar", description="get avatar of a user")
async def avatar(ctx: Context, member: discord.Member):

    """
    Prints avatar in an embed for specified user.
    """
    
    avurl = member.avatar_url    
    embed= discord.Embed(color=discord.Colour.green()) # set embed color
    embed.add_field(name='Avatar', value = f'<@{member.id}>') # 'naem' field is the embed title. 'value' field is the "description"
    embed.set_image(url=avurl) # attach avatar image url to embed
    await ctx.send(embed=embed)


@slash.slash(name="urbandictionary", description="urban dictionary definitions")
async def urbandictionary(ctx: Context, expression = ""):

    """
    Prints the first urban dictionary definition for expression.
    """

    # UD unofficial API
    url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"
    querystring = {"term":expression}
    headers = {
    'X-RapidAPI-Host': 'mashape-community-urban-dictionary.p.rapidapi.com',
    'X-RapidAPI-Key': 'b3b1de9292msh80cd0fcf49db1d5p13996djsn6e620e40dd7a'
    }

    response = request("GET", url, headers=headers, params=querystring)

    embed= discord.Embed(color=discord.Colour.green())
    lastindex = response.text.find(',')
    embed.add_field(name=expression, value = f'{response.text[24:lastindex-1]}')
    await ctx.send(embed=embed)


@client.event
async def on_member_remove(member: discord.Member):

    """
    Prints a message in the general chat when someone leaves.
    """

    channel = client.get_channel(790638511254011937)    # id = 790638511254011937 is the id of the general chat
    await channel.send(f'{member} has left <:wahhh:790731210602053643>')


@client.event
async def on_message_delete(message: discord.message):

    """
    Logs deleted messages, channel name, user name, and message create time in lists. Pops the oldest message after 3 hrs of bot bootup.
    """

    del_channel.append(message.channel)
    del_user.append(message.author)
    del_time.append(message.created_at)
    del_message_logs.append(message.content)

    if divmod((datetime.now() - time).total_seconds(), 3600)[0] > 3:

        del_channel.pop(0)
        del_user.pop(0)
        del_time.pop(0)
        del_message_logs.pop(0)


@slash.slash(name="deleted-messages", description="deleted messages from past 3 hrs")
async def deleted(ctx):

    """
    Prints the deleted messages, channel name, user name and message creation time from the past 3 hrs.
    """

    message_list = [
        f" ```{del_user[key]} sent message in {del_channel[key]} at {del_time[key]}```: {del_message_logs[key]}\n"
        for key, _ in enumerate(del_message_logs)
    ]

    message = ''.join(map(str, message_list))
    await ctx.send(message)


@slash.slash(name="wordle", description="generates a game of wordle!")
async def wordle(ctx):

    """
    iterations a wordle game and calls the wordle generator.
    """

    won = 0 # logs whether the game is over

    iteration = 0 # logs the number of tries

    guess = [['1', '2', '3', '4', '5']] # logs guesses stripped into individual letters

    wordlist = open('wordlist.txt').readlines() # read from file containing all possible correct words
    number = randrange(len(wordlist) + 1)   
    correct_word = list(wordlist[number][:-1])  # pick a random word
    print(correct_word)

    print_guesses = '' # logs the wordle square block thingy 

    playerid = ctx.author.id
    channel_id = ctx.channel.id

    while won != 1:

        if iteration == 0:

            # Initial embed
            embed = discord.Embed(color=discord.Colour.green())
            embed.add_field(name='Wordle', value='Start making guesses!')
            await ctx.send(embed=embed)

        won, guess, print_guesses = await wordle_generator(ctx, channel_id, guess, correct_word, print_guesses, playerid)   # call wordle generator method and start the next iteration of the game

        iteration += 1

        if iteration == 6:  # game over
            embed = discord.Embed(color=discord.Colour.green())
            embed.add_field(name='Wordle', value=f'<@{ctx.author.id}> lost! \n{print_guesses}')
            await ctx.send(embed=embed)
            break

        if won == 1:    # game won
            break  
        

#parameters for youtube song streaming
youtube_dl.utils.bug_reports_message = lambda: ''

# youtube downloader format options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn -b:a 0.8M',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

# This class generates data later piped to ffmpeg for streaming
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):    # get stream data from youtube link, set stream to False to download song before streaming (takes an insanely longer amount of time!!)
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        title = data['title']
        return filename, title

file_queue: List[discord.FFmpegPCMAudio] = [] # list of songs in a format discord can play
song_queue: List[str] = []  # list of song names
author_list: List[discord.Member] = []  # list of song requesters
count: int = 0  # index of currently playing song


# method to loop until the queue is empty
def play_next(error):

    try:

        next = asyncio.run_coroutine_threadsafe(playit(), loop=client.loop)
        next.result()

    except Exception as e:

        print(e)


# method to download and append songs in a streamable format
async def download(song):

    filename, title = await YTDLSource.from_url(song, loop=client.loop, stream=True)
    play = discord.FFmpegPCMAudio(executable="/usr/bin/ffmpeg", source=filename)    # ffmpeg is required, change executable path accordingly for your system
    file_queue.append(play)
    song_queue.append(title)


# method to play current song
async def playit():

    global count
    play = file_queue[count]
    voice_client = client.voice_clients[0]
    voice_client.play(play, after=play_next)
    count += 1


@slash.slash(name="play", description="play a song")
async def play(ctx: Context,  link: str = '', search: str = ''):

    """
    command to play songs, calls the play_next() method to play the next song in queue
    """

    voice_channel:discord.VoiceChannel = client.get_channel(790705872342482965) # voice channel (chitter-chatter)
    if client.voice_clients == []:

        voice_client = await voice_channel.connect(timeout = 1200,reconnect=True)   # connect to vc

    else:

        voice_client = client.voice_clients[0] # if alreadt connected, get voice channel

    url = ''
    if link != '':

        if requests.get(link).status_code == 200:

            url = link
            if voice_client.is_playing() is True:
                await ctx.send("Song added to queue!")

        else:

            await ctx.send("That is not a valid url.")

    elif search != '':
        search_query = search.split(' ')
        for i, _ in enumerate(search_query):
            url = f'{url}{search_query[i]}+'
        url = url[:-1]
        if voice_client.is_playing() is True:
            await ctx.send("Song added to queue!")

    else:

        await ctx.send('Error: You must specify a song link or search for a song!')


    song = url
    print(song)
    await download(song=song)   # download the song
    author_list.append(ctx.author)


    if voice_client.is_playing() is not True:

        voice_client.play(source=file_queue[count], after=play_next)
        embed = discord.Embed(title='Now playing', colour=discord.Color.green())
        embed.add_field(name=f'{song_queue[count]}', value='\u200b')
        embed.add_field(name='Requested by', value=author_list[count], inline=True)
        await ctx.send(embed=embed)        


@slash.slash(name="pause", description="pause the bot")
async def pause(ctx: Context):

    """
    pause the song
    """

    voice_client:discord.voice_client = client.voice_clients[0]
    voice_client.pause()
    await ctx.send("Paused.")


@slash.slash(name="resume", description="resume the bot")
async def resume(ctx: Context):

    """
    resume playing song
    """

    voice_client:discord.voice_client = client.voice_clients[0]
    voice_client.resume()
    await ctx.send("Resumed.")


@slash.slash(name="queue", description="display song queue")
async def queue(ctx: Context):

    """
    print the song queue
    """

    message = '```\n'
    for num, name in enumerate(song_queue):

        message = f'{message}{num + 1}. {name}, requested by: {author_list[num]}\n'

    message = message + '\n```'

    await ctx.send(message)


@slash.slash(name="queueremove", description="remove song from queue")
async def queueremove(ctx: Context, index: str = 0):

    """
    Remove song from queue given its index
    """

    await ctx.send(f'Removed {song_queue[int(index)-1]}.')
    index = int(index) - 1
    song_queue.pop(int(index))
    file_queue.pop(int(index))
    author_list.pop(int(index))


@slash.slash(name="skip", description="skip to next song")
async def skip(ctx: Context):

    """
    skip the currently playing song
    """

    client.voice_clients[0].pause()
    global count
    count += 1
    await playit()
    await ctx.send("Skipped.")


@slash.slash(name="connect", description="connect to voice channel")
async def connect(ctx: Context):

    """
    connect to vc
    """

    global count
    voice_client: discord.VoiceClient = client.get_channel(790705872342482965)
    await voice_client.connect()
    song_queue.clear()
    author_list.clear()
    file_queue.clear()
    count = 0
    await ctx.send("Hello.")


@slash.slash(name="leave", description="leave voice channel")
async def leave(ctx: Context):

    """
    leave vc
    """

    global count
    voice_client: discord.VoiceClient = client.voice_clients[0]
    await voice_client.disconnect()
    song_queue.clear()
    author_list.clear()
    file_queue.clear()
    count = 0
    await ctx.send("Bye.")


@slash.slash(name="meme", description="post a meme from Reddit")
async def meme(ctx: Context):

    await ctx.defer()
    reddit = Reddit(client_id = "22zNl3X38I-mQJvd2MuJ5A", client_secret="HMxVZEHtMjm5S5zSBGkleh2Ea642uQ", user_agent="petunibot/0.1 by uwrallyx")

    submissions = []
    whenthe = await reddit.subreddit("whenthe", fetch=True)
    shitposting = await reddit.subreddit("shitposting", fetch=True)
    memes = await reddit.subreddit("memes", fetch=True)

    async for sub in whenthe.top(limit=10):

        submissions.append(sub.url)

    async for sub in shitposting.top(limit=10):

        submissions.append(sub.url)

    async for sub in memes.top(limit=10):

        submissions.append(sub.url)

    num = randrange(start = 0, stop = len(submissions)-1)

    await ctx.send(submissions[num])


@slash.slash(name="view-birthdays", description="View server birthdays")
async def view_birthdays(ctx: Context):

    message = '```\n02/23 - Lex\n02/25 - Joanne\n03/19 - Karan\n08/11 - Skandan\n08/26 - skelly\n09/10 - Arjun\n09/15 - Parm\n09/19 - Tij\n09/21 - Tobi\n```'

    await ctx.send(message)
    

@slash.slash(name="help",description="List of commands and descriptions")
async def help(ctx):

    """
    help command
    """

    embed = discord.Embed(title='Help', description='Commands:', color=discord.Colour.green())
    embed.add_field(name='```avatar```', value='Prints the avatar of a user')
    embed.add_field(name='```deleted-messages```', value='Prints deleted messages from the past 3 hrs')
    embed.add_field(name='```hug```', value='Hug a user!')
    embed.add_field(name='```wordle```', value='Start a game of Wordle')
    embed.add_field(name='```urbandictionary```', value='Prints an Urban Dictionary definiton of a word')
    embed.add_field(name='```play```', value='Play a song/ add a song to queue. Takes either youtube links or search queries')
    embed.add_field(name='```pause```', value="Pause the currently playing song")
    embed.add_field(name='```resume```', value="Resume playing songs")
    embed.add_field(name='```skip```', value="Skip to the next song")
    embed.add_field(name='```queue```', value="Print the current queue list of songs")
    embed.add_field(name='```queueremove```', value="Remove a song from the queue given its position in the queue")
    embed.add_field(name='```connect```', value="Connect to the voice channel")
    embed.add_field(name='```leave```', value="Leave the voice channel")
    embed.add_field(name='```meme```', value="Post a meme from Reddit (r/whenthe, r/shitposting, r/memes)")
    embed.add_field(name='```view-birthdays```', value="Print the brithdays of alol the servers members")

    await ctx.send(embed=embed)


async def wordle_generator(ctx, CHANNEL_ID, guess, correct_word, print_guesses, playerid):

    """
    Generates a game of wordle.
    """

    with open('validguesses.txt', 'r') as file:
        validguesses = file.read().replace('\n', '')    # read all possible valid guesses from a file

    msg = await client.wait_for(event="message")   # get word

    if msg.channel.id != CHANNEL_ID or msg.author.id != playerid:
        return -1, guess, print_guesses
    if msg.content not in validguesses:
        await ctx.send(f'{msg.content} is not a valid guess!') 
        return -1, guess, print_guesses

    else:
        check_guess = list(msg.content)

    # check if guess os correct and update the block thingy accordingly
    string = list('⬛⬛⬛⬛⬛\n')
    for key2, _ in enumerate(guess[-1]):
        if check_guess[key2] == correct_word[key2]:
            string[key2] = '🟩'
        elif check_guess[key2] in correct_word:
            string[key2] = '🟨'

    print_guesses = print_guesses + ''.join(string)

    print(check_guess)
    print(correct_word)

        # send messages with the block thingy
    if check_guess == correct_word:
        
        embed = discord.Embed(color=discord.Colour.green())
        embed.add_field(
            name='Wordle',
            value=f"<@{playerid}> won:\nThe word was: {''.join(correct_word)}\n{print_guesses}",
        )

        await ctx.send(embed=embed)
        return 1, guess, print_guesses

    else:

        embed = discord.Embed(color=discord.Colour.green())
        embed.add_field(name='Wordle', value=f'<@{msg.author.id}> guessed:\n{print_guesses}')
        await ctx.send(embed=embed)
        return 0, guess, print_guesses
   

def hugs(sender, reciever):
    
    """
    returns randomized hug message. 🤗
    """

    messagedict = {
        
        0 : f'<@{sender}> stalks <@{reciever}> for information on their hugging habits, and then proceeds to hug them perfectly.',
        1 : f'<@{sender}> gently squeezes <@{reciever}>.',
        2 : f'<@{sender}> motivates everyone to cuddle <@{reciever}>.',
        3 : f'<@{sender}> pats <@{reciever}> lots and lots with both hands.',
        4 : f'<@{sender}> urges everyone to cuddle with <@{reciever}>.',
        5 : f'<@{sender}> creates a portal to the hug dimension, so they can cuddle <@{reciever}>.',
        6 : f'<@{sender}> hugs <@{reciever}> tightly drowning them in an ocean of love.'

    }
    
    number = randrange(len(messagedict))
    
    return messagedict.get(number)
    
client.run(token)   # run the bot
