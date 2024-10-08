from ..cfg import bbData, cfg
import os
from ..shipRenderer import shipRenderer
from .. import lib
from discord import File
from typing import Dict
from ..baseClasses import serializable


def _saveShip(ship):
    shipData = bbData.builtInShipData[ship]
    shipTL = shipData["techLevel"]
    shipPath = shipData["path"]
    del shipData["techLevel"]
    del shipData["path"]
    shipData["builtIn"] = False
    lib.jsonHandler.writeJSON(shipPath + os.sep + "META.json", shipData, prettyPrint=True)
    shipData["builtIn"] = True
    shipData["techLevel"] = shipTL
    shipData["saveDue"] = False
    shipData["path"] = shipPath


class ShipSkin(serializable.Serializable):
    def __init__(self, name : str, textureRegions : int, shipRenders : Dict[str, str],
                    path : str, designer : str, wiki : str = ""):
        self.name = name
        self.textureRegions = textureRegions
        self.compatibleShips = list(shipRenders.keys())
        self.shipRenders = shipRenders
        self.path = path
        if len(self.compatibleShips) > 0:
            self.averageTL = 0
            for ship in self.compatibleShips:
                self.averageTL += bbData.builtInShipData[ship]["techLevel"]
            self.averageTL = int(self.averageTL / len(self.compatibleShips))
        else:
            self.averageTL = -1
        self.designer = designer
        self.wiki = wiki
        self.hasWiki = wiki != ""


    def toDict(self, **kwargs) -> dict:
        data = {    "name": self.name, "textureRegions": self.textureRegions,
                    "ships": self.shipRenders, "designer": self.designer}
        if self.hasWiki:
            data["wiki"] = self.wiki
        return data


    def _save(self, **kwargs):
        lib.jsonHandler.writeJSON(self.path + os.sep + "META.json", self.toDict(**kwargs), prettyPrint=True)


    async def addShip(self, ship, rendersChannel):
        if ship not in bbData.builtInShipData:
            raise KeyError("Ship not found: '" + str(ship) + "'")

        shipData = bbData.builtInShipData[ship]

        if not shipData["skinnable"]:
            raise ValueError("Attempted to render a skin onto an non-skinnable ship: '" + str(ship) + "'")

        if ship not in self.shipRenders:
            _outputSkinFile = shipData["path"] + os.sep + "skins" + os.sep + self.name
            renderPath = _outputSkinFile + "-RENDER.png"
            # emojiRenderPath = _outputSkinFile + "_emoji-RENDER.png"
            texPath = _outputSkinFile + ".jpg"
            # emojiTexPath = _outputSkinFile + "_emoji.jpg"

            # if not os.path.isfile(renderPath):
            textureFiles = {0: self.path + os.sep + "1.jpg"}
            for i in range(self.textureRegions):
                textureFiles[i  +1] = self.path + os.sep + str(i + 2) + ".jpg"
            await shipRenderer.renderShip(self.name, shipData["path"], shipData["model"], textureFiles, [],
                                            cfg.skinRenderIconResolution[0], cfg.skinRenderIconResolution[1],
                                            cfg.skinRenderIconSamples)

            # == Scrapped code for creating custom emojis for each ship reskin ==
            # await shipRenderer.renderShip(self.name + "_emoji", shipData["path"], shipData["model"], [texPath],
            #                               cfg.skinRenderEmojiResolution[0], cfg.skinRenderEmojiResolution[1])
            # os.remove(emojiTexPath)

            # with open(emojiRenderPath, "rb") as f:
            #     newEmoji = await rendersChannel.guild.create_custom_emoji(name=ship + "_+" + self.name, image=f.read(),
            #                                                               reason="New skin '" + self.name \
            #                                                                       + "' registered for ship '" + ship + "'")

            with open(renderPath, "rb") as f:
                renderMsg = await rendersChannel.send(ship + " +" + self.name, file=File(f))
                # If saving emoji renders of skins, also save the emoji in here: str(newEmoji)
                self.shipRenders[ship] = [renderMsg.attachments[0].url, renderMsg.id]
            os.remove(renderPath)
            os.remove(texPath)

        if ship not in self.compatibleShips:
            self.compatibleShips.append(ship)

        if self.name not in shipData["compatibleSkins"]:
            shipData["compatibleSkins"].append(self.name.lower())

        _saveShip(ship)
        self._save()


    async def removeShip(self, ship, rendersChannel):
        if ship not in bbData.builtInShipData:
            raise KeyError("Ship not found: '" + str(ship) + "'")

        shipData = bbData.builtInShipData[ship]

        if ship in self.compatibleShips:
            self.compatibleShips.remove(ship)

        if self.name in shipData["compatibleSkins"]:
            try:
                os.remove(shipData["path"] + os.sep + "skins" + os.sep + self.name + ".png")
            except FileNotFoundError:
                pass
            shipData["compatibleSkins"].remove(self.name.lower())

        if ship in self.shipRenders:
            # renderMsg = await rendersChannel.fetch_message(self.shipRenders[ship][1])
            # await renderMsg.delete()
            del self.shipRenders[ship]

        _saveShip(ship)
        self._save()


    @classmethod
    def fromDict(cls, skinDict: dict, **kwargs):
        if skinDict["name"] in bbData.builtInShipSkins:
            return bbData.builtInShipSkins[skinDict["name"]]
        return ShipSkin(**cls._makeDefaults(skinDict, ignores=("ships","disabledRegions"), shipRenders=skinDict["ships"]))
