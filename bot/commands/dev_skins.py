import discord

from . import commandsDB as botCommands
from ..cfg import cfg, bbData
from ..gameObjects.items import shipItem
from .. import lib, botState


botCommands.addHelpSection(2, "skins")


async def dev_cmd_addSkin(message : discord.Message, args : str, isDM : bool):
    """Make the specified ship compatible with the specified skin.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a ship name and a skin, prefaced with a + character.
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a item was given
    if args == "":
        if isDM:
            prefix = cfg.defaultCommandPrefix
        else:
            prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix
        await message.reply(mention_author=False, content=":x: Please provide a ship! Example: `" + prefix + "ship Groza Mk II`")
        return

    if "+" in args:
        if len(args.split("+")) > 2:
            await message.reply(mention_author=False, content=":x: Please only provide one skin, with one `+`!")
            return
        args, skin = args.split("+")
    else:
        skin = ""

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

    if skin != "":
        skin = skin.lstrip(" ").lower()
        if skin not in bbData.builtInShipSkins:
            if len(skin) < 20:
                await message.reply(mention_author=False, content=":x: The **" + skin + "** skin is not in my database! :detective:")
            else:
                await message.reply(mention_author=False, content=":x: The **" + skin[0:15] + "**... skin is not in my database! :detective:")

        elif skin in bbData.builtInShipData[itemObj.name]["compatibleSkins"]:
            await message.reply(mention_author=False, content=":x: That skin is already compatible with the **" + itemObj.name + "**!")

        else:
            await lib.discordUtil.startLongProcess(message)
            await bbData.builtInShipSkins[skin].addShip(itemObj.name, botState.client.skinStorageChannel)
            await lib.discordUtil.endLongProcess(message)
            await message.reply(mention_author=False, content="Done!")

    else:
        await message.reply(mention_author=False, content=":x: Please provide a skin, prefaced by a `+`!")

botCommands.register("addSkin", dev_cmd_addSkin, 2, helpSection="skins", useDoc=True)


async def dev_cmd_delSkin(message : discord.Message, args : str, isDM : bool):
    """Remove the specified ship's compatibility with the specified skin.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a ship name and a skin, prefaced with a + character.
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a item was given
    if args == "":
        if isDM:
            prefix = cfg.defaultCommandPrefix
        else:
            prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix
        await message.reply(mention_author=False, content=":x: Please provide a ship! Example: `" + prefix + "ship Groza Mk II`")
        return

    if "+" in args:
        if len(args.split("+")) > 2:
            await message.reply(mention_author=False, content=":x: Please only provide one skin, with one `+`!")
            return
        args, skin = args.split("+")
    else:
        skin = ""

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

    if skin != "":
        skin = skin.lstrip(" ").lower()
        if skin not in bbData.builtInShipSkins:
            if len(skin) < 20:
                await message.reply(mention_author=False, content=":x: The **" + skin + "** skin is not in my database! :detective:")
            else:
                await message.reply(mention_author=False, content=":x: The **" + skin[0:15] + "**... skin is not in my database! :detective:")

        elif skin not in bbData.builtInShipData[itemObj.name]["compatibleSkins"]:
            await message.reply(mention_author=False, content=":x: That skin is already incompatible with the **" + itemObj.name + "**!")

        else:
            await bbData.builtInShipSkins[skin].removeShip(itemObj.name, botState.client.skinStorageChannel)
            await message.reply(mention_author=False, content="Done!")

    else:
        await message.reply(mention_author=False, content=":x: Please provide a skin, prefaced by a `+`!")

botCommands.register("delSkin", dev_cmd_delSkin, 2, helpSection="skins", useDoc=True)


