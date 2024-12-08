"""
Internal functions for DriverNos Bot Operation, and related features.
"""

import sys
import json
import discord
import time
from . import permissions

# Module-wide globals
_config = {"file": None, "client": None}


def startClient(configfile="filename"):
    _config["file"] = configfile
    _config["client"] = discord.Client(intents=permissions.setIntents())

    return _config["client"]


# Return start string depending on prod or dev bot
def getCmd():
    name = _config["client"].user.name

    if name == "DriverNos":
        return "##"
    else:
        return "!!"


def readConfig():
    config = {}

    try:
        input_fh = open(_config["file"], "r")
        config = json.load(input_fh)

        # Convert JSON string keys to ints
        config = {int(k): v for k, v in config.items()}
    except IOError:
        print("open input file: " + _config["file"] + ", creating fresh data.")

    return config


def writeConfig(guilddata, gid):
    alldata = readConfig()
    alldata[gid] = guilddata[gid]  # N.B. added by reference

    # Test minimal output
    try:
        _ = json.dumps(alldata, separators=(",", ":"))
    except TypeError as err:
        sys.exit(f"Unable to write new config due to TypeError in guilddata: {err}")

    # Write config
    try:
        output_fh = open(_config["file"], "w")
    except IOError:
        sys.exit("Unable to open output file: " + _config["file"])

    json.dump(alldata, output_fh, separators=(",", ":"))

    return


def removeConfig(gid):
    alldata = readConfig()
    alldata.pop(gid)

    try:
        output_fh = open(_config["file"], "w")
    except IOError:
        sys.exit("Unable to open output file: " + _config["file"])

    # Minify output
    json.dump(alldata, output_fh, separators=(",", ":"))

    return


def formatDrivers(guilddata, guildid):
    template = ["", ""]

    for i in range(1, 10):
        template[0] += f"` {i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[0] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[0] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[0] += "\n"
    for i in range(10, 51):
        template[0] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[0] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[0] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[0] += "\n"
    for i in range(51, 100):
        template[1] += f"`{i}` - "
        if guildid in guilddata and str(i) in guilddata[guildid]["numbers"]:
            template[1] += f"<@{guilddata[guildid]['numbers'][str(i)]}>"
        else:
            template[1] += "\u2800" * 4 + "--" + "\u2800" * 4
        template[1] += "\n"

    return template


async def updateDrivers(guilddata, guildid):
    writeConfig(guilddata, guildid)

    # Record in records channel
    guild = _config["client"].get_guild(guildid)
    numchan = guild.get_channel(guilddata[guildid]["config"]["numchanid"])

    if numchan is None:
        return (
            "Unable to update records due to channel no longer existing. "
            "Use `## move new-channel-name` to set this channel for DriverNos use."
        )

    numbers = formatDrivers(guilddata, guildid)

    for i, msgid in enumerate(guilddata[guildid]["config"]["msg"]):
        msg = await numchan.fetch_message(msgid)
        await msg.edit(content=numbers[i])

    return


def gridEmbed(guilddata, guildid, channel):
    # Get Driver Nicknames
    nicks = getNicks(guildid)

    embed = discord.Embed(title=channel.name, color=discord.Color.gold())

    emoji = getEmojis()

    perrow = 0

    for team in guilddata[guildid]["grids"][str(channel.id)]["grid"]:
        temoji = str(emoji[team.lower().replace(" ", "")])
        drivers = [
            "\u2800" * 4 + "--" + "\u2800" * 4,
            "\u2800" * 4 + "--" + "\u2800" * 4,
        ]
        memberids = guilddata[guildid]["grids"][str(channel.id)]["grid"][team]

        for seat, memberid in enumerate(memberids):
            if memberid is not None:
                if memberid in nicks:
                    drivers[seat] = nicks[memberid].translate(str.maketrans("|", "/"))
                else:
                    drivers[seat] = (
                        f"`{getNumFromId(guilddata, guildid, memberid)} // <Unknown>`"
                    )

        embed.add_field(name=f"{temoji} {team}", value="\n".join(drivers), inline=True)
        perrow += 1
        # Empty field for 2 per lineguilddata[guildid]["numbers"]
        if perrow == 2:
            embed.add_field(name="\u200b", value="\u200b")
            perrow = 0

    return embed


async def updateEmbed(guilddata, guildid, channel):
    # Get message
    msg = await channel.fetch_message(
        guilddata[guildid]["grids"][str(channel.id)]["msg"]
    )

    await msg.edit(content=None, embed=gridEmbed(guilddata, guildid, channel))

    return


def getNumFromId(guilddata, guildid, memberid):
    # Return first driver number found for member id or None
    for num in guilddata[guildid]["numbers"]:
        if guilddata[guildid]["numbers"][num] == memberid:
            return num


def getEmojis():
    guild = _config["client"].get_guild(948129536808189962)

    temoji = {}

    emoji = guild.emojis

    for e in emoji:
        temoji[e.name] = e

    return temoji


def getEmoji(team):
    guild = _config["client"].get_guild(948129536808189962)

    name = team.lower().replace(" ", "")

    emoji = guild.emojis

    for e in emoji:
        if e.name == name:
            return e

    return ""


def getNicks(guildid):
    nicks = {}
    guild = _config["client"].get_guild(guildid)
    membs = guild.members
    for member in membs:
        if member.nick is not None:
            nicks[member.id] = member.nick
        else:
            nicks[member.id] = member.name

    return nicks


async def reapExpired(guilddata):
    for guildid in guilddata:
        guild = _config["client"].get_guild(guildid)

        if guilddata[guildid]["config"]["expiration"] >= 0:
            expires = []

            for driverno in guilddata[guildid]["expires"]:
                if int(time.time()) > guilddata[guildid]["expires"][driverno]:
                    # Prep allocation for removal
                    expires.append(driverno)

            # Check for any deleted members (https://github.com/discord/discord-api-docs/discussions/3274)
            # If id not in expired list, or members, it has been deleted.
            members = []
            for member in guild.members:
                members.append(member.id)

            for driverno in guilddata[guildid]["numbers"]:
                if guilddata[guildid]["numbers"][driverno] not in members:
                    if driverno not in guilddata[guildid]["expires"]:
                        expires.append(driverno)

            if len(expires) > 0:
                changedGrids = set()

                # Remove allocation
                for driverno in expires:
                    # Check if member is in any teams
                    memberid = guilddata[guildid]["numbers"][driverno]
                    for grid in guilddata[guildid]["grids"]:
                        for team in guilddata[guildid]["grids"][grid]["grid"]:
                            if (
                                memberid
                                in guilddata[guildid]["grids"][grid]["grid"][team]
                            ):
                                seat = guilddata[guildid]["grids"][grid]["grid"][
                                    team
                                ].index(memberid)
                                guilddata[guildid]["grids"][grid]["grid"][team][
                                    seat
                                ] = None
                                changedGrids.add(grid)

                    guilddata[guildid]["numbers"].pop(driverno)

                    if driverno in guilddata[guildid]["expires"]:
                        guilddata[guildid]["expires"].pop(driverno)

                # Update guild record
                await updateDrivers(guilddata, guildid)
                for grid in changedGrids:
                    await updateEmbed(guilddata, guildid, guild.get_channel(int(grid)))
