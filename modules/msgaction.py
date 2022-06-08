'''
Bot Operations for Discord Message actions.
'''
import discord
import re
import string
from . import dnos, memaction


async def _validateInit(guilddata, message, admin=False):
    if admin:
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return False

    if message.guild.id not in guilddata:
        await message.channel.send("This guild has not been initialised. " +
                                   "First run `## init #channel`.")
        return False

    return True


async def init(guilddata, message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command can only be run by server admins.")
        return

    if message.guild.id in guilddata:
        await message.channel.send("This guild has already been initialised. " +
                                   "To reset, use `## reset` and then run `## init` again.")
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" init\s+<#(\d+)>", message.content)

    if m is None:
        await message.channel.send("Provide a channel name to initialise. e.g: `## init #channel`")
        return

    numchan = message.guild.get_channel(int(m.group(1)))

    # Print driver numbers to number channel
    msg1 = await numchan.send("Number Channel Placeholder 1")
    msg2 = await numchan.send("Number Channel Placeholder 2")

    # Initialise guild data
    guilddata[message.guild.id] = {}
    guilddata[message.guild.id]["config"] = {
        "msg": [msg1.id, msg2.id],
        "numchanid": numchan.id,
        "expiration": 1209600  # 2 weeks, use -1 for off, 0 for instant, else up to an hour minimum
    }
    guilddata[message.guild.id]["expires"] = {}
    guilddata[message.guild.id]["grids"] = {}
    guilddata[message.guild.id]["numbers"] = {}

    await dnos.updateDrivers(guilddata, message.guild.id)

    await message.channel.send(f"DriverNos has been initialised in <#{numchan.id}>.")

    return


async def migrate(guilddata, message):
    # Remove old single message
    numchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    msgid = guilddata[message.guild.id]["config"]["msg"]

    if type(msgid) is not int:
        await message.channel.send("Drivernos has already migrated this guild to new format.")
        return

    try:
        m = await numchan.fetch_message(msgid)
        await m.delete()
    except discord.errors.NotFound:
        await message.channel.send("Unable to remove DriverNos records due to message no longer existing.")

    # Create new formatted messages
    msg1 = await numchan.send("Number Channel Placeholder 1")
    msg2 = await numchan.send("Number Channel Placeholder 2")
    guilddata[message.guild.id]["config"]["msg"] = [msg1.id, msg2.id]

    await dnos.updateDrivers(guilddata, message.guild.id)

    await message.channel.send(f"DriverNos has migrated to the new number format in <#{numchan.id}>.")

    return


async def assign(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" assign\s+<@!?(\d+)>\s+(\d+)", message.content)

    if m is None:
        await message.channel.send("Provide a tagged user and driver number. e.g: `## assign @DriverNos 1`")
        return

    member = message.guild.get_member(int(m.group(1)))
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

        # Update grid if driver was in one
        for grid in guilddata[message.guild.id]["grids"]:
            for team in guilddata[message.guild.id]["grids"][grid]["grid"]:
                if member.id in guilddata[message.guild.id]["grids"][grid]["grid"][team]:
                    await dnos.updateEmbed(guilddata, message.guild.id, message.guild.get_channel(int(grid)))
                    break

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

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" unassign\s+<@!?(\d+)>", message.content)

    if m is None:
        await message.channel.send("Provide a tagged user. e.g: `## unassign @DriverNos`")
        return

    member = message.guild.get_member(int(m.group(1)))

    # Check if member has a number
    if member.id not in guilddata[message.guild.id]["numbers"].values():
        await message.channel.send(f"Member <@!{member.id} is not assigned to a Driver Number.")
        return

    # Unassign member from number
    number = 0
    for x in guilddata[message.guild.id]["numbers"].items():
        if x[1] == member.id:
            number = x[0]
    guilddata[message.guild.id]["numbers"].pop(number)

    # Check if member is in any teams
    changedGrids = set()

    for grid in guilddata[message.guild.id]["grids"]:
        for team in guilddata[message.guild.id]["grids"][grid]["grid"]:
            if member.id in guilddata[message.guild.id]["grids"][grid]["grid"][team]:
                seat = guilddata[message.guild.id]["grids"][grid]["grid"][team].index(member.id)
                guilddata[message.guild.id]["grids"][grid]["grid"][team][seat] = None
                await message.channel.send(f"Removing <@!{member.id}> from seat {seat + 1} in "
                                           f"{dnos.getEmoji(team)} **{team}** of grid <#{grid}>.")
                changedGrids.add(grid)

    for grid in changedGrids:
        await dnos.updateEmbed(guilddata, message.guild.id, message.guild.get_channel(int(grid)))

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

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" move\s+<#(\d+)>", message.content)

    if m is None:
        await message.channel.send("Provide a channel name to move records to. e.g: `## move #newchannel`")
        return

    newnumchan = message.guild.get_channel(int(m.group(1)))
    oldnumchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    # Delete old numbers posts
    if oldnumchan is None:
        await message.channel.send("Unable to remove old DriverNos records due to channel no longer existing.")
    else:
        try:
            for msgid in guilddata[message.guild.id]["config"]["msg"]:
                msg = await oldnumchan.fetch_message(msgid)
                await msg.delete()
        except discord.errors.NotFound:
            await message.channel.send("Unable to remove DriverNos records due to messages no longer existing.")

    # Print driver numbers to number channel
    msg1 = await newnumchan.send("Number Channel Placeholder 1")
    msg2 = await newnumchan.send("Number Channel Placeholder 2")

    # Update guild data
    guilddata[message.guild.id]["config"]["msg"] = [msg1.id, msg2.id]
    guilddata[message.guild.id]["config"]["numchanid"] = newnumchan.id

    await dnos.updateDrivers(guilddata, message.guild.id)

    await message.channel.send(f"DriverNos records have been moved to <#{newnumchan.id}>.")

    return


