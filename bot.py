import os
import random
import re
from time import sleep
import datetime

from dotenv import load_dotenv
from discord.ext import commands
import discord

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
time_regex = r"([0|1]\d[0-5]\d|2[0-3][0-5]\d)"

members = {}
events = {}

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# **************************
# ******* BOT EVENTS *******
# **************************


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    for guild in bot.guilds:
        if guild == GUILD:
            break

    for member in guild.members:
        print(member)


# add help command, maybe include summary functionality
@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to our server!'
        f'If you would like to be a part of the server scheduling, please enter the'
        f'\"!signup\" command in the scheduling text channel'
    )

# *****************************
# ******* BOT COMMANDS ********
# *****************************


# - optin command
#     allows user to opt in to scheduling functionality
#     gives stock availablity?
# - optout commands
#     allow user to opt out if previously opted in
# - available command
#     takes in user availablilty for each day
#     (overrides original stock availablility)
# - create command
#     allows user to create an event
# - cancel commands
#     allows user to cancel event
# - join commands
#     allows you to join specified event
# - leave commands
#     allows you to leave specified event

# ****UPDATED WITH OBJECT******
@bot.command(name='optin', help='This command gives you the ability to join events.')
async def opt_in(ctx):

    if ctx.author.nick:
        response = f'{ctx.author.nick} has signed up for events!'
    else:
        response = f'{ctx.author.name} has signed up for events!'

    members[ctx.author] = Member(ctx.author.name, [])

    print(members)

    await ctx.send(response)


@bot.command(name='optout', help='This command allows')
async def opt_out(ctx):
    if ctx.author.nick:
        response = f'{ctx.author.nick} has decided to opt out for events!'
    else:
        response = f'{ctx.author.name} has decided to opt out for events!'

    members.pop(ctx.author)
    print(members)
    await ctx.send(response)


# ***** FIX ISSUE OF TIME STARTING WITH 0 OR 2 ***********
@bot.command(name='availability', help='This command allows you to enter in your typical availability')
async def enter_availability(message):
    days_of_week = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    user_availability = []
    await message.channel.send(f'For each days availability, please enter your available time range in a 24 hour format '
                               f'(Ex. 1545, 2330) or None if not available')

    for day in days_of_week:
        sleep(1)
        await message.channel.send(f'Enter your availability on {day} ->')
        msg = await bot.wait_for('message')
        split_message = helper_check(msg.content)

        if len(split_message) == 2:
            fixed_message = [int(split_message[0]), int(split_message[1])]
            user_availability.append(fixed_message)
        elif msg.content == "None":
            user_availability.append([None])
        else:
            await message.channel.send(f'Invalid Input! Your availability for {day} is now None '
                                       f'if you want to change this redo your !availability command!')
            user_availability.append([None])

    members[message.author].availability = user_availability
    print(members[message.author].availability)

    await message.channel.send(user_availability)


def helper_check(message):
    return re.findall(time_regex, message)


@bot.command(name='create', help='This command allows a user to create a new event.')
async def create_event(ctx):
    await ctx.channel.send(f'Please enter your event name ->')
    name = await bot.wait_for('message')
    await ctx.channel.send(f'Please enter a description for your event ->')
    description = await bot.wait_for('message')
    await ctx.channel.send(f'Please enter your event duration (2:40 would be 2 hours and 40 minutes ->')
    duration = await bot.wait_for('message')

    events[name.content] = Event(name.content, description.content, int(duration.content))

    print(events)

    create_event_algorithm(events[name.content], members)

    for key in members.keys():
        await key.create_dm()
        await key.dm_channel.send(
            f'Hey {members[key].name} you have been added to {events[name.content].name}! '
            f'This event will be happening on {events[name.content].day}, starting at {events[name.content].start_time}'
            f' and ending at {events[name.content].end_time}. Don\'t be late!'
        )


# await create_scheduled_event(*, name, start_time, entity_type=..., privacy_level=..., channel=..., location=...,
#                              end_time=..., description=..., image=..., reason=None)¶


@bot.command(name='cancel', help='This command allows a user to cancel an event. Inlcude event name.')
async def cancel_event(ctx):
    input_list = ctx.message.content.split()
    event_name = " ".join(input_list[1:])

    if event_name in events:
        del events[event_name]
        print(events)
        await ctx.channel.send(f'You have cancelled the {event_name} event.')
    else:
        await ctx.channel.send(f'Sorry, {event_name} is not a valid event in our logs.')


