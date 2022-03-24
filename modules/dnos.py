'''
Internal functions for DriverNos Bot Operation, and related features.
'''
import sys
import json
import discord
import time
from . import permissions

# Module-wide globals
_config = {"file": None}


def startClient(configfile="filename"):
    _config["file"] = configfile
    return discord.Client(intents=permissions.setIntents())


def readConfig():
    try:
        input_fh = open(_config["file"], 'r')
    except IOError:
        sys.exit("Unable to open input file: " + _config["file"])

    config = json.load(input_fh)

    # Convert JSON string keys to ints
    config = {int(k): v for k, v in config.items()}

    return config


def writeConfig(gid, data):
    alldata = readConfig()
    alldata[gid] = data

    try:
        output_fh = open(_config["file"], 'w')
    except IOError:
        sys.exit("Unable to open output file: " + _config["file"])

    # Minify output
    json.dump(alldata, output_fh, separators=(',', ':'))

    return


def removeConfig(gid):
    alldata = readConfig()
    alldata.pop(gid)

    try:
        output_fh = open(_config["file"], 'w')
    except IOError:
        sys.exit("Unable to open output file: " + _config["file"])

    # Minify output
    json.dump(alldata, output_fh, separators=(',', ':'))

    return


def formatDrivers(guilddata, guild):
    template = ["", ""]
    for i in range(1, 10):
        template[0] += f"` {i}` - "
        if guild.id in guilddata and str(i) in guilddata[guild.id]["numbers"]:
            template[0] += f"<@{guilddata[guild.id]['numbers'][str(i)]}>"
        template[0] += "\n"
    for i in range(10, 50):
        template[0] += f"`{i}` - "
        if guild.id in guilddata and str(i) in guilddata[guild.id]["numbers"]:
            template[0] += f"<@{guilddata[guild.id]['numbers'][str(i)]}>"
        template[0] += "\n"
    for i in range(50, 100):
        template[1] += f"`{i}` - "
        if guild.id in guilddata and str(i) in guilddata[guild.id]["numbers"]:
            template[1] += f"<@{guilddata[guild.id]['numbers'][str(i)]}>"
        template[1] += "\n"

    return template


async def updateDrivers(guilddata, message):
    writeConfig(message.guild.id, guilddata[message.guild.id])

    # Record in records channel
    numchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    if numchan is None:
        await message.channel.send("Unable to update records due to channel no longer existing. " +
                                   "Use `##move new-channel-name` to set this channel for DriverNos use.")
        return

    numbers = formatDrivers(guilddata, message.guild)
    msg0 = await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg0"])
    msg1 = await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg1"])
    await msg0.edit(content=numbers[0])
    await msg1.edit(content=numbers[1])

    return


def reapExpired(guilddata):
    print("Reaping...")
    for guildid in guilddata:
        if guilddata[guildid]["config"]["expiration"] != 0:
            expires = []

            for driverno in guilddata[guildid]["expires"]:
                if int(time.time()) > guilddata[guildid]["expires"][driverno]:
                    # Prep allocation for removal
                    expires.append(driverno)

            # Remove allocation
            for driverno in expires:
                guilddata[guildid]["numbers"].pop(driverno)
                guilddata[guildid]["expires"].pop(driverno)

        # Write reaped config
        writeConfig(guildid, guilddata[guildid])