async def setExpiry(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" expiry\s+(\-?\d+)", message.content)

    # Report current expiry if no time given.
    if m is None:
        await message.channel.send(f"Current expiry is {guilddata[message.guild.id]['config']['expiration']}.\n"
                                   "To change, provide a new value e.g: `## expiry 1209600`\n"
                                   "Use `-1` to never release.")
        return

    guilddata[message.guild.id]["config"]["expiration"] = int(m.group(1))
    dnos.writeConfig(guilddata, message.guild.id)

    await message.channel.send(f"Expiry set to {m.group(1)}.")

    return


def gridTemplate():
    return {
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


async def grid(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    gridchanname = message.content[6:].strip(" ")

    if len(gridchanname) == 0:
        await message.channel.send("Provide a channel name to setup grid. e.g: `## grid #gridchannel`")
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" grid\s+<#(\d+)>", message.content)

    if m is None:
        await message.channel.send("Provide a channel name to initialise. e.g: `## grid #gridchannel`")
        return

    gridchan = message.guild.get_channel(int(m.group(1)))

    # Print grid to grid channel
    gridmsg = await gridchan.send("Grid Channel Placeholder")

    # Initialise guild data
    guilddata[message.guild.id]["grids"][str(gridchan.id)] = {
        "grid": gridTemplate(),
        "msg": gridmsg.id
    }

    dnos.writeConfig(guilddata, message.guild.id)

    # Update Embed
    await dnos.updateEmbed(guilddata, message.guild.id, gridchan)

    await message.channel.send(f"Grid has been initialised in <#{gridchan.id}>.")

    return


async def teamAdd(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" teamadd\s+([^<]+)\s+<@!?(\d+)>\s+<#(\d+)>", message.content)

    # Report usage if no match found.
    if m is None:
        await message.channel.send("Usage: `## teamadd teamname @username #gridchannel`")
        return

    teamname = string.capwords(m.group(1))
    if teamname == "Mclaren":
        teamname = "McLaren"
    member = message.guild.get_member(int(m.group(2)))
    gridchan = message.guild.get_channel(int(m.group(3)))

    # Report if member not assigned a number
    if member.id not in guilddata[message.guild.id]["numbers"].values():
        await message.channel.send(f"<@{member.id}> has not been assigned a driver number. "
                                   "Use `## assign` to assign them one.")
        return

    # Report if grid channel not initialised
    if str(gridchan.id) not in guilddata[message.guild.id]["grids"]:
        await message.channel.send(f"<#{gridchan.id}> has not been setup with a grid. Use `## grid` to initialise.")
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
                                       f"{dnos.getEmoji(teamname)} **{teamname}**.")
            return

    if seat is None:
        await message.channel.send(f"No available seats in {dnos.getEmoji(teamname)} **{teamname}**.\n"
                                   f"Use `## teamdel` to release a seat.")
        return

    # If seat available, and member is already in a seat, remove them first
    for oldteam in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"]:
        if member.id in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][oldteam]:
            oldseat = guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][oldteam].index(member.id)
            guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][oldteam][oldseat] = None
            await message.channel.send(f"<@{member.id}> has moved from seat {oldseat + 1} "
                                       f"in {dnos.getEmoji(oldteam)} **{oldteam}** of grid <#{gridchan.id}>.")

    # Assign seat
    guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat] = member.id
    dnos.writeConfig(guilddata, message.guild.id)

    # Update Embed
    await dnos.updateEmbed(guilddata, message.guild.id, gridchan)

    await message.channel.send(f"<@{member.id}> has been assigned seat {seat + 1} "
                               f"in {dnos.getEmoji(teamname)} **{teamname}** of grid <#{gridchan.id}>.")

    return


