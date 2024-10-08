import discord
import os
import asyncio
import time
from datetime import timedelta

from . import commandsDB as botCommands
from . import util_help
from .. import botState, lib
from ..cfg import cfg, bbData
from ..userAlerts import userAlerts
from ..scheduling import timedTask
from ..reactionMenus import reactionRolePicker, reactionSkinRegionPicker
from ..gameObjects.items import shipItem
from ..shipRenderer import shipRenderer

CWD = os.getcwd()
robotIcon = "https://emojipedia-us.s3.dualstack.us-west-1.amazonaws.com/thumbs/120/twitter/259/robot_1f916.png"


async def admin_cmd_admin_help(message: discord.Message, args: str, isDM: bool):
    """admin command printing help strings for admin commands

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    await util_help.util_autohelp(message, args, isDM, 2)

botCommands.register("admin-help", admin_cmd_admin_help, 2, signatureStr="**admin-help** *[page number, section or command]*",
                     shortHelp="Display information about admin-only commands.\nGive a specific command for detailed " \
                                + "info about it, or give a page number or give a section name for brief info.",
                     longHelp="Display information about admin-only commands.\nGive a specific command for detailed " \
                                + "info about it, or give a page number or give a section name for brief info about " \
                                + "a set of commands. These are the currently valid section names:\n- Miscellaneous")


async def admin_cmd_set_prefix(message: discord.Message, args: str, isDM: bool):
    """admin command setting the calling guild's command prefix

    :param discord.Message message: the discord message calling the command
    :param str args: the command prefix to use
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    callingBGuild = botState.guildsDB.getGuild(message.guild.id)

    if not args:
        await message.reply(mention_author=False, content="Please provide the command prefix you would like to set. E.g: `" \
                                    + callingBGuild.commandPrefix + "set-prefix $`")
    else:
        callingBGuild.commandPrefix = args
        await message.reply(mention_author=False, content="Command prefix set.")

botCommands.register("set-prefix", admin_cmd_set_prefix, 2, signatureStr="**set-prefix <prefix>**",
                     shortHelp="Set the prefix you would like to use for bot commands in this server.")


async def admin_cmd_ping(message: discord.Message, args: str, isDM: bool):
    """admin command testing bot latency.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    start = time.perf_counter()
    msg = await message.reply(mention_author=False, content="Ping...")
    end = time.perf_counter()
    duration = (end - start) * 1000
    await msg.edit(content='Pong! {:.2f}ms'.format(duration))

botCommands.register("ping", admin_cmd_ping, 2, signatureStr="**ping**",
                     shortHelp="Test the bot's response latency in milliseconds.")


async def admin_cmd_config(message : discord.Message, args : str, isDM : bool):
    """Apply various bountybot configuration settings for the calling guild.
    TODO: Refactor!

    :param discord.Message message: the discord message calling the command
    :param str args: A string containing a config setting id followed by a value
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    argsSplit = args.split(" ")
    if isDM:
        prefix = cfg.defaultCommandPrefix
    else:
        prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix

    if len(argsSplit) < 2 or not (argsSplit[0] and argsSplit[1]):
        await message.reply(mention_author=False, content=":x: Please provide both a setting and a value! e.g: `" + prefix \
                                    + "config bounties enable`")
        return

    setting, value = argsSplit[0], " ".join(argsSplit[1:])

    trueStrings = ["yes", "true", "on", "enable", "enabled"]
    falseStrings = ["no", "false", "off", "disable", "disabled"]
    callingBBGuild = botState.guildsDB.getGuild(message.guild.id)

    if setting in ["bounty", "bounties"]:
        if value in trueStrings:
            if not callingBBGuild.bountiesDisabled:
                await message.reply(mention_author=False, content=":x: Bounties are already enabled in this server!")
            else:
                callingBBGuild.enableBounties()
                await message.reply(mention_author=False, content=":white_check_mark: Bounties are now enabled on this server!")
        elif value in falseStrings:
            if callingBBGuild.bountiesDisabled:
                await message.reply(mention_author=False, content=":x: Bounties are already disabled in this server!")
            else:
                callingBBGuild.disableBounties()
                await message.reply(mention_author=False, content=":white_check_mark: Bounties are now disabled on this server!")
        else:
            await message.reply(mention_author=False, content=":x: Unknown value!")
    elif setting in ["shop", "shops"]:
        if value in trueStrings:
            if not callingBBGuild.shopDisabled:
                await message.reply(mention_author=False, content=":x: The shop is already enabled in this server!")
            else:
                callingBBGuild.enableShop()
                await message.reply(mention_author=False, content=":white_check_mark: The shop is now enabled on this server!")
        elif value in falseStrings:
            if callingBBGuild.shopDisabled:
                await message.reply(mention_author=False, content=":x: The shop is already disabled in this server!")
            else:
                callingBBGuild.disableShop()
                await message.reply(mention_author=False, content=":white_check_mark: The shop is now disabled on this server!")
        else:
            await message.reply(mention_author=False, content=":x: Unknown value!")
    else:
        await message.reply(mention_author=False, content=":x: Unknown setting!")

