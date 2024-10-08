from . import reactionMenu
from ..cfg import cfg
from discord import Message, User, Member, Colour
from typing import Union, List


class ReactionSkinRegionPicker(reactionMenu.SingleUserReactionMenu):
    """An unsaveable menu allowing users to choose autoskin layer indices that they want to provide.
    """
    def __init__(self, msg : Message, owningUser : Union[User, Member], timeoutSeconds : int,
                    numRegions : int = 0, possibleRegions : List[int] = [], titleTxt : str = "",
                    desc : str = "", col : Colour = Colour.blue(), footerTxt : str = "", img : str = "",
                    thumb : str = "", icon : str = cfg.defaultShipSkinToolIcon, authorName : str = ""):
        """
        :param discord.Message msg: the message where this menu is embedded
        :param owningUser: The user choosing skin layers
        :type owningUser: discord.Member or discord.User
        :param int timeoutSeconds: The number of seconds that this menu should last before timing out
        :param int numRegions: The number of optional texture regions to choose from. If zero, use possibleRegions (default 0)
        :param List[int] possibleRegions: List of selectable region numbers. If [], use numRegions. (default [])
        :param str titleTxt: The content of the embed title (Default "")
        :param str desc: he content of the embed description; appears at the top below the title (Default "")
        :param discord.Colour col: The colour of the embed's side strip (Default None)
        :param str footerTxt: Secondary description appearing in darker font at the bottom of the embed
                                (Default time until menu expiry if timeout is not None, "" otherwise)
        :param str img: URL to a large icon appearing as the content of the embed, left aligned like a field (Default "")
        :param str thumb: URL to a larger image appearing to the right of the title (Default "")
        :param str icon: URL to a smaller image to the left of authorName. AuthorName is required for this to be displayed.
                            (Default "")
        :param str authorName: Secondary, smaller title for the embed (Default "")
        """

        if not possibleRegions:
            if numRegions > len(cfg.defaultEmojis.numbers) - 2:
                raise IndexError("Attempted to create a ReactionSkinRegionPicker choosing from more regions than can can be" \
                                    + " represented by cfg.ReactionSkinRegionPicker")
            if numRegions < 1:
                raise IndexError("Attempted to create a ReactionSkinRegionPicker choosing from fewer than one regions, and" \
                                    + " possibleRegions not provided/empty")
        else:
            if numRegions < 0:
                raise IndexError("Attempted to create a ReactionSkinRegionPicker choosing from fewer than zero regions," \
                                    + " possibleRegions not provided")

        if desc == "":
            desc = "This ship has **" + str(numRegions) + "** optional texture region" + ("" if numRegions == 1 else "s") \
                    + ".\nWhich regions would you like to change?"
        if not titleTxt:
            titleTxt = "Custom Skin Renderer"


        regionOptions = {cfg.defaultEmojis.spiral: reactionMenu.DummyReactionMenuOption("Select all",
                                                                                        cfg.defaultEmojis.spiral)}
        for regionNumber in (possibleRegions if possibleRegions else range(1, numRegions + 1)):
            layerOption = reactionMenu.DummyReactionMenuOption("Layer " + str(regionNumber),
                                                                cfg.defaultEmojis.numbers[regionNumber])
            regionOptions[cfg.defaultEmojis.numbers[regionNumber]] = layerOption

        regionOptions[cfg.defaultEmojis.submit] = reactionMenu.DummyReactionMenuOption("Submit", cfg.defaultEmojis.submit)
        regionOptions[cfg.defaultEmojis.cancel] = reactionMenu.DummyReactionMenuOption("Cancel render",
                                                                                        cfg.defaultEmojis.cancel)

        super(ReactionSkinRegionPicker, self).__init__(msg, owningUser, timeoutSeconds,
                                                        returnTriggers=[    cfg.defaultEmojis.spiral,
                                                                            cfg.defaultEmojis.submit,
                                                                            cfg.defaultEmojis.cancel],
                                                        options=regionOptions, titleTxt=titleTxt, desc=desc, col=col,
                                                        footerTxt=footerTxt, img=img, thumb=thumb, icon=icon,
                                                        authorName=authorName)
        self.saveable = False
