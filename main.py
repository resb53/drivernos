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

intents = discord.Intents.default()
intents.members = True
intents.messages = True
client = discord.Client(intents=intents)
configfile = "data/guilddata.json"


# Setup bot
def readConfig():
    try:
        input_fh = open(configfile, 'r')
    except IOError:
        sys.exit("Unable to open input file: " + configfile)

    config = json.load(input_fh)

    # Convert JSON string keys to ints
    config = {int(k): v for k, v in config.items()}

    return config


def writeConfig(gid, data):
    alldata = readConfig()
    alldata[gid] = data

    try:
        output_fh = open(configfile, 'w')
    except IOError:
        sys.exit("Unable to open output file: " + configfile)

    # Minify output
    json.dump(alldata, output_fh, separators=(',', ':'))


def removeConfig(gid):
    alldata = readConfig()
    alldata.pop(gid)

    try:
        output_fh = open(configfile, 'w')
    except IOError:
        sys.exit("Unable to open output file: " + configfile)

    # Minify output
    json.dump(alldata, output_fh, separators=(',', ':'))


def formatDrivers(guilddata, guild):
    template = ["", ""]
    for i in range(1, 10):
        template[0] += f"` {i}` - "
        if guild.id in guilddata and i in guilddata[guild.id]["numbers"]:
            template[0] += f"<@{guilddata[guild.id]['numbers'][i]}>"
        template[0] += "\n"
    for i in range(10, 50):
        template[0] += f"`{i}` - "
        if guild.id in guilddata and i in guilddata[guild.id]["numbers"]:
            template[0] += f"<@{guilddata[guild.id]['numbers'][i]}>"
        template[0] += "\n"
    for i in range(50, 100):
        template[1] += f"`{i}` - "
        if guild.id in guilddata and i in guilddata[guild.id]["numbers"]:
            template[1] += f"<@{guilddata[guild.id]['numbers'][i]}>"
        template[1] += "\n"

    return template


# Globals
gd = readConfig()


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
                                       "To reset, use `##reset` and then run `##init` again.")
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

        # Initialise guild data
        gd[message.guild.id] = {}
        gd[message.guild.id]["numbers"] = {}
        gd[message.guild.id]["config"] = {
            "msg0": msg0.id,
            "msg1": msg1.id,
            "numchanid": numchan.id
        }
        writeConfig(message.guild.id, gd[message.guild.id])

        await message.channel.send("DriverNos has been initialised in.")

        return

    elif message.content.startswith("##test"):
        teststring = message.content[7:].strip(" ")
        print(teststring)

    # Assign a user a number
    elif message.content.startswith("##assign"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return

        m = re.match(r"^##assign\s+<@!?(\d+)>\s+(\d+)", message.content)

        if m is None:
            await message.channel.send("Provide a tagged user and driver number. e.g: `##assign @DriverNos 1`")
            return

        member = await message.guild.fetch_member(int(m.group(1)))
        number = int(m.group(2))

        if number not in range(1, 100):
            await message.channel.send("Driver number must be between 1 and 99.")
            return

        if member is None:
            await message.channel.send(f"Unable to find member <@{int(m.group(1))}>")
            return

        if member.bot:
            await message.channel.send("Unable to assign numbers to bots. Please tag a real user.")
            return

        # Assign the number in gd
        report = ""

        if member.id not in gd[message.guild.id]["numbers"].values():
            gd[message.guild.id]["numbers"][number] = member.id
            report = f"Driver number `{number}` assigned to <@!{member.id}>."
        else:
            oldnum = 0
            for x in gd[message.guild.id]["numbers"].items():
                if x[1] == member.id:
                    oldnum = x[0]
            gd[message.guild.id]["numbers"].pop(oldnum)
            gd[message.guild.id]["numbers"][number] = member.id
            report = f"Driver number `{number}` assigned to <@{member.id}>, and number `{oldnum}` released."

        # Update number channel
        numchan = message.guild.get_channel(gd[message.guild.id]["config"]["numchanid"])
        dnos = formatDrivers(gd, message.guild)
        msg0 = await numchan.fetch_message(gd[message.guild.id]["config"]["msg0"])
        msg1 = await numchan.fetch_message(gd[message.guild.id]["config"]["msg1"])
        await msg0.edit(content=dnos[0])
        await msg1.edit(content=dnos[1])

        # Report success
        writeConfig(message.guild.id, gd[message.guild.id])
        await message.channel.send(report)

        return

    # Reset drivernos for the guild
    elif message.content.startswith("##reset"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return

        # TODO: For production CHECK THIS IS REALLY WANTED!

        if message.guild.id not in gd:
            await message.channel.send("Unable to reset DriverNos. It has not yet been initialised in this guild.")
            return

        # Remove drivernos from server and cached data
        numchan = message.guild.get_channel(gd[message.guild.id]["config"]["numchanid"])

        if numchan is None:
            # TODO: Handle this better
            print("Error: config out of sync")
            return

        msgs = [
            await numchan.fetch_message(gd[message.guild.id]["config"]["msg0"]),
            await numchan.fetch_message(gd[message.guild.id]["config"]["msg1"])
        ]

        for msg in msgs:
            await msg.delete()

        removeConfig(message.guild.id)
        gd.pop(message.guild.id)

        await message.channel.send("DriverNos has been reset.")

        return


# Control nicknames when a nickname is changed. NOT WORKING
@client.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        name = ""

        if after.nick is None:
            name = after.name
        else:
            name = after.nick

        # If user has a driver number, prepend this to their chosen name
        number = None

        if after.id not in gd[after.guild.id]["numbers"].values():
            return
        else:
            for n, id in gd[after.guild.id]["numbers"].items():
                if id == after.id:
                    number = n

        print(f"Driver number {number} changed their name to {name}.")


client.run(os.getenv("TOKEN"))