botCommands.register("config", admin_cmd_config, 1, signatureStr="**config <setting> <value>**",
                        shortHelp="Set various settings for how bountybot will function in this server.",
                        longHelp="Set various settings for how bountybot will function in this server. Currently, " \
                                    + "`setting` can be either 'bounties' or 'shop', and `value` can either " \
                                    + "'enable' or 'disable', all with a few handy aliases. This command is lets you enable " \
                                    + "or disable large amounts of functionality all together.")


async def admin_cmd_del_reaction_menu(message : discord.Message, args : str, isDM : bool):
    """Force the expiry of the specified reaction menu message, regardless of reaction menu type.

    :param discord.Message message: the discord message calling the command
    :param str args: A string containing the message ID of an active reaction menu.
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    msgID = int(args)
    if msgID in botState.reactionMenusDB:
        await botState.reactionMenusDB[msgID].delete()
    else:
        await message.reply(mention_author=False, content=":x: Unrecognised reaction menu!")

botCommands.register("del-reaction-menu", admin_cmd_del_reaction_menu, 1, signatureStr="**del-reaction-menu <id>**",
                        longHelp="Remove the specified reaction menu. You can also just delete the message," \
                                    + " if you have permissions.\nTo get the ID of a reaction menu, enable discord's " \
                                    + "developer mode, right click on the menu, and click Copy ID.")


async def admin_cmd_set_notify_role(message : discord.Message, args : str, isDM : bool):
    """For the current guild, set a role to mention when certain events occur.

    can take either a role mention or ID.

    :param discord.Message message: the discord message calling the command
    :param str args: the notfy role type, and either a role mention or a role ID
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    argsSplit = args.split(" ")
    if len(argsSplit) < 2:
        await message.reply(mention_author=False, content=":x: Please provide both a notification type, and either a role mention or ID!")
        return
    if not (lib.stringTyping.isInt(argsSplit[-1]) or lib.stringTyping.isRoleMention(argsSplit[-1])):
        await message.reply(mention_author=False, content=":x: Invalid role! Please give either a role mention or ID!")
        return

    requestedBBGuild = botState.guildsDB.getGuild(message.guild.id)
    alertsToSet = userAlerts.getAlertIDFromHeirarchicalAliases(argsSplit)
    if alertsToSet[0] == "ERR":
        await message.reply(alertsToSet[1].replace("$COMMANDPREFIX$", requestedBBGuild.commandPrefix),
                            mention_author=False)
        return

    if lib.stringTyping.isRoleMention(argsSplit[-1]):
        requestedRole = message.guild.get_role(int(argsSplit[-1][3:-1]))
    else:
        requestedRole = message.guild.get_role(int(argsSplit[-1]))

    if requestedRole is None:
        await message.reply(mention_author=False, content=":x: Role not found!")
        return

    for alertID in alertsToSet:
        alertType = userAlerts.userAlertsIDsTypes[alertID]
        requestedBBGuild.setUserAlertRoleID(alertID, requestedRole.id)
        await message.reply(mention_author=False, content=":white_check_mark: Role set for " + userAlerts.userAlertsTypesNames[alertType] \
                                    + " notifications!")

botCommands.register("set-notify-role", admin_cmd_set_notify_role, 1,
                        signatureStr="**set-notify-role <type>** *[alert]* **<role>**",
                        shortHelp="Set a role to ping when various events occur. For valid notification types, " \
                                    + "see `help notify`.", longHelp="Set a role to ping when various events occur. " \
                                    + "**<type>** and/or *[alert]* must specify a type of notification. **<role>** can be " \
                                    + "either a role mention, or a role ID. For valid notification types, see `help notify`.")


