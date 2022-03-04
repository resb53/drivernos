import discord
import os
from collections import defaultdict
import json
import sys
import re

'''
Discord DriverNos Bot.

This is for racing leagues to help manage assignment of driver numbers, and using these in user nicknames.

Functions:
##init:   Initialise the bot for this guild.
##assign: Assign a number to a member.
##move:   Move driver numbers listing to a new location.
##reset:  Reset and wipe all help data for this guild.
##help:   Help text for using this bot.
'''

client = discord.Client()


# Setup bot
def readConfig(jfile):
    try:
        input_fh = open(jfile, 'r')
    except IOError:
        sys.exit("Unable to open input file: " + jfile)

    config = json.load(input_fh)

    # Convert JSON string keys to ints
    config = {int(k): v for k, v in config.items()}

    return config


def writeConfig(jfile, gid, data):
    alldata = readConfig(jfile)
    alldata[gid] = data

    try:
        output_fh = open(jfile, 'w')
    except IOError:
        sys.exit("Unable to open output file: " + jfile)

    # Minify output
    json.dump(alldata, output_fh, separators=(',', ':'))


def formatDrivers(guilddata, guild):
    template = ["", ""]
    for i in range(1, 10):
        template[0] += f"` {i}` - "
        if guild.id in guilddata and i in guilddata[guild.id]["numbers"]:
            template[0] += f"<@{guilddata[guild.id][i]}>"
        template[0] += "\n"
    for i in range(10, 50):
        template[0] += f"`{i}` - "
        if guild.id in guilddata and i in guilddata[guild.id]["numbers"]:
            template[0] += f"<@{guilddata[guild.id][i]}>"
        template[0] += "\n"
    for i in range(50, 100):
        template[1] += f"`{i}` - "
        if guild.id in guilddata and i in guilddata[guild.id]["numbers"]:
            template[1] += f"<@{guilddata[guild.id][i]}>"
        template[1] += "\n"

    return template


# Globals
configfile = "data/guilddata.json"
gd = readConfig(configfile)


# Discord Events
@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Initialise bot in guild
    elif message.content.startswith("##init"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return

        if message.guild.id in gd:
            await message.channel.send("This guild has already been initialised. " +
                                       "To reset, use `.reset` and then run `##init` again.")
            return

        numchanname = message.content[7:].strip(" ")

        if len(numchanname) == 0:
            await message.channel.send("Provide a channel name to initialise. e.g: `##init numbers`")
            return

        textchannels = defaultdict(list)

        for tchans in message.guild.text_channels:
            textchannels[tchans.name].append(tchans.id)

        if numchanname not in textchannels:
            await message.channel.send(f"Text channel `{numchanname}` does not exist.")
            return
        elif len(textchannels[numchanname]) > 1:
            await message.channel.send(f"Multiple `{numchanname}` channels exist. Choose a unique channel name.")
            return

        numchan = message.guild.get_channel(textchannels[numchanname][0])

        # Print driver numbers to number channel
        dnos = formatDrivers(gd, message.guild)
        msg0 = await numchan.send(dnos[0])
        msg1 = await numchan.send(dnos[1])

        # (Re-)Initialise guild data
        gd[message.guild.id] = {}
        gd[message.guild.id]["numbers"] = {}
        gd[message.guild.id]["config"] = {
            "msg0": msg0.id,
            "msg1": msg1.id,
            "numchanid": numchan.id
        }
        writeConfig(configfile, message.guild.id, gd[message.guild.id])

        return

    # Assign a user a number
    elif message.content.startswith("##assign"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return

        m = re.match(r"^.assign\s+<@!(\d+)>\s+(\d+)", message.content)

        if m is not None:
            print(f"Assigning {m.group(1)} to number {m.group(2)}")
        else:
            await message.channel.send("Provide a tagged user and driver number. e.g: `##assign @DriverNos 1`")
            return

        member = message.guild.get_member(m.group(1))
        number = m.group(2)

        if member.bot:
            await message.channel.send("Unable to assign numbers to bots. Please tag a real user.")
            return

        print(f"Assigning {member} to {number}")


# Control nicknames when a nickname is changed. NOT WORKING
@client.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        for chan in before.guild.text_channels:
            if chan.name == "general":
                await chan.send(f"{before.nick} changed their nickname to {after.nick}")


client.run(os.getenv("TOKEN"))
