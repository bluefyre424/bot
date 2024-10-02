from . import moduleItem
from ....cfg import bbData
from .... import lib
from typing import List
from ..gameItem import spawnableItem


@spawnableItem
class EmergencySystemModule(moduleItem.ModuleItem):
    """"A module providing a ship with a short period of invincibility just before dying

    :var duration: The number of seconds the effect is active for
    :vartype duration: float
    """

    def __init__(self, name : str, aliases : List[str], duration : int = 0, value : int = 0,
            wiki : str = "", manufacturer : str = "", icon : str = "",
            emoji : lib.emojis.BasedEmoji = lib.emojis.BasedEmoji.EMPTY, techLevel : int = -1,
            builtIn : bool = False):
        """
        :param str name: The name of the module. Must be unique.
        :param list[str] aliases: Alternative names by which this module may be referred to
        :param int duration: The number of seconds the effect is active for (Default 0)
        :param int value: The number of credits this module may be sold or bought or at a shop (Default 0)
        :param str wiki: A web page that is displayed as the wiki page for this module. (Default "")
        :param str manufacturer: The name of the manufacturer of this module (Default "")
        :param str icon: A URL pointing to an image to use for this module's icon (Default "")
        :param lib.emojis.BasedEmoji emoji: The emoji to use for the module's small icon (Default lib.emojis.BasedEmoji.EMPTY)
        :param int techLevel: A rating from 1 to 10 of this item's technical advancement. Used as a measure for
                                its effectiveness compared to other modules of the same type (Default -1)
        :param bool builtIn: Whether this is a BountyBot standard module (loaded in from bbData) or a
                                custom spawned module (Default False)
        """
        super(EmergencySystemModule, self).__init__(name, aliases, value=value, wiki=wiki, manufacturer=manufacturer,
                                                    icon=icon, emoji=emoji, techLevel=techLevel, builtIn=builtIn)

        self.duration = duration


    def statsStringShort(self):
        return "*Duration: " + moduleItem.lib.stringTyping.lib.stringTyping.formatAdditive(self.duration) + "s*"


    def toDict(self, **kwargs) -> dict:
        """Serialize this module into dictionary format, to be saved to file. Uses the base moduleItem
        toDict method as a starting point, and adds extra attributes implemented by this specific module.

        :return: A dictionary containing all information needed to reconstruct this module
        :rtype: dict
        """
        itemDict = super(EmergencySystemModule, self).toDict(**kwargs)
        if not self.builtIn:
            itemDict["duration"] = self.duration
        return itemDict


    @classmethod
    def fromDict(cls, moduleDict : dict, **kwargs):
        """Factory function building a new module object from the information in the provided dictionary.
        The opposite of this class's toDict function.

        :param moduleDict: A dictionary containing all information needed to construct the requested module
        :return: The new module object as described in moduleDict
        :rtype: dict
        """
        if moduleDict.get("builtIn", False):
            return bbData.builtInModuleObjs[moduleDict["name"]]

        return EmergencySystemModule(**cls._makeDefaults(moduleDict, ignores=("type",),
                                                emoji=lib.emojis.BasedEmoji.fromStr(moduleDict["emoji"]) \
                                                        if "emoji" in moduleDict else lib.emojis.BasedEmoji.EMPTY))
