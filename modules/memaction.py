'''
Bot Operations for Discord Message actions.
'''
import re


async def setNick(guilddata, member):
    name = ""

    if member.nick is None:
        name = member.name
    else:
        name = member.nick

    # If user has a driver number, prepend this to their chosen name
    number = None

    if member.id not in guilddata[member.guild.id]["numbers"].values():
        return
    else:
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

    name = f"{number} || " + name

    # Update user nickname
    await member.edit(nick=name)

    return
