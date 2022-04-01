import os
import sys
from modules import dnos, memaction, msgaction
from discord.ext import tasks

'''
Discord DriverNos Bot.

This is for racing leagues to help manage assignment of driver numbers, and using these in user nicknames.
'''

# Setup bot
client = dnos.startClient(configfile="data/guilddata.json")
gd = dnos.readConfig()


# Background task to check for releasing numbers every hour
@tasks.loop(hours=1)
async def reap():
    await dnos.reapExpired(gd)


# Discord Events
@client.event
async def on_ready():
    print(f"We have logged in as {client.user.name}")
    reap.start()


# Control events when messages are sent
@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Initialise bot in guild
    elif message.content.startswith(dnos.getCmd() + " init"):
        await msgaction.init(gd, message)

    # Assign a user a number
    elif message.content.startswith(dnos.getCmd() + " assign"):
        await msgaction.assign(gd, message)

    # Unassign a user a number
    elif message.content.startswith(dnos.getCmd() + " unassign"):
        await msgaction.unassign(gd, message)

    # Move the numbers listing to a new channel
    elif message.content.startswith(dnos.getCmd() + " move"):
        await msgaction.move(gd, message)

    # Reset drivernos for the guild
    elif message.content.startswith(dnos.getCmd() + " expiry"):
        await msgaction.setExpiry(gd, message)

    # Initialise grid in guild
    elif message.content.startswith(dnos.getCmd() + " grid"):
        await msgaction.grid(gd, message)

    # Add driver to team
    elif message.content.startswith(dnos.getCmd() + " teamadd"):
        await msgaction.teamAdd(gd, message)

    # Remove driver from team
    elif message.content.startswith(dnos.getCmd() + " teamdel"):
        await msgaction.teamDel(gd, message)

    # Reset drivernos for the guild
    elif message.content.startswith(dnos.getCmd() + " reset"):
        await msgaction.reset(gd, message)


# Control nicknames when a nickname is changed.
@client.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        await memaction.setNick(gd, after)


# Handle events when member leaves the guild it feature enabled
@client.event
async def on_member_remove(member):
    if gd[member.guild.id]["config"]["expiration"] > -1:
        if member.id in gd[member.guild.id]["numbers"].values():
            await memaction.handleLeaver(gd, member)


# Handle events when member leaves the guild it feature enabled
@client.event
async def on_member_join(member):
    if member.id in gd[member.guild.id]["numbers"].values():
        await memaction.handleRejoiner(gd, member)
    await memaction.setNick(gd, member)


# Get token and run
token = os.getenv("TOKEN")

if token is None:
    try:
        token_fh = open("/run/secrets/drivernos-secret")
    except IOError:
        sys.exit("Unable to find bot token.")

    token = token_fh.read()

client.run(token)
