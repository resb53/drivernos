'''
Bot Operations for Discord Message actions.
'''
import discord
import re
from collections import defaultdict
from . import dnos, memaction

# Template grid for reuse
_gridtemplate = {
    "Alfa Romeo": [None, None],
    "Alpha Tauri": [None, None],
    "Alpine": [None, None],
    "Aston Martin": [None, None],
    "Ferrari": [None, None],
    "Haas": [None, None],
    "McLaren": [None, None],
    "Mercedes": [None, None],
    "Red Bull": [None, None],
    "Williams": [None, None]
}


async def _validateInit(guilddata, message, admin=False):
    if admin:
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return False

    if message.guild.id not in guilddata:
        await message.channel.send("This guild has not been initialised. " +
                                   "First run `##init <channel-name>`.")
        return False

    return True


async def init(guilddata, message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command can only be run by server admins.")
        return

    if message.guild.id in guilddata:
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
    numbers = dnos.formatDrivers(guilddata, message.guild)
    msg0 = await numchan.send(numbers[0])
    msg1 = await numchan.send(numbers[1])

    # Initialise guild data
    guilddata[message.guild.id] = {}
    guilddata[message.guild.id]["config"] = {
        "msg0": msg0.id,
        "msg1": msg1.id,
        "numchanid": numchan.id,
        "expiration": 1209600  # 2 weeks, use -1 for off, 0 for instant, else up to an hour minimum
    }
    guilddata[message.guild.id]["expires"] = {}
    guilddata[message.guild.id]["grids"] = {}
    guilddata[message.guild.id]["numbers"] = {}
    dnos.writeConfig(guilddata, message.guild.id)

    await message.channel.send(f"DriverNos has been initialised in <#{numchan.id}>.")

    return


def test(guilddata, message):
    teststring = message.content[7:].strip(" ")
    print(teststring)

    return


async def assign(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    m = re.match(r"^##assign\s+<@!?(\d+)>\s+(\d+)", message.content)

    if m is None:
        await message.channel.send("Provide a tagged user and driver number. e.g: `##assign @DriverNos 1`")
        return

    member = await message.guild.fetch_member(int(m.group(1)))
    number = m.group(2)

    if int(number) not in range(1, 100):
        await message.channel.send("Driver number must be between 1 and 99.")
        return

    if number in guilddata[message.guild.id]["numbers"]:
        await message.channel.send(f"Driver number `{number}` is already assigned to " +
                                   f"<@!{guilddata[message.guild.id]['numbers'][number]}>.")
        return

    if member is None:
        await message.channel.send(f"Unable to find member <@{m.group(1)}>")
        return

    if member.bot:
        await message.channel.send("Unable to assign numbers to bots. Please tag a real user.")
        return

    # Assign the number in guilddata
    if member.id not in guilddata[message.guild.id]["numbers"].values():
        guilddata[message.guild.id]["numbers"][number] = member.id
        report = f"Driver number `{number}` assigned to <@!{member.id}>."
    else:
        oldnum = "0"
        for x in guilddata[message.guild.id]["numbers"].items():
            if x[1] == member.id:
                oldnum = x[0]
        guilddata[message.guild.id]["numbers"].pop(oldnum)
        guilddata[message.guild.id]["numbers"][number] = member.id
        report = f"Driver number `{number}` assigned to <@{member.id}>, and number `{oldnum}` released."

    # Update number channel
    err = await dnos.updateDrivers(guilddata, message.guild.id)
    if err is not None:
        await message.channel.send(err)

    # Assign the number to the members nickname
    await memaction.setNick(guilddata, member, message=message)

    # Report success
    await message.channel.send(report)

    return


async def unassign(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    m = re.match(r"^##unassign\s+<@!?(\d+)>", message.content)

    if m is None:
        await message.channel.send("Provide a tagged user. e.g: `##unassign @DriverNos`")
        return

    member = await message.guild.fetch_member(int(m.group(1)))

    # Check if member has a number
    if member.id not in guilddata[message.guild.id]["numbers"].values():
        await message.channel.send(f"Member `<@!{member.id}` is not assigned to a Driver Number.")
        return

    # Unassign member from number
    number = 0
    for x in guilddata[message.guild.id]["numbers"].items():
        if x[1] == member.id:
            number = x[0]
    guilddata[message.guild.id]["numbers"].pop(number)

    # Update number channel
    err = await dnos.updateDrivers(guilddata, message.guild.id)
    if err is not None:
        await message.channel.send(err)

    # Unassign the number to the members nickname
    await memaction.setNick(guilddata, member, message=message)

    # Report success
    await message.channel.send(f"Member <@!{member.id}> unassigned from number `{number}`.")

    return


async def move(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    numchanname = message.content[7:].strip(" ")

    if len(numchanname) == 0:
        await message.channel.send("Provide a channel name to move number records to. e.g: `##init numbers`")
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

    newnumchan = message.guild.get_channel(textchannels[numchanname][0])
    oldnumchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    # Delete old numbers posts
    if oldnumchan is None:
        await message.channel.send("Unable to remove old DriverNos records due to channel no longer existing.")
    else:
        try:
            msgs = [
                await oldnumchan.fetch_message(guilddata[message.guild.id]["config"]["msg0"]),
                await oldnumchan.fetch_message(guilddata[message.guild.id]["config"]["msg1"])
            ]
            for msg in msgs:
                await msg.delete()
        except discord.errors.NotFound:
            await message.channel.send("Unable to remove DriverNos records due to messages no longer existing.")

    # Update guild data
    numbers = dnos.formatDrivers(guilddata, message.guild)
    msg0 = await newnumchan.send(numbers[0])
    msg1 = await newnumchan.send(numbers[1])
    guilddata[message.guild.id]["config"]["msg0"] = msg0.id
    guilddata[message.guild.id]["config"]["msg1"] = msg1.id
    guilddata[message.guild.id]["config"]["numchanid"] = newnumchan.id

    dnos.writeConfig(guilddata, message.guild.id)

    await message.channel.send(f"DriverNos records have been moved to <#{newnumchan.id}>.")

    return


async def setExpiry(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    m = re.match(r"^##expiry\s+(\-?\d+)", message.content)

    # Report current expiry if no time given.
    if m is None:
        await message.channel.send(f"Current expiry is {guilddata[message.guild.id]['config']['expiration']}.\n"
                                   "To change, provide a new value e.g: `##expiry 1209600`\n"
                                   "Use `0` for instant release, and `-1` for never release.")
        return

    guilddata[message.guild.id]["config"]["expiration"] = int(m.group(1))
    dnos.writeConfig(guilddata, message.guild.id)

    await message.channel.send(f"Expiry set to {m.group(1)}.")

    return


async def grid(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    gridchanname = message.content[6:].strip(" ")

    if len(gridchanname) == 0:
        await message.channel.send("Provide a channel name to setup grid. e.g: `##grid grid`")
        return

    textchannels = defaultdict(list)

    for tchans in message.guild.text_channels:
        textchannels[tchans.name].append(tchans.id)

    if gridchanname not in textchannels:
        await message.channel.send(f"Text channel `{gridchanname}` does not exist.")
        return
    elif len(textchannels[gridchanname]) > 1:
        await message.channel.send(f"Multiple `{gridchanname}` channels exist. Choose a unique channel name.")
        return

    gridchan = message.guild.get_channel(textchannels[gridchanname][0])

    # Print grid to grid channel
    gridmsg = await gridchan.send("Grid Channel Placeholder")

    # Initialise guild data
    guilddata[message.guild.id]["grids"][str(gridchan.id)] = {
        "grid": _gridtemplate.copy(),
        "msg": gridmsg.id
    }

    dnos.writeConfig(guilddata, message.guild.id)

    # Update to Embed
    await gridmsg.edit(
        content=None,
        embed=await dnos.gridEmbed(guilddata, message.guild.id, gridchan)
    )

    await message.channel.send(f"Grid has been initialised in <#{gridchan.id}>.")

    return


async def teamAdd(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    m = re.match(r"^##teamadd\s+([^<]+)\s+<@!?(\d+)>\s+<#(\d+)>", message.content)

    # Report usage if no match found.
    if m is None:
        await message.channel.send("Usage: `##teamadd teamname @username #gridchannel`")
        return

    teamname = m.group(1)
    member = await message.guild.fetch_member(int(m.group(2)))
    gridchan = message.guild.get_channel(int(m.group(3)))

    # Report if grid channel not initialised
    if str(gridchan.id) not in guilddata[message.guild.id]["grids"]:
        await message.channel.send(f"<#{gridchan.id}> has not been setup with a grid. Use `##grid` to initialise.")
        return

    # Report team list if no match found.
    if teamname not in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"]:
        teams = guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"].keys()
        teamlist = "`" + "`, `".join(sorted(teams)) + "`"
        await message.channel.send(f"Team `{teamname}` not found. Use one of:\n{teamlist}")
        return

    # Find first available seat
    seat = None

    for s, driver in enumerate(guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname]):
        if driver is None:
            seat = s

            break
        elif driver == member.id:
            await message.channel.send(f"<@{member.id}> already has a seat in "
                                       f"{await dnos.getEmoji(teamname)} **{teamname}**.")
            return

    if seat is None:
        await message.channel.send(f"No available seats in {await dnos.getEmoji(teamname)} **{teamname}**.\n"
                                   f"Use `##teamdel` to release a seat.")
        return

    # If seat available, and member is already in a seat, remove them first
    for oldteam in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"]:
        if member.id in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][oldteam]:
            oldseat = guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][oldteam].index(member.id)
            guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][oldteam][oldseat] = None

    # Assign seat
    guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat] = member.id
    dnos.writeConfig(guilddata, message.guild.id)

    # Update Embed
    gridmsg = await gridchan.fetch_message(guilddata[message.guild.id]["grids"][str(gridchan.id)]["msg"])

    await gridmsg.edit(
        content=None,
        embed=await dnos.gridEmbed(guilddata, message.guild.id, gridchan)
    )

    await message.channel.send(f"<@{member.id}> has been assigned seat {seat + 1} "
                               f"in {await dnos.getEmoji(teamname)} **{teamname}** of grid <#{gridchan.id}>.")

    return


async def teamDel(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    m = re.match(r"^##teamdel\s+([^<]+)\s+([12])\s+<#(\d+)>", message.content)

    # Report usage if no match found.
    if m is None:
        await message.channel.send("Usage: `##teamdel teamname seatnum(1,2) #gridchannel`")
        return

    teamname = m.group(1)
    seat = int(m.group(2)) - 1
    gridchan = message.guild.get_channel(int(m.group(3)))

    # Report if grid channel not initialised
    if str(gridchan.id) not in guilddata[message.guild.id]["grids"]:
        await message.channel.send(f"<#{gridchan.id}> has not been setup with a grid. Use `##grid` to initialise.")
        return

    # Report team list if no match found.
    if teamname not in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"]:
        teams = guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"].keys()
        teamlist = "`" + "`, `".join(sorted(teams)) + "`"
        await message.channel.send(f"Team `{teamname}` not found. Use one of:\n{teamlist}")
        return

    # If seat assigned, remove the driver, else report no change.
    if guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat] is None:
        await message.channel.send(f"Seat {seat + 1} in {await dnos.getEmoji(teamname)} **{teamname}**"
                                   " is already empty.")
        return

    member = await message.guild.fetch_member(
        guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat]
    )
    guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat] = None
    dnos.writeConfig(guilddata, message.guild.id)

    # Update Embed
    gridmsg = await gridchan.fetch_message(guilddata[message.guild.id]["grids"][str(gridchan.id)]["msg"])

    await gridmsg.edit(
        content=None,
        embed=await dnos.gridEmbed(guilddata, message.guild.id, gridchan)
    )

    await message.channel.send(f"<@{member.id}> has been removed from seat {seat + 1} "
                               f"in {await dnos.getEmoji(teamname)} **{teamname}** of grid <#{gridchan.id}>.")

    return


