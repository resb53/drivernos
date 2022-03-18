'''
Bot Operations for Discord Message actions.
'''


def nickchange(guilddata, before, after):
    name = ""

    if after.nick is None:
        name = after.name
    else:
        name = after.nick

    # If user has a driver number, prepend this to their chosen name
    number = None

    if after.id not in guilddata[after.guild.id]["numbers"].values():
        return
    else:
        for n, id in guilddata[after.guild.id]["numbers"].items():
            if id == after.id:
                number = n

    print(f"Driver number {number} changed their name to {name}.")
