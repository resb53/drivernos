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

    # Reset drivernos for the guild
    elif message.content.startswith("##reset"):
        await msgaction.reset(gd, message)


# Control nicknames when a nickname is changed.
@client.event
async def on_member_update(before, after):
    if before.nick != after.nick:
        await memaction.setNick(gd, after)


client.run(os.getenv("TOKEN"))