async def reset(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    if message.content != "##reset Everything":
        await message.channel.send("**This will delete ALL drivernos data and is irreversible.**\n"
                                   "If you are sure you would like to proceed, "
                                   "use this exact command: `##reset Everything`")
        return

    # Remove drivernos from server and cached data
    numchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    if numchan is None:
        await message.channel.send("Unable to remove DriverNos records due to channel no longer existing.")
    else:
        try:
            msgs = [
                await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg0"]),
                await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg1"])
            ]
            for msg in msgs:
                await msg.delete()
        except discord.errors.NotFound:
            await message.channel.send("Unable to remove DriverNos records due to messages no longer existing.")

    for gridchan in message.guild.get_channel(guilddata[message.guild.id]["grids"]):
        if gridchan is None:
            await message.channel.send("Unable to remove DriverNos grid due to channel no longer existing.")
        else:
            try:
                msg = await gridchan.fetch_message(guilddata[message.guild.id]["grids"][str(gridchan.id)]["msg"]),
                await msg.delete()
            except discord.errors.NotFound:
                await message.channel.send("Unable to remove DriverNos grid due to messages no longer existing.")

    dnos.removeConfig(message.guild.id)
    guilddata.pop(message.guild.id)

    await message.channel.send("DriverNos has been reset.")

    return
