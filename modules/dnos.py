'''
Internal functions for DriverNos Bot Operation, and related features.
'''
import sys
import json
import discord
import time
from . import permissions

# Module-wide globals
_config = {
    "file": None,
    "client": None
}


def startClient(configfile="filename"):
    _config["file"] = configfile
    _config["client"] = discord.Client(intents=permissions.setIntents())

    return _config["client"]


def readConfig():
    try:
        input_fh = open(_config["file"], 'r')
    except IOError:
        sys.exit("Unable to open input file: " + _config["file"])

    config = json.load(input_fh)

    # Convert JSON string keys to ints
    config = {int(k): v for k, v in config.items()}

    return config


def writeConfig(guilddata, gid):
    alldata = readConfig()
    alldata[gid] = guilddata[gid]  # N.B. added by reference

    # Test minimal output
    try:
        _ = json.dumps(alldata, separators=(',', ':'))
    except TypeError as err:
        sys.exit(f"Unable to write new config due to TypeError in guilddata: {err}")

    # Write config
    try:
        output_fh = open(_config["file"], 'w')
    except IOError:
        sys.exit("Unable to open output file: " + _config["file"])

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


def formatDrivers(guilddata, guildid):
    template = ["", ""]
    for i in range(1, 10):
        template[0] += f"` {i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[0] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        template[0] += "\n"
    for i in range(10, 50):
        template[0] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[0] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        template[0] += "\n"
    for i in range(50, 100):
        template[1] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[1] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        template[1] += "\n"

    return template


async def updateDrivers(guilddata, guildid):
    writeConfig(guilddata, guildid)

    # Record in records channel
    guild = _config["client"].get_guild(guildid)
    numchan = guild.get_channel(guilddata[guildid]["config"]["numchanid"])

    if numchan is None:
        return ("Unable to update records due to channel no longer existing. "
                "Use `##move new-channel-name` to set this channel for DriverNos use.")

    numbers = formatDrivers(guilddata, guildid)
    msg0 = await numchan.fetch_message(guilddata[guildid]["config"]["msg0"])
    msg1 = await numchan.fetch_message(guilddata[guildid]["config"]["msg1"])
    await msg0.edit(content=numbers[0])
    await msg1.edit(content=numbers[1])

    return


def gridEmbed(guilddata, guildid, channel):
    embed = discord.Embed(
        title=channel.name,
        color=discord.Color.gold()
    )

    perrow = 0

    for team in guilddata[guildid]["grids"][str(channel.id)]["grid"]:
        embed.add_field(
            name=team,
            value="Driver1\nDriver2",
            inline=True
        )
        perrow += 1
        # Empty field for 2 per line
        if perrow == 2:
            embed.add_field(name='\u200b', value='\u200b')
            perrow = 0

    return embed


async def reapExpired(guilddata):
    for guildid in guilddata:
        if guilddata[guildid]["config"]["expiration"] > 0:
            expires = []

            for driverno in guilddata[guildid]["expires"]:
                if int(time.time()) > guilddata[guildid]["expires"][driverno]:
                    # Prep allocation for removal
                    expires.append(driverno)

            if len(expires) > 0:
                # Remove allocation
                for driverno in expires:
                    guilddata[guildid]["numbers"].pop(driverno)
                    guilddata[guildid]["expires"].pop(driverno)

                # Update guild record
                await updateDrivers(guilddata, guildid)

        # Write reaped config
        writeConfig(guilddata, guildid)
