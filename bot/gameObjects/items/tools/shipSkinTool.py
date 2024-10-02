from __future__ import annotations
from . import toolItem
from .... import lib
from ....lib import gameMaths
from ....cfg import cfg, bbData
from ...shipSkin import ShipSkin
from ..shipItem import Ship
from discord import Message
from .... import botState
from ..gameItem import spawnableItem
from ....reactionMenus.confirmationReactionMenu import InlineConfirmationMenu


@spawnableItem
class ShipSkinTool(toolItem.ToolItem):
    """A tool that can be used to apply a skin to a ship.
    This item is named after the skin it applies.
    The manufacturer is set to the skin designer.
    This tool is single use. If a calling user is given, the tool is removed from that user's inventory after use.
    """
    def __init__(self, skin : ShipSkin, value : int = 0, wiki : str = "", icon : str = cfg.defaultShipSkinToolIcon,
            emoji : lib.emojis.BasedEmoji = None, techLevel : int = -1, builtIn : bool = False):
        """
        :param shipSkin shipSkin: The skin that this tool applies.
        :param int value: The number of credits that this item can be bought/sold for at a shop. (Default 0)
        :param str wiki: A web page that is displayed as the wiki page for this item. If no wiki is given and shipSkin
                            has one, that will be used instead. (Default "")
        :param str icon: A URL pointing to an image to use for this item's icon (Default cfg.defaultShipSkinToolIcon)
        :param lib.emojis.BasedEmoji emoji: The emoji to use for this item's small icon
                                            (Default cfg.defaultEmojis.shipSkinTool)
        :param int techLevel: A rating from 1 to 10 of this item's technical advancement. Used as a measure for its
                                effectiveness compared to other items of the same type (Default shipSkin.averageTL)
        :param bool builtIn: Whether this is a BountyBot standard item (loaded in from bbData) or a custom spawned
                                item (Default False)
        """
        if emoji is None:
            emoji = cfg.defaultEmojis.shipSkinTool
        super().__init__(lib.stringTyping.shipSkinNameToToolName(skin.name.title()), [skin.name, "Skin: " + skin.name,
                            "Ship Skin " + skin.name + "Skin " + skin.name], value=value,
                            wiki=wiki if wiki else skin.wiki if skin.hasWiki else "",
                            manufacturer=skin.designer, icon=icon, emoji=emoji,
                            techLevel=techLevel if techLevel > -1 else skin.averageTL, builtIn=builtIn)
        self.skin = skin


    async def use(self, *args, **kwargs):
        """Apply the skin to the given ship.
        After use, the tool will be removed from callingBUser's inventory. To disable this, pass callingBUser as None.
        """
        if "ship" not in kwargs:
            raise NameError("Required kwarg not given: ship")
        if not isinstance(kwargs["ship"], Ship):
            raise TypeError("Required kwarg is of the wrong type. Expected bbShip, received " \
                            + type(kwargs["ship"]).__name__)
        if "callingBUser" not in kwargs:
            raise NameError("Required kwarg not given: callingBUser")
        if kwargs["callingBUser"] is not None and type(kwargs["callingBUser"]).__name__ != "BasedUser":
            raise TypeError("Required kwarg is of the wrong type. Expected BasedUser or None, received " \
                            + type(kwargs["callingBUser"]).__name__)

        ship, callingBUser = kwargs["ship"], kwargs["callingBUser"]

        if not callingBUser.ownsShip(ship):
            raise RuntimeError("User '" + str(callingBUser.id) \
                                + "' attempted to skin a ship that does not belong to them: " \
                                + ship.getNameAndNick())

        if ship.isSkinned:
            return ValueError("Attempted to apply a skin to an already-skinned ship")
        if ship.name not in self.skin.compatibleShips:
            return TypeError("The given skin is not compatible with this ship")

        ship.applySkin(self.skin)
        if self in callingBUser.inactiveTools:
            callingBUser.inactiveTools.removeItem(self)


    async def userFriendlyUse(self, message : Message, *args, **kwargs) -> str:
        """Apply the skin to the given ship.
        After use, the tool will be removed from callingBUser's inventory. To disable this, pass callingBUser as None.

        :param Message message: The discord message that triggered this tool use
        :return: A user-friendly message summarising the result of the tool use.
        :rtype: str
        """
        if "ship" not in kwargs:
            raise NameError("Required kwarg not given: ship")
        if not isinstance(kwargs["ship"], Ship):
            raise TypeError("Required kwarg is of the wrong type. Expected bbShip, received " \
                            + type(kwargs["ship"]).__name__)
        if "callingBUser" not in kwargs:
            raise NameError("Required kwarg not given: callingBUser")

        # converted to soft type check due to circular import
        """if (not isinstance(kwargs["callingBUser"], BasedUser)) and kwargs["callingBUser"] is not None:
            raise TypeError("Required kwarg is of the wrong type. Expected BasedUser or None, received " \
                            + type(kwargs["callingBUser"]).__name__)"""
        if (type(kwargs["callingBUser"]).__name__ != "BasedUser") and kwargs["callingBUser"] is not None:
            raise TypeError("Required kwarg is of the wrong type. Expected BasedUser or None, received " \
                            + type(kwargs["callingBUser"]).__name__)

        ship, callingBUser = kwargs["ship"], kwargs["callingBUser"]

        if not callingBUser.ownsShip(ship):
            raise RuntimeError("User '" + str(callingBUser.id) \
                                + "' attempted to skin a ship that does not belong to them: " \
                                + ship.getNameAndNick())

        if ship.isSkinned:
            return ":x: This ship already has a skin applied! Please equip a different ship."
        if ship.name not in self.skin.compatibleShips:
            try:
                message.guild
            except AttributeError:
                prefix = cfg.defaultCommandPrefix
            else:
                prefix = botState.guildsDB.getGuild(message.guild.id).commandPrefix
            return ":x: Your ship is not compatible with this skin! Please equip a different ship, or use `" \
                    + prefix + "info skin " + self.name + "` to see what ships are compatible with this skin."

        callingBUser = kwargs["callingBUser"]
        confirmMsg = await message.reply(mention_author=False, content="Are you sure you want to apply the " + self.skin.name \
                                                + " skin to your " + ship.getNameAndNick() + "?")
        confirmation = await InlineConfirmationMenu(confirmMsg, message.author,
                                                    cfg.toolUseConfirmTimeoutSeconds).doMenu()

        if cfg.defaultEmojis.reject in confirmation:
            return "🛑 Skin application cancelled."
        elif cfg.defaultEmojis.accept in confirmation:
            ship.applySkin(self.skin)
            if self in callingBUser.inactiveTools:
                callingBUser.inactiveTools.removeItem(self)

            return "🎨 Success! Your skin has been applied."


    def statsStringShort(self) -> str:
        """Summarise all the statistics and functionality of this item as a string.

        :return: A string summarising the statistics and functionality of this item
        :rtype: str
        """
        try:
            return "*Designer: " + botState.client.get_user(self.manufacturer).name + "*"
        except AttributeError:
            return "*Designer: user #" + str(self.manufacturer) + "*"


    def toDict(self, **kwargs):
        """

        :param bool saveType: When true, include the string name of the object type in the output.
        """
        data = super().toDict(**kwargs)
        if self.builtIn:
            data["name"] = self.skin.name
        else:
            data["skin"] = self.skin.toDict(**kwargs)
        return data
        # raise RuntimeError("Attempted to save a non-builtIn shipSkinTool")


    @classmethod
    def fromDict(cls, toolDict : dict, **kwargs) -> ShipSkinTool:
        """Construct a shipSkinTool from its dictionary-serialized representation.

        :param dict toolDict: A dictionary containing all information needed to construct the required shipSkinTool.
                                Critically, a name and builtIn specifier.
        :return: A new shipSkinTool object as described in toolDict
        :rtype: shipSkinTool
        """
        if toolDict["builtIn"]:
            return bbData.builtInToolObjs[lib.stringTyping.shipSkinNameToToolName(toolDict["name"])]
        else:
            skin = ShipSkin.fromDict(toolDict["skin"])
            return ShipSkinTool(skin, value=gameMaths.shipSkinValueForTL(skin.averageTL), builtIn=False)