async def teamDel(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" teamdel\s+([^<]+)\s+([12])\s+<#(\d+)>", message.content)

    # Report usage if no match found.
    if m is None:
        await message.channel.send("Usage: `## teamdel teamname seatnum(1,2) #gridchannel`")
        return

    teamname = string.capwords(m.group(1))
    if teamname == "Mclaren":
        teamname = "McLaren"
    seat = int(m.group(2)) - 1
    gridchan = message.guild.get_channel(int(m.group(3)))

    # Report if grid channel not initialised
    if str(gridchan.id) not in guilddata[message.guild.id]["grids"]:
        await message.channel.send(f"<#{gridchan.id}> has not been setup with a grid. Use `## grid` to initialise.")
        return

    # Report team list if no match found.
    if teamname not in guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"]:
        teams = guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"].keys()
        teamlist = "`" + "`, `".join(sorted(teams)) + "`"
        await message.channel.send(f"Team `{teamname}` not found. Use one of:\n{teamlist}")
        return

    # If seat assigned, remove the driver, else report no change.
    if guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat] is None:
        await message.channel.send(f"Seat {seat + 1} in {dnos.getEmoji(teamname)} **{teamname}**"
                                   " is already empty.")
        return

    memberid = guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat]
    member = message.guild.get_member(memberid)

    if member is not None:
        member = f"<@{member.id}>"
    else:
        member = f"`{dnos.getNumFromId(guilddata, message.guild.id, memberid)} || <Unknown>`"

    guilddata[message.guild.id]["grids"][str(gridchan.id)]["grid"][teamname][seat] = None
    dnos.writeConfig(guilddata, message.guild.id)

    # Update Embed
    await dnos.updateEmbed(guilddata, message.guild.id, gridchan)

    await message.channel.send(f"{member} has been removed from seat {seat + 1} "
                               f"in {dnos.getEmoji(teamname)} **{teamname}** of grid <#{gridchan.id}>.")

    return


async def reset(guilddata, message):
    if not await _validateInit(guilddata, message, admin=True):
        return

    cmd = dnos.getCmd()
    m = re.match("^" + cmd + r" reset (Everything|<#\d+>)$", message.content)

    if m is None:
        await message.channel.send(
            "Reset options:\n"
            "`## reset Everything`: **This will delete ALL drivernos data and is irreversible.**\n"
            "`## reset #gridchannel`: This will remove a grid from existence and is irreversible."
        )
        return

    mg = re.match(r"^<#(\d+)>$", m.group(1))

    if mg is not None:
        # Remove specified grid only.
        if mg.group(1) not in guilddata[message.guild.id]["grids"]:
            await message.channel.send(f"<#{mg.group(1)}> is not an initialised grid channel and cannot be reset.")
            return

        # Get specified channel
        gridchan = message.guild.get_channel(int(mg.group(1)))

        # Remove message and record in guilddata
        gridmsg = await gridchan.fetch_message(guilddata[message.guild.id]["grids"][str(gridchan.id)]["msg"])
        await gridmsg.delete()

        guilddata[message.guild.id]["grids"].pop(str(gridchan.id))

        dnos.writeConfig(guilddata, message.guild.id)

        await message.channel.send(f"<#{gridchan.id}> has been reset.")

        return

    # Remove drivernos from server and cached data
    numchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    if numchan is None:
        await message.channel.send("Unable to remove DriverNos records due to channel no longer existing.")
    else:
        try:
            for msgid in guilddata[message.guild.id]["config"]["msg"]:
                msg = await numchan.fetch_message(msgid)
                await msg.delete()
        except discord.errors.NotFound:
            await message.channel.send("Unable to remove DriverNos records due to messages no longer existing.")

    for gridchanid in guilddata[message.guild.id]["grids"]:
        gridchan = message.guild.get_channel(int(gridchanid))
        if gridchan is None:
            await message.channel.send("Unable to remove DriverNos grid due to channel no longer existing.")
        else:
            try:
                msg = await gridchan.fetch_message(guilddata[message.guild.id]["grids"][str(gridchan.id)]["msg"])
                await msg.delete()
            except discord.errors.NotFound:
                await message.channel.send("Unable to remove DriverNos grid due to messages no longer existing.")

    dnos.removeConfig(message.guild.id)
    guilddata.pop(message.guild.id)

    await message.channel.send("DriverNos has been reset.")

    return
