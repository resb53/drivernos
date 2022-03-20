import os
from modules import dnos, memaction, msgaction

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

# Setup bot
client = dnos.startClient(configfile="data/guilddata.json")
gd = dnos.readConfig()


# Discord Events
@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


# Control events when messages are sent
@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Initialise bot in guild
    elif message.content.startswith("##init"):
        await msgaction.init(gd, message)

    elif message.content.startswith("##test"):
        msgaction.test(gd, message)

    # Assign a user a number
    elif message.content.startswith("##assign"):
        await msgaction.assign(gd, message)

    # Unassign a user a number
    elif message.content.startswith("##unassign"):
        await msgaction.unassign(gd, message)

    # Move the numbers listing to a new channel
    elif message.content.startswith("##move"):
        await msgaction.move(gd, message)

    # Reset drivernos for the guild
    elif message.content.startswith("##reset"):
        await msgaction.reset(gd, message)


# Control nicknames when a nickname is changed.
@client.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        await memaction.setNick(gd, after)


# Handle events when member leaves the guild.
@client.event
async def on_member_remove(member):
    if member.id in gd[member.guild.id]["numbers"].values():
        memaction.handleLeaver(gd, member)


client.run(os.getenv("TOKEN"))
