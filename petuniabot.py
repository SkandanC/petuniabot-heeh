from random import randrange
import discord
from discord.ext import commands
import emoji
from discord_slash import SlashCommand
from matplotlib.pyplot import get

token = 'token'

client = discord.Client()
slash = SlashCommand(client, sync_commands=True)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game('Being cute and derpy'))
    print('Bot Ready')
    channel = client.get_channel(929854932650184747)
    await channel.send("bot ready")

@slash.slash(name="hug", description="give hugs!")
async def hug(ctx, member: discord.Member):

    sender = ctx.author.id
    reciever = member.id
    message = hugs(sender, reciever)
    await ctx.send(str(message))


def hugs(sender, reciever):
    
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
    
client.run(token)
