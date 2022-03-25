'''
Bot Operations for Discord Message actions.
'''
import discord
import re
import time
from . import dnos


async def setNick(guilddata, member, message=None):
    name = ""

    if member.nick is None:
        name = member.name
    else:
        name = member.nick

    # If user has a driver number, prepend this to their chosen name
    number = None

    if member.id in guilddata[member.guild.id]["numbers"].values():
        for n, id in guilddata[member.guild.id]["numbers"].items():
            if id == member.id:
                number = n

    # Remove any prepended number tags
    ready = False

    while not ready:
        m = re.match(r"^\s*\d{1,2} \|\| (.+)$", name)

        if m is not None:
            name = m.group(1)
        else:
            ready = True

    if number is not None:
        name = f"{number} || " + name

    # Update user nickname
    try:
        await member.edit(nick=name)
    except discord.errors.Forbidden:
        # Silently fail if admins / higher ranks change their own nickname
        if message is not None:
            await message.channel.send(f"\nUnable to modify nickname for <@!{member.id}>. "
                                       "Bot must be a higher rank than the member. "
                                       "Guild owner must manually set nickname.")

    return


async def handleLeaver(guilddata, member):
    # Add expiry to the leavers driver number
    dno = "0"
    for x in guilddata[member.guild.id]["numbers"].items():
        if x[1] == member.id:
            dno = x[0]

    expiration = guilddata[member.guild.id]["config"]["expiration"]

    if expiration == 0:
        # Instantly remove allocation
        guilddata[member.guild.id]["numbers"].pop(dno)
        await dnos.updateDrivers(guilddata, member.guild.id)
    else:
        # Set expiry on allocation
        guilddata[member.guild.id]["expires"][dno] = int(time.time()) + expiration

    dnos.writeConfig(guilddata, member.guild.id)

    return


async def handleRejoiner(guilddata, member):
    # Remove expiry
    dno = "0"
    for x in guilddata[member.guild.id]["numbers"].items():
        if x[1] == member.id:
            dno = x[0]

    if dno in guilddata[member.guild.id]["expires"]:
        guilddata[member.guild.id]["expires"].pop(dno)
        dnos.writeConfig(guilddata, member.guild.id)
