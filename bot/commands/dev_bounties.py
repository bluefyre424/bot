import discord
from datetime import datetime

from . import commandsDB as botCommands
from .. import botState, lib
from ..cfg import cfg, bbData
from ..gameObjects.bounties import bounty, bountyConfig

botCommands.addHelpSection(2, "bounties")


async def dev_cmd_clear_bounties(message : discord.Message, args : str, isDM : bool):
    """developer command clearing all active bounties. If a guild ID is given, clear bounties in that guild.
    If 'all' is given, clear bounties in all guilds. If nothing is given, clear bounties in the calling guild.

    :param discord.Message message: the discord message calling the command
    :param str args: empty or a guild id
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if args == "all":
        for guild in botState.guildsDB.getGuilds():
            if not guild.bountiesDisabled:
                if guild.hasBountyBoardChannel:
                    await guild.bountyBoardChannel.clear()
                guild.bountiesDB.clearBounties()
        await message.reply(mention_author=False, content=":ballot_box_with_check: All active bounties cleared.")
        return
    elif args == "":
        if isDM:
            await message.reply(mention_author=False, content="Give either an id or 'all', or call from within a guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(message.guild.id)
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content="This guild has bounties disabled.")
            return
    elif lib.stringTyping.isInt(args):
        if not botState.guildsDB.idExists(int(args)):
            await message.reply(mention_author=False, content="Unrecognised guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(int(args))
        if callingBBGuild.bountiesDisabled:
            await message.reply((("'" + callingBBGuild.dcGuild.name + "' ") if callingBBGuild.dcGuild is not None \
                                        else "The requested guild ") + " has bounties disabled.",
                                mention_author=False)
            return
    else:
        await message.reply(mention_author=False, content=":x: Unrecognised parameter: " + args)
        return

    if callingBBGuild.hasBountyBoardChannel:
        await callingBBGuild.bountyBoardChannel.clear()
    callingBBGuild.bountiesDB.clearBounties()
    await message.reply(mention_author=False, content=":ballot_box_with_check: Active bounties cleared" + ((" for '" + callingBBGuild.dcGuild.name \
                                + "'.") if callingBBGuild.dcGuild is not None else "."))

botCommands.register("clear-bounties", dev_cmd_clear_bounties, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_get_cooldown(message : discord.Message, args : str, isDM : bool):
    """developer command printing the calling user's checking cooldown

    :param discord.Message message: the discord message calling the command
    :param str args: ignore
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    callingUser = botState.usersDB.getUser(message.author.id)
    diff = datetime.utcfromtimestamp(callingUser.bountyCooldownEnd) - datetime.utcnow()
    minutes = int(diff.total_seconds() / 60)
    seconds = int(diff.total_seconds() % 60)
    await message.reply(str(callingUser.bountyCooldownEnd) + " = " + str(minutes) + "m, " + str(seconds) + "s.", mention_author=False)
    await message.reply(datetime.utcfromtimestamp(callingUser.bountyCooldownEnd).strftime("%Hh%Mm%Ss"), mention_author=False)
    await message.reply(datetime.utcnow().strftime("%Hh%Mm%Ss"), mention_author=False)

