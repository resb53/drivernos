import discord
import os

client = discord.Client()


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

        else:
            numchan = message.content[6:].strip(" ")

            if numchan in [c.name for c in message.guild.text_channels]:
                await message.channel.send(f"Initialising DriverNos in channel {numchan}.")
            else:
                await message.channel.send(f"Text channel {numchan} does not exist.")


client.run(os.getenv("TOKEN"))
