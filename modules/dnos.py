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
    template = ["", "", ""]
    for i in range(1, 10):
        template[0] += f"` {i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[0] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[0] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[0] += "\n"
    for i in range(10, 34):
        template[0] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[0] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[0] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[0] += "\n"
    for i in range(34, 67):
        template[1] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[1] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[1] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[1] += "\n"
    for i in range(67, 100):
        template[2] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[2] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[2] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[2] += "\n"

    return template


async def updateDrivers(guilddata, guildid):
    writeConfig(guilddata, guildid)

    # Record in records channel
    guild = _config["client"].get_guild(guildid)
    numchan = guild.get_channel(guilddata[guildid]["config"]["numchanid"])

    if numchan is None:
        return ("Unable to update records due to channel no longer existing. "
                "Use `## move new-channel-name` to set this channel for DriverNos use.")

    embed = discord.Embed(
        title="Driver Numbers",
        color=discord.Color.gold()
    )

    numbers = formatDrivers(guilddata, guildid)

    embed.add_field(
        name="\u200b",
        value=numbers[0],
        inline=True
    )
    embed.add_field(
        name="\u200b",
        value=numbers[1],
        inline=True
    )
    embed.add_field(
        name="\u200b",
        value=numbers[2],
        inline=True
    )

    msg = await numchan.fetch_message(guilddata[guildid]["config"]["msg"])
    await msg.edit(content="", embed=embed)

    return


async def gridEmbed(guilddata, guildid, channel):
    embed = discord.Embed(
        title=channel.name,
        color=discord.Color.gold()
    )

    emoji = await getEmojis()

    perrow = 0

    for team in guilddata[guildid]["grids"][str(channel.id)]["grid"]:
        temoji = str(emoji[team.lower().replace(" ", "")])
        d1 = "\u2800" * 4 + "--" + "\u2800" * 4
        d2 = "\u2800" * 4 + "--" + "\u2800" * 4

        if guilddata[guildid]["grids"][str(channel.id)]["grid"][team][0] is not None:
            d1 = "<@" + str(guilddata[guildid]["grids"][str(channel.id)]["grid"][team][0]) + ">"

        if guilddata[guildid]["grids"][str(channel.id)]["grid"][team][1] is not None:
            d2 = "<@" + str(guilddata[guildid]["grids"][str(channel.id)]["grid"][team][1]) + ">"

        embed.add_field(
            name=f"{temoji} {team}",
            value=f"{d1}\n{d2}",
            inline=True
        )
        perrow += 1
        # Empty field for 2 per line
        if perrow == 2:
            embed.add_field(name="\u200b", value="\u200b")
            perrow = 0

    return embed


async def updateEmbed(guilddata, guildid, channel):
    # Get message
    msg = await channel.fetch_message(guilddata[guildid]["grids"][str(channel.id)]["msg"])

    await msg.edit(
        content=None,
        embed=await gridEmbed(guilddata, guildid, channel)
    )

    return


async def getEmojis():
    guild = _config["client"].get_guild(948129536808189962)

    temoji = {}

    emoji = await guild.fetch_emojis()

    for e in emoji:
        temoji[e.name] = e

    return temoji


async def getEmoji(team):
    guild = _config["client"].get_guild(948129536808189962)

    name = team.lower().replace(" ", "")

    emoji = await guild.fetch_emojis()

    for e in emoji:
        if e.name == name:
            return e

    return ""


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