@bot.command(name='join', help='This command allows a user to join an event. Include event name.')
async def join_event(ctx):
    input_list = ctx.message.content.split()
    event_name = ' '.join(input_list[1:])
    if event_name in events:
        events[event_name][ctx.author] = members[ctx.author]
        print(events)
        await ctx.channel.send(f'{ctx.author.name} has joined {event_name}')
    else:
        await ctx.channel.send(f'Sorry, {event_name} is not a valid event in our logs.')


@bot.command(name='leave', help='This command allows a user to leave an event. Include event name.')
async def leave_event(ctx):
    input_list = ctx.message.content.split()
    event_name = ' '.join(input_list[1:])
    if events[event_name]:
        if ctx.author.name in events[event_name]:
            events[event_name].pop(ctx.author.name)
            await ctx.channel.send(f'{ctx.author.name} has left {event_name}')
    else:
        await ctx.channel.send(f'Sorry, {event_name} is not a valid event in our logs.')

    print(events)


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
    print(member)
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to our server!'
        f'If you would like to be a part of the server scheduling, please enter the'
        f'\"!optin\" command in the scheduling text channel'
    )

# **************************
# ****** BOT ALGORITHM *****
# **************************

# Create an object that contains
# members = list of user objects
# - user object
#     - guild
#     - availability
#     - user's name
# - event object
#     - guild
#     - event name
#     - description
#     - duration


class Member:
    def __init__(self, name, availability=[], guild=1020450611826806875):
        self.name = name
        self.availability = availability
        self.guild = guild


class Event:
    def __init__(self, name, description, duration, guild=1020450611826806875):
        self.name = name
        self.description = description
        self.duration = duration
        self.guild = guild
        self.start_time = None
        self.end_time = None
        self.day = None


def create_event_algorithm(ctx, members):
    # event = {
    #   'guild' : ctx.guild,
    #   'name' : ctx.name,
    #   'description' : ctx.description,
    #   'start' : 0,
    #   'end' : 0,
    # }
    _members = []

    for key in members.keys():
        if members[key].guild == ctx.guild:
            _members.append(members[key])
    # for member in members: ## TODO: USE SQL SEARCH TO GET GUILD MEMBERS IN BOT
    #     if member.guild == ctx.guild:
    #         _members.append(member)

    if not _members:
        return 'No active members'

    hours = _members[0].availability

    for i in range(1, len(_members)):
        for j, hour in enumerate(hours):
            if _members[i].availability[j][0] is None:
                hours[j] = [None]
                continue
            if hour[0] is None:
                continue
            if _members[i].availability[j][1] < hour[0]:
                hours[j] = [None]
            if _members[i].availability[j][0] > hour[1]:
                hours[j] = [None]
            if _members[i].availability[j][0] > hour[0]:
                hour[0] = _members[i].availability[j][0]
            if _members[i].availability[j][1] < hour[1]:
                hour[1] = _members[i].availability[j][1]

    week = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    for i, hour in enumerate(hours):
        if hour[0] is None:
            continue
        start = hour[0] % 100
        end = hour[1] % 100
        if (start + end) < 60:
            if hour[1] - hour[0] >= ctx.duration:
                # return f'{week[i]} from {hour[0]} to {hour[0] + ctx.duration}'
                ctx.start_time = hour[0]
                ctx.end_time = hour[0] + ctx.duration
                ctx.day = week[i]
                return
            if hour[1] - hour[0] < ctx.duration:
                continue
        if start > end:
            actual_time = (hour[1] - end) - (hour[0] - start) - (40+(start-end))
            if actual_time >= ctx.duration:
                # return f'{week[i]} from {hour[0]} to {hour[0] + ctx.duration}'
                ctx.start_time = hour[0]
                ctx.end_time = hour[0] + ctx.duration
                ctx.day = week[i]
                return
        if start <= end:
            actual_time = (hour[1] - end) - (hour[0] - start) + (end-start)
            if actual_time >= ctx.duration:
                # return f'{week[i]} from {hour[0]} to {hour[0] + ctx.duration}'
                ctx.start_time = hour[0]
                ctx.end_time = hour[0] + ctx.duration
                ctx.day = week[i]
                return
    return 'No times found'


bot.run(TOKEN)