async def admin_cmd_remove_notify_role(message : discord.Message, args : str, isDM : bool):
    """For the current guild, remove role mentioning when certain events occur.
    Takes only a UserAlert ID.

    :param discord.Message message: the discord message calling the command
    :param str args: the notfy role type, and either a role mention or a role ID
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if args == "":
        await message.reply(mention_author=False, content=":x: Please provide both a notification type!")
        return

    requestedBBGuild = botState.guildsDB.getGuild(message.guild.id)
    alertsToSet = userAlerts.getAlertIDFromHeirarchicalAliases(args)
    if alertsToSet[0] == "ERR":
        await message.reply(alertsToSet[1].replace("$COMMANDPREFIX$", requestedBBGuild.commandPrefix),
                            mention_author=False)
        return

    for alertID in alertsToSet:
        alertType = userAlerts.userAlertsIDsTypes[alertID]
        requestedBBGuild.removeUserAlertRoleID(alertID)
        await message.reply(mention_author=False, content=":white_check_mark: Role pings disabled for " \
                                    + userAlerts.userAlertsTypesNames[alertType] + " notifications.")

botCommands.register("remove-notify-role", admin_cmd_remove_notify_role, 1,
                        signatureStr="**remove-notify-role <type>** *[alert]*",
                        shortHelp="Disable role pings for various events. For valid notification types, see `help notify`.",
                        longHelp="Disable role pings for various events. **<type>** and/or *[alert]* must specify a type of " \
                                    + "notification. For valid notification types, see `help notify`.")


async def admin_cmd_make_role_menu(message : discord.Message, args : str, isDM : bool):
    """Create a reaction role menu, allowing users to self-assign or remove roles by adding and removing reactions.
    Each guild may have a maximum of cfg.maxRoleMenusPerGuild role menus active at any one time.
    Option reactions must be either unicode, or custom to the server where the menu is being created.

    args must contain a menu subject and new line, followed by a newline-separated list of emoji-option pairs,
    where each pair is separated with a space.
    For example: 'Number Roles\n0️⃣ @Role-1\n1️⃣ @Role-2\n2️⃣ @Role-3' will produce three options:
    - Toggling the 0️⃣ reaction will toggle user ownership of @Role-1
    - Toggling the 1️⃣ reaction will toggle user ownership of @Role-2
    - Toggling the 2️⃣ reaction will toggle user ownership of @Role-3
    Where the subject of the menu is 'Number Roles'.
    The menu subject is optional. To not provide a subject, simply start args with a new line.

    args may also optionally contain the following keyword arguments, given as argname=value
    - target         : A role or user to restrict participants by. Must be a user or role mention, not ID.
    - days           : The number of days that the menu should run for. Must be at least one, or unspecified.
    - hours          : The number of hours that the menu should run for. Must be at least one, or unspecified.
    - minutes        : The number of minutes that the menu should run for. Must be at least one, or unspecified.
    - seconds        : The number of seconds that the menu should run for. Must be at least one, or unspecified.

    Reaction menus can be forced to run forever. To do this, specify ALL run time kwargs as 'off'.

    TODO: Change options list formatting from comma separated to new line separated
    TODO: Support target IDs
    TODO: Implement single choice/grouped roles
    TODO: Change non-expiring menu specification from all kwargs 'off' to a special kwarg 'on'

    :param discord.Message message: the discord message calling the command
    :param str args: A comma-separated list of space-separated emoji-option pairs, and optionally any kwargs
                        as specified in this function's docstring
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    requestedBBGuild = botState.guildsDB.getGuild(message.guild.id)
    if requestedBBGuild.ownedRoleMenus >= cfg.maxRoleMenusPerGuild:
        await message.reply(mention_author=False, content=":x: Guilds can have at most " + str(cfg.maxRoleMenusPerGuild) + " role menus!")
        return
    requestedBBGuild.ownedRoleMenus += 1

    botRole = None
    potentialRoles = []
    for currRole in message.guild.me.roles:
        if currRole.name == message.guild.me.name and currRole.managed:
            potentialRoles.append(currRole)

    if potentialRoles == []:
        await message.reply(mention_author=False, content=":x: I can't find my '" + message.guild.me.name + "' role! Have you renamed it?")
        return
    botRole = potentialRoles[-1]

    reactionRoles = {}
    kwArgs = {}

    argsSplit = args.split("\n")
    if len(argsSplit) < 2:
        await message.reply(mention_author=False, content=":x: Invalid arguments! Please provide your menu title, followed by a new line, " \
                                    + "then a new line-separated series of options.\nFor more info, see `" \
                                    + requestedBBGuild.commandPrefix + "admin-help`")
        return
    menuSubject = argsSplit[0]
    argPos = 0

    for arg in argsSplit[1:]:
        if arg == "":
            continue
        argPos += 1
        try:
            roleStr, dumbReact = arg.strip(" ").split(" ")[1], lib.emojis.BasedEmoji.fromStr(arg.strip(" ").split(" ")[0])
        except (ValueError, IndexError):
            for kwArg in ["target=", "days=", "hours=", "seconds=", "minutes=", "multiplechoice="]:
                if arg.lower().startswith(kwArg):
                    kwArgs[kwArg[:-1]] = arg[len(kwArg):]
                    break
        # except lib.emojis.UnrecognisedCustomEmoji:
        #     await message.reply(mention_author=False, content=":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) \
        #                                 + " emoji!\nYou can only use built in emojis, or custom emojis " \
        #                                 + "that are in this server.")
        #     return
        else:
            if dumbReact.sendable == "None":
                await message.reply(mention_author=False, content=":x: I don't know your " + str(argPos) + lib.stringTyping.getNumExtension(argPos) \
                                            + " emoji!\nYou can only use built in emojis, or custom emojis that " \
                                            + "are in this server.")
                return
            if dumbReact is None:
                await message.reply(mention_author=False, content=":x: Invalid emoji: " + arg.strip(" ").split(" ")[1])
                return
            elif dumbReact.isID:
                localEmoji = False
                for localEmoji in message.guild.emojis:
                    if localEmoji.id == dumbReact.id:
                        localEmoji = True
                        break
                if not localEmoji:
                    await message.reply(mention_author=False, content=":x: I don't know your " + str(argPos) \
                                                + lib.stringTyping.getNumExtension(argPos) + " emoji!\n" \
                                                + "You can only use built in emojis, or custom emojis " \
                                                + "that are in this server.")
                    return

            if dumbReact in reactionRoles:
                await message.reply(mention_author=False, content=":x: Cannot use the same emoji for two options!")
                return


            role = message.guild.get_role(int(roleStr.lstrip("<@&").rstrip(">")))
            if role is None:
                await message.reply(mention_author=False, content=":x: Unrecognised role: " + roleStr)
                return
            elif role.position > botRole.position:
                await message.reply(mention_author=False, content=":x: I can't grant the **" + role.name + "** role!\nMake sure it's below my '" \
                                            + botRole.name + "' role in the server roles list.")
            reactionRoles[dumbReact] = role

    if len(reactionRoles) == 0:
        await message.reply(mention_author=False, content=":x: No roles given!")
        return

    targetRole = None
    targetMember = None
    if "target" in kwArgs:
        if lib.stringTyping.isRoleMention(kwArgs["target"]):
            targetRole = message.guild.get_role(int(kwArgs["target"].lstrip("<@&").rstrip(">")))
            if targetRole is None:
                await message.reply(mention_author=False, content=":x: Unknown target role!")
                return

        elif lib.stringTyping.isMention(kwArgs["target"]):
            targetMember = message.guild.get_member(int(kwArgs["target"].lstrip("<@!").rstrip(">")))
            if targetMember is None:
                await message.reply(mention_author=False, content=":x: Unknown target user!")
                return

        else:
            await message.reply(mention_author=False, content=":x: Invalid target role/user!")
            return

    timeoutDict = {}

    for timeName in ["days", "hours", "minutes", "seconds"]:
        if timeName in kwArgs:
            if kwArgs[timeName].lower() == "off":
                timeoutDict[timeName] = -1
            else:
                if not lib.stringTyping.isInt(kwArgs[timeName]) or int(kwArgs[timeName]) < 1:
                    await message.reply(mention_author=False, content=":x: Invalid number of " + timeName + " before timeout!")
                    return

                timeoutDict[timeName] = int(kwArgs[timeName])

    timeoutExists = False
    for timeName in timeoutDict:
        if timeoutDict[timeName] != -1:
            timeoutExists = True
    timeoutExists = timeoutExists or timeoutDict == {}

    menuMsg = await message.reply(mention_author=False, content="‎")

    if timeoutExists:
        timeoutDelta = timedelta(**cfg.timeouts.roleMenuExpiry if timeoutDict == {} else timeoutDict)
        timeoutTT = timedTask.TimedTask(expiryDelta=timeoutDelta, expiryFunction=reactionRolePicker.markExpiredRoleMenu,
                                        expiryFunctionArgs=menuMsg.id)
        botState.reactionMenusTTDB.scheduleTask(timeoutTT)

    else:
        timeoutTT = None

    menu = reactionRolePicker.ReactionRolePicker(menuMsg, reactionRoles, message.guild, targetRole=targetRole,
                                                    targetMember=targetMember, timeout=timeoutTT, titleTxt=menuSubject)
    await menu.updateMessage()
    botState.reactionMenusDB[menuMsg.id] = menu

