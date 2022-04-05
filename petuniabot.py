from random import randrange
from requests import request
from datetime import datetime
import discord
from discord_slash import SlashCommand

token = 'token'   # bot token

# next 3 lines are needed to be able to log when members leave
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

slash = SlashCommand(client, sync_commands=True)

# delete logs
del_channel = []
del_user = []
del_time = []
del_message_logs = []
time = datetime.today()

@client.event
async def on_ready():

    """
    Prints bot status in the bot test server. Sets bot activity.
    """

    await client.change_presence(activity=discord.Game('Being cute and derpy'))
    print('Bot Ready')
    channel = client.get_channel(929854932650184747) # id is the id of the general channel in the bost test server
    await channel.send("bot ready")

@slash.slash(name="hug", description="give hugs!")
async def hug(ctx, member: discord.Member):

    """
    Prints randomized hug message by calling the hug() method.
    """

    sender = ctx.author.id
    reciever = member.id
    message = hugs(sender, reciever)
    await ctx.send(str(message))

@slash.slash(name="avatar", description="get avatar of a user")
async def avatar(ctx, member: discord.Member):

    """
    Prints avatar in an embed for specified user.
    """

    avurl = member.avatar_url    
    embed= discord.Embed(color=discord.Colour.green()) # set embed color
    embed.add_field(name='Avatar', value = f'<@{member.id}>') # 'naem' field is the embed title. 'value' field is the "description"
    embed.set_image(url=avurl) # attach avatar image url to embed
    await ctx.send(embed=embed)

@slash.slash(name="urbandictionary", description="urban dictionary definitions")
async def urbandictionary(ctx, expression = ""):

    """
    Prints the first urba dictionary definition for expression.
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
async def on_member_remove(member):

    """
    Prints a message in the general chat when someone leaves.
    """

    channel = client.get_channel(790638511254011937)
    await channel.send(f'{member} has left <:wahhh:790731210602053643>')

@client.event
async def on_message_delete(message: discord.message):

    """
    Logs deleted messages, channel name, user name, and message create time un lists. Pops the oldest message after 3 hrs of bot bootup.
    """

    del_channel.append(message.channel)
    del_user.append(message.author)
    del_time.append(message.created_at)
    del_message_logs.append(message.content)
    
    if divmod((datetime.today() - time).total_seconds(), 3600)[0] > 3:

        del_channel.pop(0)
        del_user.pop(0)
        del_time.pop(0)
        del_message_logs.pop(0)

@slash.slash(name="deleted-messages", description="deleted messages from past 3 hrs")
async def deleted(ctx):

    """
    Prints the deleted messages, channel name, user name and message creation time from the past 3 hrs.
    """
    
    message_list = []
    for key, _ in enumerate(del_message_logs):
        message_list.append(f" ```{del_user[key]} sent message in {del_channel[key]} at {del_time[key]}```: {del_message_logs[key]}\n")
    
    message = ''.join(map(str, message_list))
    await ctx.send(message)

@slash.slash(name="wordle", description="generates a game of wordle!")
async def wordle(ctx):

    """
    iterations a wordle game and calls the wordle generator.
    """
    
    won = 0 # logs whether the game is over

    iteration = 0 # logs whether the game iterationed
    
    guess = [['1', '2', '3', '4', '5']] # logs guesses stripped into individual letters
    
    wordlist = open('wordlist.txt').readlines() # read from file containing all possible correct words
    number = randrange(len(wordlist) + 1)   
    correct_word = list(wordlist[number][:-1])  # pick a random word
    print(correct_word)
    
    print_guesses = '' # logs the wordle square block thingy 

    playerid = ctx.author.id
    id = ctx.channel.id
    
    while won != 1:
        
        if iteration == 0:
            
            embed = discord.Embed(color=discord.Colour.green())
            embed.add_field(name='Wordle', value='Start making guesses!')
            await ctx.send(embed=embed)

        won, guess, print_guesses = await wordle_generator(ctx, id, guess, correct_word, print_guesses, playerid)
        
        iteration += 1

        if iteration == 6 and won == 0:
            embed = discord.Embed(color=discord.Colour.green())
            embed.add_field(name='Wordle', value=f'<@{ctx.author.id}> lost! \n{print_guesses}')
            await ctx.send(embed=embed)
        
        if won == 1:
            break          

async def wordle_generator(ctx, CHANNEL_ID, guess, correct_word, print_guesses, playerid):

    """
    Generates a game of wordle.
    """

    with open('validguesses.txt', 'r') as file:
        validguesses = file.read().replace('\n', '')    # read all possible valid guesses from a file
        
    msg = await client.wait_for(event="message")   # get word

    if msg.channel.id == CHANNEL_ID and msg.author.id == playerid:
        
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
            elif check_guess[key2] in correct_word and check_guess[key2] !=correct_word[key2]:
                string[key2] = '🟨'

        print_guesses = print_guesses + ''.join(square for square in string)

        print(check_guess)
        print(correct_word)

        # send messages with the block thingy
        if check_guess == correct_word:
            
            embed = discord.Embed(color=discord.Colour.green())
            embed.add_field(name='Wordle', value=f"<@{playerid}> won:\nThe word was: {''.join(letter for letter in correct_word)}\n{print_guesses}")
            await ctx.send(embed=embed)
            return 1, guess, print_guesses
        
        else:

            embed = discord.Embed(color=discord.Colour.green())
            embed.add_field(name='Wordle', value=f'<@{msg.author.id}> guessed:\n{print_guesses}')
            await ctx.send(embed=embed)
            return 0, guess, print_guesses

    else:
        return -1, guess, print_guesses
   

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
