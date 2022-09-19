import os
import random

from dotenv import load_dotenv
from discord.ext import commands
import discord

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    for guild in bot.guilds:
        if guild == GUILD:
            break

    for member in guild.members:
        print(member)


@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to our server!'
        f'If you would like to be a part of the server scheduling, please enter the'
        f'\"!signup\" command in the scheduling text channel'
    )


@bot.command(name='hello', help='Please help me :(')
async def hello(ctx):
    greetings = [
        'Hello',
        'Hola',
        'Greetings',
    ]

    response = random.choice(greetings)
    await ctx.send(response)



@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to our server!'
        f'If you would like to be a part of the server scheduling, please enter the'
        f'\"!signup\" command in the scheduling text channel'
    )

bot.run(TOKEN)