async def dev_cmd_makeSkin(message : discord.Message, args : str, isDM : bool):
    """Make the specified ship compatible with the specified skin.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a ship name and a skin, prefaced with a + character.
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a item was given
    if args == "":
        if isDM:
            prefix = cfg.defaultCommandPrefix
        else:
            prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix
        await message.reply(mention_author=False, content=":x: Please provide a ship! Example: `" + prefix + "ship Groza Mk II`")
        return

    if "+" in args:
        if len(args.split("+")) > 2:
            await message.reply(mention_author=False, content=":x: Please only provide one skin, with one `+`!")
            return
        args, skin = args.split("+")
    else:
        skin = ""

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

    if skin != "":
        skin = skin.lstrip(" ").lower()
        if skin not in bbData.builtInShipSkins:
            if len(skin) < 20:
                await message.reply(mention_author=False, content=":x: The **" + skin + "** skin is not in my database! :detective:")
            else:
                await message.reply(mention_author=False, content=":x: The **" + skin[0:15] + "**... skin is not in my database! :detective:")

        elif skin in bbData.builtInShipData[itemObj.name]["compatibleSkins"]:
            await message.reply(mention_author=False, content=":x: That skin is already compatible with the **" + itemObj.name + "**!")

        else:
            await bbData.builtInShipSkins[skin].addShip(itemObj.name, botState.client.skinStorageChannel)
            await message.reply(mention_author=False, content="Done!")

    else:
        await message.reply(mention_author=False, content=":x: Please provide a skin, prefaced by a `+`!")

botCommands.register("makeSkin", dev_cmd_makeSkin, 2, helpSection="skins", useDoc=True)


async def dev_cmd_applySkin(message : discord.Message, args : str, isDM : bool):
    """Apply the specified ship skin to the equipped ship.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a skin name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a item was given
    if args == "":
        await message.reply(mention_author=False, content=":x: Please provide a skin!")
        return

    activeShip = botState.usersDB.getOrAddID(message.author.id).activeShip
    if activeShip.isSkinned:
        await message.reply(mention_author=False, content=":x: Your ship already has a skin applied!")
        return

    if args != "":
        skin = args.lower()
        if skin not in bbData.builtInShipSkins:
            if len(skin) < 20:
                await message.reply(mention_author=False, content=":x: The **" + skin + "** skin is not in my database! :detective:")
            else:
                await message.reply(mention_author=False, content=":x: The **" + skin[0:15] + "**... skin is not in my database! :detective:")

        elif skin not in bbData.builtInShipData[activeShip.name]["compatibleSkins"]:
            await message.reply(mention_author=False, content=":x: That skin is incompatible with your active ship! (" + activeShip.name + ")")

        else:
            activeShip.applySkin(bbData.builtInShipSkins[skin])
            await message.reply(mention_author=False, content="Done!")

botCommands.register("applySkin", dev_cmd_applySkin, 2, helpSection="skins", useDoc=True)


async def dev_cmd_unapplySkin(message : discord.Message, args : str, isDM : bool):
    """Remove the applied skin from the active ship.

    :param discord.Message message: the discord message calling the command
    :param str args: ignored
    :param bool isDM: Whether or not the command is being called from a DM channel
    """

    activeShip = botState.usersDB.getOrAddID(message.author.id).activeShip
    if not activeShip.isSkinned:
        await message.reply(mention_author=False, content=":x: Your ship has no skin applied!")
    elif not activeShip.builtIn:
        await message.reply(mention_author=False, content=":x: Your ship is not built in, so the original icon cannot be recovered.")
    else:
        activeShip.icon = bbData.builtInShipData[activeShip.name]["icon"]
        activeShip.skin = ""
        activeShip.isSkinned = False
        await message.reply(mention_author=False, content="Done!")

botCommands.register("unApplySkin", dev_cmd_unapplySkin, 2, helpSection="skins", useDoc=True)


async def dev_cmd_add_skin_to_all_ships(message : discord.Message, args : str, isDM : bool):
    """Make all ships in the game compatible with the specified skin.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a skin name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a item was given
    if args == "":
        await message.reply(mention_author=False, content=":x: Please provide a skin!")
        return

    skin = args.strip(" ").lower()
    if skin not in bbData.builtInShipSkins:
        if len(skin) < 20:
            await message.reply(mention_author=False, content=":x: The **" + skin + "** skin is not in my database! :detective:")
        else:
            await message.reply(mention_author=False, content=":x: The **" + skin[0:15] + "**... skin is not in my database! :detective:")

    await lib.discordUtil.startLongProcess(message)

    for shipName in bbData.builtInShipData:
        if skin not in bbData.builtInShipData[shipName]["compatibleSkins"]:
            await bbData.builtInShipSkins[skin].addShip(shipName, )

    await lib.discordUtil.endLongProcess(message)
    await message.reply(mention_author=False, content="Done!")

botCommands.register("add-skin-to-all-ships", dev_cmd_add_skin_to_all_ships, 2, helpSection="skins", useDoc=True)


async def dev_cmd_del_skin_from_all_ships(message : discord.Message, args : str, isDM : bool):
    """Make all ships in the game incompatible with the specified skin.

    :param discord.Message message: the discord message calling the command
    :param str args: string containing a skin name
    :param bool isDM: Whether or not the command is being called from a DM channel
    """
    # verify a item was given
    if args == "":
        await message.reply(mention_author=False, content=":x: Please provide a skin!")
        return

    skin = args.strip(" ").lower()
    if skin not in bbData.builtInShipSkins:
        if len(skin) < 20:
            await message.reply(mention_author=False, content=":x: The **" + skin + "** skin is not in my database! :detective:")
        else:
            await message.reply(mention_author=False, content=":x: The **" + skin[0:15] + "**... skin is not in my database! :detective:")

    await lib.discordUtil.startLongProcess(message)

    for shipName in bbData.builtInShipData:
        if skin in bbData.builtInShipData[shipName]["compatibleSkins"]:
            await bbData.builtInShipSkins[skin].removeShip(shipName, botState.client.skinStorageChannel)

    await lib.discordUtil.endLongProcess(message)
    await message.reply(mention_author=False, content="Done!")

botCommands.register("del-skin-from-all-ships", dev_cmd_del_skin_from_all_ships, 2, helpSection="skins", useDoc=True)
