'''
Set Discord Intents and Permissions for the bot, and related features.
'''
import discord


def setIntents():
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True

    return intents
