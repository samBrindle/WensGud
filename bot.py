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
time_regex = r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday): *(?:(?:([0|1]\d[0-5]\d|2[0-3][0-5]\d) *(?:-|,) *([0|1]\d[0-5]\d|2[0-3][0-5]\d))|(None))"

members = {}
events = {}
help_command = commands.DefaultHelpCommand(no_category="Commands")

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=help_command)

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


# ****UPDATED WITH OBJECT******
@bot.command(name='optin', help='This command enables users to be added to events.')
async def opt_in(ctx):

    if ctx.author.nick:
        response = f'{ctx.author.nick} has signed up for events!'
    else:
        response = f'{ctx.author.name} has signed up for events!'

    members[ctx.author] = Member(ctx.author.name, ctx.guild.id)

    await ctx.send(response)


@bot.command(name='optout', help='This command prevents users from being added to events.')
async def opt_out(ctx):
    if ctx.author.nick:
        response = f'{ctx.author.nick} has decided to opt out for events!'
    else:
        response = f'{ctx.author.name} has decided to opt out for events!'

    members.pop(ctx.author)

    await ctx.send(response)


@bot.command(name='freetime', help='This command allows a user to enter in their availability for the week. '
                                   'Please start each days availability with the day (Ex: Sunday-Saturday)'
                                   ' followed by the start time and end time in military time (Ex: 0800, 2200 would'
                                   ' be 8:00AM to 10:00PM)')
async def enter_availability(message):
    days_of_week = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
    user_availability = members[message.author].availability

    await message.channel.send(f'We hear you want to change your availability. Please enter the days you would like '
                               f'to change your availability on followed by the times you are available (ex. Tuesday: '
                               f'1000, 1400)')

    days = await bot.wait_for('message')
    user_input = helper_check(days.content)

    for input_day in user_input:
        for i, day in enumerate(days_of_week):
            if input_day[0].lower() == day:
                if input_day[1] != '':
                    user_availability[i] = [int(input_day[1]), int(input_day[2])]
                else:
                    user_availability[i] = [None]

    members[message.author].availability = user_availability

    await message.channel.send(f'{message.author.name} has updated their availability.')


def helper_check(message):
    return re.findall(time_regex, message)


@bot.command(name='showfreetime', help='This command will send a direct message to the user with their current '
                                       'availability for the week.')
async def show_free_time(message):
    await message.author.create_dm()
    await message.author.dm_channel.send(
        f'Hey {message.author.name}, your current availability for this week is: '
        f'Sunday: {members[message.author].availability[0]}, Monday: {members[message.author].availability[1]}, Tuesday:'
        f' {members[message.author].availability[2]}, Wednesday: {members[message.author].availability[3]}, Thursday:'
        f' {members[message.author].availability[4]}, Friday: {members[message.author].availability[5]}, Saturday:'
        f' {members[message.author].availability[6]}'
    )


@bot.command(name='create', help='This command allows a user to create a new event. Enter the event name as an argument'
                                 ' with the command (Ex: !create Movie Night). After the following command, the user '
                                 'will be prompted for a event description and an event duration. Event duration '
                                 'should be entered in military format (Ex. 200 would be 2 hours and 00 minutes)')
async def create_event(ctx):
    input_list = ctx.message.content.split()
    name = ' '.join(input_list[1:])
    await ctx.channel.send(f'Please enter a description for your event ->')
    description = await bot.wait_for('message')
    await ctx.channel.send(f'Please enter your event duration (240 would be 2 hours and 40 minutes ->')
    duration = await bot.wait_for('message')

    events[name] = Event(name, description.content, int(duration.content), ctx.guild.id)

    create_event_algorithm(events[name], members)

    if events[name].start_time:
        for key in members.keys():
            await key.create_dm()
            await key.dm_channel.send(
                f'Hey {members[key].name} you have been added to {events[name].name}! '
                f'This event will be happening on {events[name].day}, starting at {events[name].start_time}'
                f' and ending at {events[name].end_time}. Don\'t be late!'
            )
    else:
        await ctx.channel.send(f'Sorry {ctx.author.name}, the event you tried to create does not work with other '
                               f'member\'s schedules. Please try a different duration or get better friends.')
        del events[name]


# await create_scheduled_event(*, name, start_time, entity_type=..., privacy_level=..., channel=..., location=...,
#                              end_time=..., description=..., image=..., reason=None)¶


@bot.command(name='cancel', help='This command allows a user to cancel an event. Include event name.')
async def cancel_event(ctx):
    input_list = ctx.message.content.split()
    event_name = " ".join(input_list[1:])

    if event_name in events:
        del events[event_name]
        await ctx.channel.send(f'You have cancelled the {event_name} event.')
    else:
        await ctx.channel.send(f'Sorry, {event_name} is not a valid event in our logs.')


@bot.command(name='events', help='This command allows the user to view all scheduled events.')
async def check_event(ctx):
    if events:
        await ctx.channel.send(f'Here is a list of scheduled events:')
        for event in events:
            await ctx.channel.send(f'- {events[event].name} takes place on {events[event].day} from '
                                   f'{events[event].start_time } to {events[event].end_time}.')
    else:
        await ctx.channel.send(f'{ctx.guild.name} has no events on the schedule at the moment! Please use the '
                               f'!create command to create one.')


# @bot.command(name='join', help='This command allows a user to join an event. Include event name.')
# async def join_event(ctx):
#     input_list = ctx.message.content.split()
#     event_name = ' '.join(input_list[1:])
#     if event_name in events:
#         events[event_name][ctx.author] = members[ctx.author]
#         print(events)
#         await ctx.channel.send(f'{ctx.author.name} has joined {event_name}')
#     else:
#         await ctx.channel.send(f'Sorry, {event_name} is not a valid event in our logs.')
#
#
# @bot.command(name='leave', help='This command allows a user to leave an event. Include event name.')
# async def leave_event(ctx):
#     input_list = ctx.message.content.split()
#     event_name = ' '.join(input_list[1:])
#     if events[event_name]:
#         if ctx.author.name in events[event_name]:
#             events[event_name].pop(ctx.author.name)
#             await ctx.channel.send(f'{ctx.author.name} has left {event_name}')
#     else:
#         await ctx.channel.send(f'Sorry, {event_name} is not a valid event in our logs.')
#
#     print(events)

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
    def __init__(self, name, guild):
        self.name = name
        self.availability = [[None], [None], [None], [None], [None], [None], [None]]
        self.guild = guild


class Event:
    def __init__(self, name, description, duration, guild):
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
