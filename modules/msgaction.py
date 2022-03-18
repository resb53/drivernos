'''
Bot Operations for Discord Message actions.
'''
import re
from collections import defaultdict
from . import dnos, memaction


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
    guilddata[message.guild.id]["numbers"] = {}
    guilddata[message.guild.id]["config"] = {
        "msg0": msg0.id,
        "msg1": msg1.id,
        "numchanid": numchan.id
    }
    dnos.writeConfig(message.guild.id, guilddata[message.guild.id])

    await message.channel.send("DriverNos has been initialised in.")

    return


def test(guilddata, message):
    teststring = message.content[7:].strip(" ")
    print(teststring)

    return


async def assign(guilddata, message):
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

    # Assign the number in guilddata
    report = ""

    if member.id not in guilddata[message.guild.id]["numbers"].values():
        guilddata[message.guild.id]["numbers"][number] = member.id
        report = f"Driver number `{number}` assigned to <@!{member.id}>."
    else:
        oldnum = 0
        for x in guilddata[message.guild.id]["numbers"].items():
            if x[1] == member.id:
                oldnum = x[0]
        guilddata[message.guild.id]["numbers"].pop(oldnum)
        guilddata[message.guild.id]["numbers"][number] = member.id
        report = f"Driver number `{number}` assigned to <@{member.id}>, and number `{oldnum}` released."

    # Update number channel
    numchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])
    numbers = dnos.formatDrivers(guilddata, message.guild)
    msg0 = await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg0"])
    msg1 = await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg1"])
    await msg0.edit(content=numbers[0])
    await msg1.edit(content=numbers[1])

    # Assign the number to the members nickname
    await memaction.setNick(guilddata, member)

    # Report success
    dnos.writeConfig(message.guild.id, guilddata[message.guild.id])
    await message.channel.send(report)

    return


async def reset(guilddata, message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("This command can only be run by server admins.")
        return

    # TODO: For production CHECK THIS IS REALLY WANTED!

    if message.guild.id not in guilddata:
        await message.channel.send("Unable to reset DriverNos. It has not yet been initialised in this guild.")
        return

    # Remove drivernos from server and cached data
    numchan = message.guild.get_channel(guilddata[message.guild.id]["config"]["numchanid"])

    if numchan is None:
        # TODO: Handle this better
        print("Error: config out of sync")
        return

    msgs = [
        await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg0"]),
        await numchan.fetch_message(guilddata[message.guild.id]["config"]["msg1"])
    ]

    for msg in msgs:
        await msg.delete()

    dnos.removeConfig(message.guild.id)
    guilddata.pop(message.guild.id)

    await message.channel.send("DriverNos has been reset.")

    return