botCommands.register("make-role-menu", admin_cmd_make_role_menu, 1, forceKeepArgsCasing=True,
                        signatureStr="**make-role-menu** *<title>*\n**<option1 emoji> <@option1 role>**\n" \
                                        + "...    ...\n*[kwargs]*",
                        shortHelp="Create a reaction role menu. Each option must be on its own new line, as an emoji, " \
                                    + "followed by a space, followed by a mention of the role to grant.",
                        longHelp="Create a reaction role menu. Each option must be on its own new line, as an emoji, " \
                                    + "followed by a space, followed by a mention of the role to grant. The `title` is " \
                                    + "displayed at the top of the meny and is optional, to exclude your title simply give " \
                                    + "a new line. \n__kwargs__\n- Give target=@role mention to limit use of the menu only " \
                                    + "to users with the specified role.\n- You may set expiry time for your menu, with " \
                                    + "each time division on a new line. Acceptable time divisions are: seconds, minutes, " \
                                    + "hours, days. To force the menu to never expire, give **all** time divisions as " \
                                    + "`off`.(default: minutes=5)")


async def admin_cmd_showmeHD(message : discord.Message, args : str, isDM : bool):
    """Render the attached image file onto the specified ship, in high definition.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a ship name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    if isDM:
        prefix = cfg.defaultCommandPrefix
    else:
        prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix

    # verify a item was given
    if args == "":
        await message.reply(mention_author=False, content=":x: Please provide a ship! Example: `" + prefix + "ship Groza Mk II`")
        return

    full = False
    if args.endswith("-full"):
        args = args.split("-full")[0]
        full = True

    # look up the ship object
    itemName = args.rstrip(" ").title()
    itemObj = None
    for ship in bbData.builtInShipData.values():
        shipObj = shipItem.Ship.fromDict(ship)
        if shipObj.isCalled(itemName):
            itemObj = shipObj

    # report unrecognised ship names
    if itemObj is None:
        if len(itemName) < 20:
            await message.reply(mention_author=False, content=":x: **" + itemName + "** is not in my database! :detective:")
        else:
            await message.reply(mention_author=False, content=":x: **" + itemName[0:15] + "**... is not in my database! :detective:")
        return

    shipData = bbData.builtInShipData[itemObj.name]
    if not shipData["skinnable"]:
        await message.reply(mention_author=False, content=":x: That ship is not skinnable!")
        return

    if len(botState.currentRenders) >= cfg.maxConcurrentRenders:
        await message.reply(mention_author=False, content=":x: My rendering queue is full currently. Please try this command again once someone " \
                                    + "else's render has completed.")
        return
    if itemObj.name in botState.currentRenders:
        await message.reply(mention_author=False, content=":x: Someone else is currently rendering this ship! Please use this command again once " \
                                    + "my other " + itemObj.name + " render has completed.")
        return

    botState.currentRenders.append(itemObj.name)

    if len(message.attachments) < 1:
        await message.reply(mention_author=False, content=":x: Please attach a 2048x2048 jpg to render.")
        botState.currentRenders.remove(itemObj.name)
        return
    skinFile = message.attachments[0]
    if (not skinFile.filename.lower().endswith(".jpg")) or not (skinFile.width == 2048 and skinFile.height == 2048):
        await message.reply(mention_author=False, content=":x: Please attach a 2048x2048 jpg to render.")
        botState.currentRenders.remove(itemObj.name)
        return
    try:
        await skinFile.save(CWD + os.sep + cfg.paths.rendererTempFolder + os.sep + str(message.id) + "_0.jpg")
    except (discord.HTTPException, discord.NotFound):
        await message.reply(mention_author=False, content=":x: I couldn't download your skin file. Did you delete it?")
        botState.currentRenders.remove(itemObj.name)
        return

    skinPaths = {0: CWD + os.sep + cfg.paths.rendererTempFolder + os.sep + str(message.id) + "_0.jpg"}
    disabledLayers = []

    if not full:
        layerIndices = [i for i in range(1, shipData["textureRegions"] + 1)]

        layersPickerMsg = await message.reply(mention_author=False, content="** **")
        layersPickerMenu = reactionSkinRegionPicker.ReactionSkinRegionPicker(layersPickerMsg, message.author,
                                                                                cfg.toolUseConfirmTimeoutSeconds,
                                                                                numRegions=shipData["textureRegions"])
        pickedLayers = []
        menuOutput = await layersPickerMenu.doMenu()
        if cfg.defaultEmojis.spiral in menuOutput:
            pickedLayers = layerIndices
        elif cfg.defaultEmojis.cancel in menuOutput:
            await message.reply(mention_author=False, content="🛑 Skin render cancelled.")
            for skinPath in skinPaths.values():
                os.remove(skinPath)
            botState.currentRenders.remove(itemObj.name)
            return
        else:
            for react in menuOutput:
                try:
                    pickedLayers.append(cfg.defaultEmojis.numbers.index(react))
                except ValueError:
                    pass

        remainingIndices = [i for i in layerIndices if i not in pickedLayers]

        if remainingIndices:
            disabledLayersPickerMenu = reactionSkinRegionPicker.ReactionSkinRegionPicker(layersPickerMsg, message.author,
                                                                                            cfg.toolUseConfirmTimeoutSeconds,
                                                                                            possibleRegions=remainingIndices,
                                                                                            desc="Would you like to disable" \
                                                                                                    + " any regions?")
            menuOutput = await disabledLayersPickerMenu.doMenu()
            if cfg.defaultEmojis.spiral in menuOutput:
                disabledLayers = remainingIndices
            elif cfg.defaultEmojis.cancel in menuOutput:
                await message.reply(mention_author=False, content="🛑 Skin render cancelled.")
                for skinPath in skinPaths.values():
                    os.remove(skinPath)
                botState.currentRenders.remove(itemObj.name)
                return
            else:
                for react in menuOutput:
                    try:
                        disabledLayers.append(cfg.defaultEmojis.numbers.index(react))
                    except ValueError:
                        pass

        def showmeAdditionalMessageCheck(newMessage):
            return newMessage.author is message.author and \
                    (newMessage.content.lower().startswith(prefix + "cancel") or len(newMessage.attachments) > 0)

        for regionNum in pickedLayers:
            nextLayerMsg = await message.reply(mention_author=False, content="Please send your image for texture region #" + str(regionNum) \
                                                        + ", or `" + prefix + "cancel` to cancel the render, within " \
                                                        + str(cfg.toolUseConfirmTimeoutSeconds) + " seconds.")
            try:
                imgMsg = await botState.client.wait_for("message", check=showmeAdditionalMessageCheck,
                                                        timeout=cfg.toolUseConfirmTimeoutSeconds)
            except asyncio.TimeoutError:
                await nextLayerMsg.edit(content="This menu has now expired. Please try the command again.")
            else:
                if imgMsg.content.lower().startswith(prefix + "cancel"):
                    await message.reply(mention_author=False, content="🛑 Skin render cancelled.")
                    for skinPath in skinPaths.values():
                        os.remove(skinPath)
                    botState.currentRenders.remove(itemObj.name)
                    return
                nextLayer = imgMsg.attachments[0]
                if (not nextLayer.filename.lower().endswith(".jpg")) or \
                        not (nextLayer.width == 2048 and nextLayer.height == 2048):
                    await message.reply(mention_author=False, content=":x: Please only give 2048x2048 jpgs!\n🛑 Skin render cancelled.")
                    for skinPath in skinPaths.values():
                        os.remove(skinPath)
                    botState.currentRenders.remove(itemObj.name)
                    return
                try:
                    await nextLayer.save(CWD + os.sep + cfg.paths.rendererTempFolder + os.sep + str(message.id) + "_" \
                                            + str(regionNum) + ".jpg")
                except (discord.HTTPException, discord.NotFound):
                    await message.reply(mention_author=False, content=":x: I couldn't download your skin file. Did you delete it?" \
                                                + "\n🛑 Skin render cancelled.")
                    for skinPath in skinPaths.values():
                        os.remove(skinPath)
                    botState.currentRenders.remove(itemObj.name)
                    return
                skinPaths[regionNum] = CWD + os.sep + cfg.paths.rendererTempFolder + os.sep + str(message.id) + "_" \
                                        + str(regionNum) + ".jpg"

    waitMsg = await message.reply(mention_author=False, content="🤖 Render started! I'll ping you when I'm done.")

    renderPath = shipData["path"] + os.sep + "skins" + os.sep + str(message.id) + "-RENDER.png"
    outSkinPath = shipData["path"] + os.sep + "skins" + os.sep + str(message.id) + ".jpg"

    await lib.discordUtil.startLongProcess(waitMsg)
    try:
        await shipRenderer.renderShip(str(message.id), shipData["path"], shipData["model"], skinPaths, disabledLayers,
                                        cfg.skinRenderShowmeHDResolution[0], cfg.skinRenderShowmeHDResolution[1], full=full)
    except shipRenderer.RenderFailed:
        await message.reply("🥺 Render failed! The error has been logged, please try a different ship.",
                            mention_author=True)
        botState.logger.log("Main", "admin_cmd_showmeHD", "HD ship render failed with args: '" + args + "'")
    else:
        with open(renderPath, "rb") as f:
            imageEmbedMsg = await botState.client.get_channel(cfg.showmeSkinRendersChannel).send("HD-u" \
                                                                + str(message.author.id) + "g" \
                                                                + ("DM" if isDM else \
                                                                    str(message.guild.id)) + "c" + str(message.channel.id) \
                                                                + "m" + str(message.id), file=discord.File(f))
            renderEmbed = lib.discordUtil.makeEmbed(col=discord.Colour.random(), img=imageEmbedMsg.attachments[0].url,
                                                    authorName="Skin Render Complete!",
                                                    icon=robotIcon, footerTxt="Custom skinned " + itemObj.name.capitalize())
            await message.reply(embed=renderEmbed, mention_author=True)

    botState.currentRenders.remove(itemObj.name)

    try:
        os.remove(renderPath)
    except FileNotFoundError:
        pass

    for skinPath in skinPaths.values():
        os.remove(skinPath)

    try:
        os.remove(outSkinPath)
    except FileNotFoundError:
        pass

    await lib.discordUtil.endLongProcess(waitMsg)
    return


botCommands.register("showmehd", admin_cmd_showmeHD, 1, allowDM=False, signatureStr="**showmeHD <ship-name>** *[-full]*",
                        shortHelp="Render your specified ship with the given skin, in full HD 1080p! " \
                                    + "⚠ WARNING: THIS WILL TAKE A LONG TIME.",
                        longHelp="You must attach a 2048x2048 jpg to your message. Render your specified ship with the " \
                                    + "given skin, in full HD 1080p! ⚠ WARNING: THIS WILL TAKE A LONG TIME. Give `-full` " \
                                    + "to disable autoskin and render exactly your provided image, " \
                                    + "with no additional texturing.")
botCommands.register("showmehd", admin_cmd_showmeHD, 2, allowDM=True, signatureStr="**showmeHD <ship-name>** *[-full]*",
                        shortHelp="Render your specified ship with the given skin, in full HD 1080p! " \
                                    + "⚠ WARNING: THIS WILL TAKE A LONG TIME.",
                        longHelp="You must attach a 2048x2048 jpg to your message. Render your specified ship with the " \
                                    + "given skin, in full HD 1080p! ⚠ WARNING: THIS WILL TAKE A LONG TIME. Give `-full` " \
                                    + "to disable autoskin and render exactly your provided image, " \
                                    + "with no additional texturing.")
