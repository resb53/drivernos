# drivernos
## Discord bot for managing driver numbers

This is for racing leagues to help manage assignment of driver numbers, and using these in user nicknames.

### Functions:
```
## init:     Initialise the bot for this guild.
## assign:   Assign a number to a member.
## unassign: Remove a number from a member.
## move:     Move driver numbers listing to a new location.
## expiry:   Set time in seconds to auto-expire numbers for guild leavers.
## grid:     Set up a channel to be used as a driver grid.
## teamadd:  Add a driver to a team in a grid channel.
## teamdel:  Remove a driver from a team in a grid channel.
## reset:    Reset and wipe all help data for this guild.
```

    elif message.content.startswith("## init"):
        await msgaction.init(gd, message)

    # Assign a user a number
    elif message.content.startswith("## assign"):
        await msgaction.assign(gd, message)

    # Unassign a user a number
    elif message.content.startswith("## unassign"):
        await msgaction.unassign(gd, message)

    # Move the numbers listing to a new channel
    elif message.content.startswith("## move"):
        await msgaction.move(gd, message)

    # Reset drivernos for the guild
    elif message.content.startswith("## expiry"):
        await msgaction.setExpiry(gd, message)

    # Initialise grid in guild
    elif message.content.startswith("## grid"):
        await msgaction.grid(gd, message)

    # Add driver to team
    elif message.content.startswith("## teamadd"):
        await msgaction.teamAdd(gd, message)

    # Remove driver from team
    elif message.content.startswith("## teamdel"):
        await msgaction.teamDel(gd, message)

    # Reset drivernos for the guild
    elif message.content.startswith("## reset"):