botCommands.register("get-cool", dev_cmd_get_cooldown, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_reset_cooldown(message : discord.Message, args : str, isDM : bool):
    """developer command resetting the checking cooldown of the calling user, or the specified user if one is given

    :param discord.Message message: the discord message calling the command
    :param str args: string, can be empty or contain a user mention
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # reset the calling user's cooldown if no user is specified
    if args == "":
        botState.usersDB.getUser(
            message.author.id).bountyCooldownEnd = datetime.utcnow().timestamp()
    # otherwise get the specified user's discord object and reset their cooldown.
    # [!] no validation is done.
    else:
        botState.usersDB.getUser(int(args.lstrip("<@!").rstrip(">"))).bountyCooldownEnd = datetime.utcnow().timestamp()
    await message.reply(mention_author=False, content="Done!")

botCommands.register("reset-cool", dev_cmd_reset_cooldown, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_reset_daily_wins(message : discord.Message, args : str, isDM : bool):
    """developer command resetting the max daily bounty wins of the calling user, or the specified user if one is given

    :param discord.Message message: the discord message calling the command
    :param str args: string, can be empty or contain a user mention
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # reset the calling user's cooldown if no user is specified
    if args == "":
        requestedBBUser = botState.usersDB.getUser(message.author.id)
    else:
        # [!] no validation is done.
        requestedBBUser = botState.usersDB.getUser(int(args.lstrip("<@!").rstrip(">")))
    requestedBBUser.dailyBountyWinsReset = datetime.utcnow()
    requestedBBUser.bountyWinsToday = 0
    # otherwise get the specified user's discord object and reset their cooldown.

    await message.reply(mention_author=False, content="Done!")

botCommands.register("reset-daily-wins", dev_cmd_reset_daily_wins, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_setcheckcooldown(message : discord.Message, args : str, isDM : bool):
    """developer command setting the checking cooldown applied to users
    this does not update cfg and will be reverted on bot restart

    :param discord.Message message: the discord message calling the command
    :param str args: string containing an integer number of minutes
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a time was requested
    if args == "":
        await message.reply(mention_author=False, content=":x: please give the number of minutes!")
        return
    # verify the requested time is an integer
    if not lib.stringTyping.isInt(args):
        await message.reply(mention_author=False, content=":x: that's not a number!")
        return
    # update the checking cooldown amount
    cfg.timeouts.checkCooldown["minutes"] = int(args)
    await message.reply(mention_author=True, content="Done! *you still need to update the config file though* ")

botCommands.register("setcheckcooldown", dev_cmd_setcheckcooldown, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_setbountyperiodm(message : discord.Message, args : str, isDM : bool):
    """developer command setting the number of minutes in the new bounty generation period
    this does not update cfg and will be reverted on bot restart
    this does not affect the numebr of hours in the new bounty generation period

    :param discord.Message message: the discord message calling the command
    :param str args: string containing an integer number of minutes
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a time was given
    if args == "":
        await message.reply(mention_author=False, content=":x: please give the number of minutes!")
        return
    # verify the given time is an integer
    if not lib.stringTyping.isInt(args):
        await message.reply(mention_author=False, content=":x: that's not a number!")
        return
    # update the new bounty generation cooldown
    cfg.newBountyFixedDelta["minutes"] = int(args)
    botState.newBountyFixedDeltaChanged = True
    await message.reply(mention_author=True, content="Done! *you still need to update the config file though*")

botCommands.register("setbountyperiodm", dev_cmd_setbountyperiodm, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_setbountyperiodh(message : discord.Message, args : str, isDM : bool):
    """developer command setting the number of hours in the new bounty generation period
    this does not update cfg and will be reverted on bot restart
    this does not affect the numebr of minutes in the new bounty generation period

    :param discord.Message message: the discord message calling the command
    :param str args: string containing an integer number of hours
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a time was specified
    if args == "":
        await message.reply(mention_author=False, content=":x: please give the number of hours!")
        return
    # verify the given time is an integer
    if not lib.stringTyping.isInt(args):
        await message.reply(mention_author=False, content=":x: that's not a number!")
        return
    # update the bounty generation period
    botState.newBountyFixedDeltaChanged = True
    cfg.newBountyFixedDelta["hours"] = int(args)
    await message.reply(mention_author=True, content="Done! *you still need to update the file though*")

botCommands.register("setbountyperiodh", dev_cmd_setbountyperiodh, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_resetnewbountycool(message : discord.Message, args : str, isDM : bool):
    """developer command resetting the current bounty generation period,
    instantly generating a new bounty

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    guildStr = args

    if guildStr == "":
        if isDM:
            await message.reply(mention_author=False, content="Either give a guild id or call from within a guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(message.guild.id)
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content="This guild has bounties disabled.")
            return
    elif lib.stringTyping.isInt(guildStr):
        if not botState.guildsDB.idExists(int(guildStr)):
            await message.reply(mention_author=False, content="Unrecognised guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(int(guildStr))
        if callingBBGuild.bountiesDisabled:
            await message.reply((("'" + callingBBGuild.dcGuild.name + "' ") if callingBBGuild.dcGuild is not None \
                                        else "The requested guild ") + " has bounties disabled.", mention_author=False)
            return
    else:
        await message.reply(mention_author=False, content=":x: Unrecognised parameter: " + guildStr)
        return

    await callingBBGuild.newBountyTT.forceExpire()
    await message.reply(mention_author=False, content=":ballot_box_with_check: New bounty cooldown reset for '" + callingBBGuild.dcGuild.name + "'")

botCommands.register("resetnewbountycool", dev_cmd_resetnewbountycool, 2, allowDM=True, helpSection="bounties", useDoc=True)


async def dev_cmd_canmakebounty(message : discord.Message, args : str, isDM : bool):
    """developer command printing whether or not the given faction can accept new bounties
    If no guild ID is given, bounty spawning ability is checked for the calling guild

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a faction followed by optionally a guild ID
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    newFaction = args.split(" ")[0].lower()
    guildStr = args.split(" ")[1] if len(args.split(" ")) > 1 else ""

    if guildStr == "":
        if isDM:
            await message.reply(mention_author=False, content="Either give a guild id or call from within a guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(message.guild.id)
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content="This guild has bounties disabled.")
            return
    elif lib.stringTyping.isInt(guildStr):
        if not botState.guildsDB.idExists(int(guildStr)):
            await message.reply(mention_author=False, content="Unrecognised guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(int(guildStr))
        if callingBBGuild.bountiesDisabled:
            await message.reply((("'" + callingBBGuild.dcGuild.name + "' ") if callingBBGuild.dcGuild is not None \
                                else "The requested guild ") + " has bounties disabled.", mention_author=False)
            return
    else:
        await message.reply(mention_author=False, content=":x: Unrecognised parameter: " + guildStr)
        return

    # ensure the given faction exists
    if not callingBBGuild.bountiesDB.factionExists(newFaction):
        await message.reply(mention_author=False, content="not a faction: '" + newFaction + "'")
    else:
        await message.reply(callingBBGuild.bountiesDB.factionCanMakeBounty(newFaction.lower()), mention_author=False)

botCommands.register("canmakebounty", dev_cmd_canmakebounty, 2, allowDM=False, helpSection="bounties", useDoc=True)


async def dev_cmd_make_bounty(message : discord.Message, args : str, isDM : bool):
    """developer command making a new bounty
    args should be separated by a space and then a plus symbol
    if no args are given, generate a new bounty at complete random
    if only one argument is given it is assumed to be a faction, and a bounty is generated for that faction
    otherwise, all 9 arguments required to generate a bounty must be given
    the route should be separated by only commas and no spaces. the endTime should be a UTC timestamp. Any argument can be
    given as 'auto' to be either inferred or randomly generated
    as such, '!bb make-bounty' is an alias for '!bb make-bounty +auto +auto +auto +auto +auto +auto +auto +auto +auto'

    :param discord.Message message: the discord message calling the command
    :param str args: can be empty, can be '[guild id] +<faction>', or can be '[guild id] +<faction> +<name> +<route> +<start>
                        +<end> +<answer> +<reward> +<endtime> +<icon>'
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    guildStr = args.split("+")[0].strip()
    args = args[len(guildStr):].lstrip()
    if guildStr == "":
        if isDM:
            await message.reply(mention_author=False, content="Either give a guild id or call from within a guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(message.guild.id)
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content="This guild has bounties disabled.")
            return
    elif lib.stringTyping.isInt(guildStr):
        if not botState.guildsDB.idExists(int(guildStr)):
            await message.reply(mention_author=False, content="Unrecognised guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(int(guildStr))
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content=(("'" + callingBBGuild.dcGuild.name + "' ") if callingBBGuild.dcGuild is not None \
                                        else "The requested guild ") + " has bounties disabled.")
            return
    else:
        await message.reply(mention_author=False, content=":x: Unrecognised parameter: " + guildStr)
        return

    # if no args were given, generate a completely random bounty
    if args == "":
        newBounty = bounty.Bounty(owningDB=callingBBGuild.bountiesDB)
    # if only one argument was given, use it as a faction
    elif len(args.split("+")) == 2:
        newFaction = args.split("+")[1]
        newBounty = bounty.Bounty(
            owningDB=callingBBGuild.bountiesDB, config=bountyConfig.BountyConfig(faction=newFaction))

    # if all args were given, generate a completely custom bounty
    # 9 args plus account for empty string at the start of the split = split of 10 elements
    elif len(args.split("+")) == 10:
        # track whether a builtIn criminal was requested
        builtIn = False
        builtInCrimObj = None
        # [1:] remove empty string before + splits
        bData = args.split("+")[1:]

        # parse the given faction
        newFaction = bData[0].rstrip(" ")
        if newFaction == "auto":
            newFaction = ""

        # parse the given criminal name
        newName = bData[1].rstrip(" ").title()
        if newName == "Auto":
            newName = ""
        else:
            # if a criminal name was given, see if it corresponds to a builtIn criminal
            for crim in bbData.builtInCriminalObjs.values():
                if crim.isCalled(newName):
                    builtIn = True
                    builtInCrimObj = crim
                    newName = crim.name
                    break

            # if a criminal name was given, ensure it does not already exist as a bounty
            if newName != "" and callingBBGuild.bountiesDB.bountyNameExists(newName):
                await message.reply(mention_author=False, content=":x: That pilot is already wanted!")
                return

        # parse the given route
        newRoute = bData[2].rstrip(" ")
        if newRoute == "auto":
            newRoute = []
        else:
            newRoute = bData[2].split(",")
            newRoute[-1] = newRoute[-1].rstrip(" ")

        # parse the given start system
        newStart = bData[3].rstrip(" ")
        if newStart == "auto":
            newStart = ""

        # parse the given end system
        newEnd = bData[4].rstrip(" ")
        if newEnd == "auto":
            newEnd = ""

        # parse the given answer system
        newAnswer = bData[5].rstrip(" ")
        if newAnswer == "auto":
            newAnswer = ""

        # parse the given reward amount
        newReward = bData[6].rstrip(" ")
        if newReward == "auto":
            newReward = -1
        newReward = int(newReward)

        # parse the given end time
        newEndTime = bData[7].rstrip(" ")
        if newEndTime == "auto":
            newEndTime = -1.0
        newEndTime = float(newEndTime)

        # parse the given icon
        newIcon = bData[8].rstrip(" ")
        if newIcon == "auto":
            newIcon = "" if not builtIn else builtInCrimObj.icon

        # special bounty generation for builtIn criminals
        if builtIn:
            newBounty = bounty.Bounty(owningDB=callingBBGuild.bountiesDB, criminalObj=builtInCrimObj,
                                        config=bountyConfig.BountyConfig(faction=newFaction, name=newName, route=newRoute,
                                                                            start=newStart, end=newEnd, answer=newAnswer,
                                                                            reward=newReward, endTime=newEndTime,
                                                                            isPlayer=False, icon=newIcon))
        # normal bounty generation for custom criminals
        else:
            newBounty = bounty.Bounty(owningDB=callingBBGuild.bountiesDB,
                                        config=bountyConfig.BountyConfig(faction=newFaction, name=newName, route=newRoute,
                                                                            start=newStart, end=newEnd, answer=newAnswer,
                                                                            reward=newReward, endTime=newEndTime,
                                                                            isPlayer=False, icon=newIcon))

    # Report an error for invalid command syntax
    else:
        await message.reply(mention_author=False, content="incorrect syntax. give +faction +name +route +start +end +answer +reward +endtime +icon")
        return

    # activate and announce the new bounty
    callingBBGuild.bountiesDB.addBounty(newBounty)
    await callingBBGuild.announceNewBounty(newBounty)

botCommands.register("make-bounty", dev_cmd_make_bounty, 2, forceKeepArgsCasing=True, allowDM=True, helpSection="bounties",
                    useDoc=True)


async def dev_cmd_make_player_bounty(message : discord.Message, args : str, isDM : bool):
    """developer command making a new PLAYER bounty
    args should be separated by a space and then a plus symbol
    the first argument should be a user MENTION
    if one arg is given, generate a new bounty at complete random, for the specified user
    if two arguments are given the second is assumed to be a faction, and a bounty is generated for that faction for the
    specified user
    otherwise, all 9 arguments required to generate a bounty must be given
    the route should be separated by only commas and no spaces. the endTime should be a UTC timestamp. Any argument can
    be given as 'auto' to be either inferred or randomly generated
    as such, '!bb make-player-bounty <user>' is an alias for '!bb make-bounty +auto +<user> +auto +auto +auto +auto
                                                                +auto +auto +auto'

    :param discord.Message message: the discord message calling the command
    :param str args: can be empty, can be '[guild id] +<user_mention> +<faction>', or can be '[guild id] +<faction>
                        +<user_mention> +<route> +<start> +<end> +<answer> +<reward> +<endtime> +<icon>'
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    guildStr = args.split("+")[0].strip()
    args = args[len(guildStr):].lstrip()
    if guildStr == "":
        if isDM:
            await message.reply(mention_author=False, content="Either give a guild id or call from within a guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(message.guild.id)
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content="This guild has bounties disabled.")
            return
    elif lib.stringTyping.isInt(guildStr):
        if not botState.guildsDB.idExists(int(guildStr)):
            await message.reply(mention_author=False, content="Unrecognised guild")
            return
        callingBBGuild = botState.guildsDB.getGuild(int(guildStr))
        if callingBBGuild.bountiesDisabled:
            await message.reply(mention_author=False, content=(("'" + callingBBGuild.dcGuild.name + "' ") if callingBBGuild.dcGuild is not None \
                                        else "The requested guild ") + " has bounties disabled.")
            return
    else:
        await message.reply(mention_author=False, content=":x: Unrecognised parameter: " + guildStr)
        return

    # if only one argument is given
    if len(args.split(" ")) == 1:
        # verify the requested user
        requestedID = int(args.lstrip("<@!").rstrip(">"))
        requestedUser = botState.client.get_user(requestedID)
        if not lib.stringTyping.isInt(requestedID) or requestedUser is None:
            await message.reply(mention_author=False, content=":x: Player not found!")
            return
        # create a new bounty at random for the specified user
        newCfg = bountyConfig.BountyConfig(name="<@" + str(requestedID) + ">", isPlayer=True,
                                            icon=str(requestedUser.avatar_url_as(size=64)),
                                            aliases=[lib.discordUtil.userTagOrDiscrim(args)])
        newBounty = bounty.Bounty(owningDB=callingBBGuild.bountiesDB, config=newCfg)

    # if the faction is also given
    elif len(args.split("+")) == 2:
        # verify the user
        requestedID = int(args.split(" ")[0].lstrip("<@!").rstrip(">"))
        if not lib.stringTyping.isInt(requestedID) or (botState.client.get_user(int(requestedID))) is None:
            await message.reply(mention_author=False, content=":x: Player not found!")
            return
        # create a bounty at random for the specified user and faction
        newFaction = args.split("+")[1]
        newCfg = bountyConfig.BountyConfig(name="<@" + str(requestedID) + ">", isPlayer=True, faction=newFaction,
                                    icon=str(botState.client.get_user(requestedID).avatar_url_as(size=64)),
                                    aliases=[lib.discordUtil.userTagOrDiscrim(args.split(" ")[0])])
        newBounty = bounty.Bounty(owningDB=callingBBGuild.bountiesDB, config=newCfg)

    # if all arguments are given
    elif len(args.split("+")) == 10:
        # [1:] remove starting empty string before + split
        bData = args.split("+")[1:]

        # parse the requested faction
        newFaction = bData[0].rstrip(" ")
        if newFaction == "auto":
            newFaction = ""

        # parse the requested user ID
        # no auto option!
        newName = bData[1].rstrip(" ").title()
        # verify the requested user
        requestedID = int(newName.lstrip("<@!").rstrip(">"))
        if not lib.stringTyping.isInt(requestedID) or (botState.client.get_user(int(requestedID))) is None:
            await message.reply(mention_author=False, content=":x: Player not found!")
            return
        # ensure no bounty already exists for this user
        if callingBBGuild.bountiesDB.bountyNameExists(newName):
            await message.reply(mention_author=False, content=":x: That pilot is already wanted!")
            return

        # parse the requested route
        newRoute = bData[2].rstrip(" ")
        if newRoute == "auto":
            newRoute = []
        else:
            newRoute = bData[2].split(",")
            newRoute[-1] = newRoute[-1].rstrip(" ")

        # parse the requested start system
        newStart = bData[3].rstrip(" ")
        if newStart == "auto":
            newStart = ""

        # parse the requested end system
        newEnd = bData[4].rstrip(" ")
        if newEnd == "auto":
            newEnd = ""

        # parse the requested answer system
        newAnswer = bData[5].rstrip(" ")
        if newAnswer == "auto":
            newAnswer = ""

        # parse the requested reward pool
        newReward = bData[6].rstrip(" ")
        if newReward == "auto":
            newReward = -1
        newReward = int(newReward)

        # parse the requested end time
        newEndTime = bData[7].rstrip(" ")
        if newEndTime == "auto":
            newEndTime = -1.0
        newEndTime = float(newEndTime)

        # parse the requested icon URL
        newIcon = bData[8].rstrip(" ")
        if newIcon == "auto":
            newIcon = str(botState.client.get_user(
                int(newName.lstrip("<@!").rstrip(">"))).avatar_url_as(size=64))

        # create the bounty object
        newBounty = bounty.Bounty(owningDB=callingBBGuild.bountiesDB,
                                    config=bountyConfig.BountyConfig(faction=newFaction, name=newName, route=newRoute,
                                                                        start=newStart, end=newEnd, answer=newAnswer,
                                                                        reward=newReward, endTime=newEndTime, isPlayer=True,
                                                                        icon=newIcon,
                                                                        aliases=[lib.discordUtil.userTagOrDiscrim(newName)]))

    # print an error for incorrect syntax
    else:
        await message.reply(mention_author=False, content="incorrect syntax. give +faction +userTag +route +start +end " \
                                    + "+answer +reward +endtime +icon")
        return

    # activate and announce the bounty
    callingBBGuild.bountiesDB.addBounty(newBounty)
    await callingBBGuild.announceNewBounty(newBounty)

botCommands.register("make-player-bounty", dev_cmd_make_player_bounty, 2, forceKeepArgsCasing=True, allowDM=True,
                        helpSection="bounties", useDoc=True)
