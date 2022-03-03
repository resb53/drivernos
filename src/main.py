import discord
import os
from collections import defaultdict

client = discord.Client()

blank_template = ["", ""]
for i in range(1, 10):
    blank_template[0] += f"` {i}` - \n"
for i in range(10, 50):
    blank_template[0] += f"`{i}` - \n"
for i in range(50, 100):
    blank_template[1] += f"`{i}` - \n"


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith(".init"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("This command can only be run by server admins.")
            return

        numchan = message.content[6:].strip(" ")

        if len(numchan) == 0:
            await message.channel.send("Please provide a channel name to initialise. e.g: `.init numbers`")
            return

        textchannels = defaultdict(list)

        for tchans in message.guild.text_channels:
            textchannels[tchans.name].append(tchans.id)

        if numchan not in textchannels:
            await message.channel.send(f"Text channel `{numchan}` does not exist.")
            return
        elif len(textchannels[numchan]) > 1:
            await message.channel.send(f"Multiple `{numchan}` channels exist. Choose a unique channel name.")
            return

        numchanid = message.guild.get_channel(textchannels[numchan][0])

        for msg in blank_template:
            await numchanid.send(msg)

        return


client.run(os.getenv("TOKEN"))
