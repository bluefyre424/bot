# Typing imports
from __future__ import annotations

from ..baseClasses import serializable

from typing import Union, TYPE_CHECKING
if TYPE_CHECKING:
    from ..gameObjects.battles import duelRequest

from ..gameObjects.items import shipItem, moduleItemFactory
from ..gameObjects.items.weapons import primaryWeapon, turretWeapon
from ..gameObjects.items.tools import toolItemFactory, toolItem
from ..gameObjects.items.modules import moduleItem
from ..cfg import cfg
from ..gameObjects.inventories import inventory
from ..userAlerts import userAlerts
from datetime import datetime, timedelta
from discord import Guild, Member
from ..users import basedGuild
from .. import lib, botState


# Dictionary-serialized shipItem to give to new players
defaultShipLoadoutDict = {"name": "Betty", "builtIn": True,
                        "weapons": [{"name": "Micro Gun MK I", "builtIn": True}],
                        "modules": [{"name": "Telta Quickscan", "builtIn": True},
                                    {"name": "E2 Exoclad", "builtIn": True},
                                    {"name": "IMT Extract 1.3", "builtIn": True}]}

# Default attributes to give to new players
defaultUserDict = {"credits": 0, "bountyCooldownEnd": 0, "lifetimeBountyCreditsWon": 0, "systemsChecked": 0, "bountyWins": 0,
                    "activeShip": defaultShipLoadoutDict,
                    "inactiveWeapons": [{"item": {"name": "Nirai Impulse EX 1", "builtIn": True}, "count": 1}]}
# Reference value not pre-calculated from defaultUserDict. This is not used in the game's code,
# but provides a reference for game design.
defaultUserValue = 28970


class BasedUser(serializable.Serializable):
    """A user of the bot. There is currently no guarantee that user still shares any guilds with the bot,
    though this is planned to change in the future.

    TODO: Consider moving alert methods (e.g setAlertByType) to userAlerts.py

    :var id: The user's unique ID. The same as their unique discord ID.
    :vartype id: int
    :var credits: The amount of credits (currency) this user has
    :vartype credits: int
    :var lifetimeBountyCreditsWon: The total amount of credits this user has earned through hunting bounties
    :vartype lifetimeBountyCreditsWon: int
    :var bountyCooldownEnd: A utc timestamp representing when the user's cmd_check cooldown is due to expire
    :vartype bountyCooldownEnd: float
    :var systemsChecked: The total number of space systems this user has checked
    :vartype systemsChecked: int
    :var bountyWins: The total number of bounties this user has won
    :vartype bountyWins: int
    :var activeShip: The user's currently equipped shipItem
    :vartype activeShip: shipItem
    :var inactiveShips: The shipItems currently in this user's inventory (unequipped)
    :vartype inactiveShips: inventory
    :var inactiveModules: The moduleItems currently in this user's inventory (unequipped)
    :vartype inactiveModules: inventory
    :var inactiveWeapons: The primaryWeapons currently in this user's inventory (unequipped)
    :vartype inactiveWeapons: inventory
    :var inactiveTurrets: The turretWeapons currently in this user's inventory (unequipped)
    :vartype inactiveTurrets: inventory
    :var inactiveTools: the toolItems currently in this user's inventory
    :vartype inactiveTools: inventory
    :var lastSeenGuildId: The ID of the guild where this user was last active. Not guaranteed to be present.
    :vartype lastSeenGuildId: int
    :var hasLastSeenGuildId: Whether or not the user currently has a lastSeenGuildId
    :vartype hasLastSeenGuildId: bool
    :var duelRequests: A dictionary mapping target BasedUser objects to DuelRequest objects.
                        Only contains duel requests issued by this user.
    :vartype duelRequests: dict[BasedUser, DuelRequest]
    :var duelWins: The total number of duels the user has won
    :vartype duelWins: int
    :var duelLosses: The total number of duels the user has lost
    :vartype duelLosses: int
    :var duelCreditsWins: The total amount of credits the user has won through fighting duels
    :vartype duelCreditsWins: int
    :var duelCreditsLosses: The total amount of credits the user has lost through fighting duels
    :vartype duelCreditsLosses: int
    :var userAlerts: A dictionary mapping userAlerts.UABase subtypes to instances of that subtype
    :vartype userAlerts: dict[type, userAlerts.UABase]
    :var bountyWinsToday: The number of bounties the user has won today
    :vartype bountyWinsToday: int
    :var dailyBountyWinsReset: A datetime.datetime representing the time at which the user's bountyWinsToday should be reset
                                to zero
    :vartype dailyBountyWinsReset: datetime.datetime
    :var pollOwned: Whether or not this user has a running ReactionPollMenu
    :vartype pollOwned: bool
    :var helpMenuOwned: Whether or not this user has a running reaction help menu
    :vartype helpMenuOwned: bool
    :var homeGuildID: The id of this user's 'home guild' - the only guild from which they may use several commands
                        e.g buy and check.
    :vartype homeGuildID: int
    :var guildTransferCooldownEnd: A timestamp after which this user is allowed to transfer their homeGuildID.
    :vartype guildTransferCooldownEnd: datetime.datetime
    """

    def __init__(self, userID: int, credits : int = 0, lifetimeBountyCreditsWon : int = 0,
                    bountyCooldownEnd : int = -1, systemsChecked : int = 0, bountyWins : int = 0, activeShip : bool = None,
                    inactiveShips : inventory.Inventory = inventory.TypeRestrictedInventory(shipItem.Ship),
                    inactiveModules : inventory.Inventory = inventory.TypeRestrictedInventory(moduleItem.ModuleItem),
                    inactiveWeapons : inventory.Inventory = inventory.TypeRestrictedInventory(primaryWeapon.PrimaryWeapon),
                    inactiveTurrets : inventory.Inventory = inventory.TypeRestrictedInventory(turretWeapon.TurretWeapon),
                    inactiveTools : inventory.Inventory = inventory.TypeRestrictedInventory(toolItem.ToolItem),
                    lastSeenGuildId : int = -1, duelWins : int = 0, duelLosses : int = 0, duelCreditsWins : int = 0,
                    duelCreditsLosses : int = 0, alerts : dict[Union[type, str], Union[userAlerts.UABase or bool]] = {},
                    bountyWinsToday : int = 0, dailyBountyWinsReset : datetime = None, pollOwned : bool = False,
                    homeGuildID : int = -1, guildTransferCooldownEnd : datetime = None):
        """
        :param int id: The user's unique ID. The same as their unique discord ID.
        :param int credits: The amount of credits (currency) this user has (Default 0)
        :param int lifetimeBountyCreditsWon: The total amount of credits this user has earned through hunting bounties
                                            (Default 0)
        :param float bountyCooldownEnd: A utc timestamp representing when the user's cmd_check cooldown is due to expire
                                        (Default -1)
        :param int systemsChecked: The total number of space systems this user has checked (Default 0)
        :param int bountyWins: The total number of bounties this user has won (Default 0)
        :param shipItem activeShip: The user's currently equipped shipItem (Default None)
        :param inventory inactiveShips: The shipItems currently in this user's inventory (unequipped)
                                        (Default empty inventory)
        :param inventory inactiveModules: The moduleItems currently in this user's inventory (unequipped)
                                            (Default empty inventory)
        :param inventory inactiveWeapons: The primaryWeapons currently in this user's inventory (unequipped)
                                            (Default empty inventory)
        :param inventory inactiveTurrets: The turretWeapons currently in this user's inventory (unequipped)
                                            (Default empty inventory)
        :param inventory inactiveTools: The toolItems currently in this user's inventory (Default empty inventory)
        :param int lastSeenGuildId: The ID of the guild where this user was last active. Not guaranteed to be present.
                                    (Default -1)
        :param int duelWins: The total number of duels the user has won (Default 0)
        :param int duelLosses: The total number of duels the user has lost (Default 0)
        :param int duelCreditsWins: The total amount of credits the user has won through fighting duels (Default 0)
        :param int duelCreditsLosses: The total amount of credits the user has lost through fighting duels (Default 0)
        :param alerts: A dictionary mapping either (userAlerts.UABase subtypes or string UA ids from
                        userAlerts.userAlertsIDsTypes) to either (instances of that subtype or booleans
                        representing the alert state) (Default {})
        :type alerts: dict[type or str, userAlerts.UABase or bool]
        :param int bountyWinsToday: The number of bounties the user has won today (Default 0)
        :param datetime.datetime dailyBountyWinsReset: A datetime.datetime representing the time at which the user's
                                                        bountyWinsToday should be reset to zero (Default datetime.utcnow())
        :param bool pollOwned: Whether or not this user has a running ReactionPollMenu (Default False)
        :param Guild homeGuildID: The ID of this user's 'home guild' - the only guild from which they may use several
                                    commands e.g buy and check.
        :param datetime.datetime guildTransferCooldownEnd: A timestamp after which this user is allowed to transfer
                                                            their homeGuildID.
        :raise TypeError: When given an argument of incorrect type
        """
        if type(userID) == float:
            userID = int(userID)
        elif type(userID) != int:
            raise TypeError("id must be int, given " + str(type(userID)))

        if type(credits) == float:
            credits = int(credits)
        elif type(credits) != int:
            raise TypeError("credits must be int, given " + str(type(credits)))

        if type(lifetimeBountyCreditsWon) == float:
            lifetimeBountyCreditsWon = int(lifetimeBountyCreditsWon)
        elif type(lifetimeBountyCreditsWon) != int:
            raise TypeError("lifetimeBountyCreditsWon must be int, given " + str(type(lifetimeBountyCreditsWon)))

        if type(bountyCooldownEnd) == int:
            bountyCooldownEnd = float(bountyCooldownEnd)
        if type(bountyCooldownEnd) != float:
            raise TypeError("bountyCooldownEnd must be float, given " + str(type(bountyCooldownEnd)))

        if type(systemsChecked) == float:
            systemsChecked = int(systemsChecked)
        elif type(systemsChecked) != int:
            raise TypeError("systemsChecked must be int, given " + str(type(systemsChecked)))

        if type(bountyWins) == float:
            bountyWins = int(bountyWins)
        elif type(bountyWins) != int:
            raise TypeError("bountyWins must be int, given " + str(type(bountyWins)))

        if dailyBountyWinsReset is None:
            dailyBountyWinsReset = datetime.utcnow()
        if guildTransferCooldownEnd is None:
            guildTransferCooldownEnd = datetime.utcnow()

        self.id = userID
        self.credits = credits
        self.lifetimeBountyCreditsWon = lifetimeBountyCreditsWon
        # TODO: Should probably change this to a datetime, like guildTransferCooldownEnd etc
        self.bountyCooldownEnd = bountyCooldownEnd
        self.systemsChecked = systemsChecked
        self.bountyWins = bountyWins

        self.activeShip = activeShip
        self.inactiveShips = inactiveShips
        self.inactiveModules = inactiveModules
        self.inactiveWeapons = inactiveWeapons
        self.inactiveTurrets = inactiveTurrets
        self.inactiveTools = inactiveTools

        self.lastSeenGuildId = lastSeenGuildId
        self.hasLastSeenGuildId = lastSeenGuildId != -1

        self.duelRequests = {}
        self.duelWins = duelWins
        self.duelLosses = duelLosses

        self.duelCreditsWins = duelCreditsWins
        self.duelCreditsLosses = duelCreditsLosses

        self.userAlerts = {}
        # Convert the given user alerts to types and instances. The given alerts may be IDs instead of types,
        # or booleans instead of instances.
        for alertID in userAlerts.userAlertsIDsTypes:
            alertType = userAlerts.userAlertsIDsTypes[alertID]
            if alertType in alerts:
                if isinstance(alerts[alertType], userAlerts.UABase):
                    self.userAlerts[alertType] = alerts[alertType]
                elif isinstance(alerts[alertType], bool):
                    self.userAlerts[alertType] = alertType(alerts[alertType])
                else:
                    botState.logger.log("bbUsr", "init", "Given unknown alert state type for UA " + alertID \
                        + ". Must be either UABase or bool, given " + type(alerts[alertType]).__name__ \
                        + ". Alert reset to default (" + str(alertType(cfg.userAlertsIDsDefaults[alertID])) + ")",
                        category="usersDB", eventType="LOAD-UA_STATE_TYPE")
                    self.userAlerts[alertType] = alertType(cfg.userAlertsIDsDefaults[alertID])
            elif alertID in alerts:
                if isinstance(alerts[alertID], userAlerts.UABase):
                    self.userAlerts[alertType] = alerts[alertID]
                elif isinstance(alerts[alertID], bool):
                    self.userAlerts[alertType] = alertType(alerts[alertID])
                else:
                    botState.logger.log("bbUsr", "init", "Given unknown alert state type for UA " + alertID \
                        + ". Must be either UABase or bool, given " + type(alerts[alertID]).__name__ \
                        + ". Alert reset to default (" + str(alertType(cfg.userAlertsIDsDefaults[alertID])) + ")",
                        category="usersDB", eventType="LOAD-UA_STATE_TYPE")
                    self.userAlerts[alertType] = alertType(cfg.userAlertsIDsDefaults[alertID])
            else:
                self.userAlerts[alertType] = alertType(cfg.userAlertsIDsDefaults[alertID])

        self.bountyWinsToday = bountyWinsToday
        self.dailyBountyWinsReset = dailyBountyWinsReset

        self.pollOwned = pollOwned
        self.helpMenuOwned = False

        self.homeGuildID = homeGuildID
        self.guildTransferCooldownEnd = guildTransferCooldownEnd


    def resetUser(self):
        """Reset the user's attributes back to their default values.
        """
        self.credits = 0
        self.lifetimeBountyCreditsWon = 0
        self.bountyCooldownEnd = -1
        self.systemsChecked = 0
        self.bountyWins = 0
        self.activeShip = shipItem.Ship.fromDict(defaultShipLoadoutDict)
        self.inactiveModules.clear()
        self.inactiveShips.clear()
        self.inactiveWeapons.clear()
        self.inactiveTurrets.clear()
        self.inactiveTools.clear()
        self.duelWins = 0
        self.duelLosses = 0
        self.duelCreditsWins = 0
        self.duelCreditsLosses = 0
        self.pollOwned = False
        self.homeGuildID = -1
        self.guildTransferCooldownEnd = datetime.utcnow()


    def numInventoryPages(self, item : str, maxPerPage : int) -> int:
        """Get the number of pages required to display all of the user's unequipped items of the named type,
        displaying the given number of items per page

        :param str item: The name of the item type whose inventory pages to calculate
        :param int maxPerPage: The maximum number of items that may be present on a single page of items (TODO: Add a default)
        :return: The number of pages of size maxPerPage needed to display all of the user's inactive items of the named type
        :rtype: int
        :raise ValueError: When requesting an invalid item type
        :raise NotImplementedError: When requesting a valid item type, but one that is not yet implemented (e.g commodity)
        """
        if item not in cfg.validItemNames:
            raise ValueError("Requested an invalid item name: " + item)

        numWeapons = self.inactiveWeapons.numKeys
        numModules = self.inactiveModules.numKeys
        numTurrets = self.inactiveTurrets.numKeys
        numShips = self.inactiveShips.numKeys
        numTools = self.inactiveTools.numKeys

        itemsNum = 0

        if item == "all":
            itemsNum = max(numWeapons, numModules, numTurrets, numShips, numTools)
        elif item == "module":
            itemsNum = numModules
        elif item == "weapon":
            itemsNum = numWeapons
        elif item == "turret":
            itemsNum = numTurrets
        elif item == "ship":
            itemsNum = numShips
        elif item == "tool":
            itemsNum = numTools
        else:
            raise NotImplementedError("Valid but unsupported item name: " + item)

        return int(itemsNum / maxPerPage) + (0 if itemsNum % maxPerPage == 0 else 1)


    def lastItemNumberOnPage(self, item : str, pageNum : int, maxPerPage : int) -> int:
        """Get index of the last item on the given page number, where page numbers are of size maxPerPage.
        This is an absolute index from the start of the inventory, not a relative index from the start of the page.

        :param str item: The name of the item type whose last index to calculate
        :param int maxPerPage: The maximum number of items that may be present on a single page of items (TODO: Add a default)
        :return: The index of the last item on page pageNum, where page numbers are of size maxPerPage
        :rtype: int
        :raise ValueError: When requesting an invalid item type
        :raise NotImplementedError: When requesting a valid item type, but one that is not yet implemented (e.g commodity)
        """
        if item not in cfg.validItemNames:
            raise ValueError("Requested an invalid item name: " + item)
        if pageNum < self.numInventoryPages(item, maxPerPage):
            return pageNum * maxPerPage

        elif item == "ship":
            return self.inactiveShips.numKeys
        elif item == "weapon":
            return self.inactiveWeapons.numKeys
        elif item == "module":
            return self.inactiveModules.numKeys
        elif item == "turret":
            return self.inactiveTurrets.numKeys
        elif item == "tool":
            return self.inactiveTools.numKeys
        else:
            raise NotImplementedError("Valid but unsupported item name: " + item)


    def unequipAll(self, ship : shipItem.Ship):
        """Unequip all items from the given shipItem, and move them into the user's inactive items ('hangar')
        The user must own ship.

        :param shipItem ship: the ship whose items to transfer to storage
        :raise TypeError: When given any other type than shipItem
        :raise RuntimeError: when given a shipItem that is not owned by this user
        """
        if not type(ship) == shipItem.Ship:
            raise TypeError("Can only unequipAll from a shipItem. Given " + str(type(ship)))

        if not self.ownsShip(ship):
            raise RuntimeError("Attempted to unequipAll on a ship that isnt owned by this BasedUser")

        for weapon in ship.weapons:
            self.inactiveWeapons.addItem(weapon)
        ship.clearWeapons()

        for module in ship.modules:
            self.inactiveModules.addItem(module)
        ship.clearModules()

        for turret in ship.turrets:
            self.inactiveTurrets.addItem(turret)
        ship.clearTurrets()


    def validateLoadout(self):
        """Ensure that the user's active loadout complies with moduleItemFactory.maxModuleTypeEquips
        This method was written as a transferal measure when maxModuleTypeEquips was first released, and should seldom be used
        """
        incompatibleModules = []

        for currentModule in self.activeShip.modules:
            if not self.activeShip.canEquipModuleType(type(currentModule)):
                incompatibleModules.append(currentModule)
                self.activeShip.unequipModuleObj(currentModule)

        finalModules = []
        for currentModule in incompatibleModules:
            if self.activeShip.canEquipModuleType(type(currentModule)):
                self.activeShip.equipModule(currentModule)
            else:
                finalModules.append(currentModule)

        for currentModule in finalModules:
            self.inactiveModules.addItem(currentModule)


    def ownsShip(self, ship : shipItem.Ship):
        """Decide whether or not this user owns the given shipItem.

        :param shipItem ship: The ship to test for ownership
        :return: True if ship is either equipped or in this user's hanger. False otherwise
        :rtype: bool
        """
        return self.activeShip is ship or ship in self.inactiveShips


    def equipShipObj(self, ship : shipItem.Ship, noSaveActive : bool = False):
        """Equip the given ship, replacing the active ship.
        Give noSaveActive=True to delete the currently equipped ship.

        :param shipItem ship: The ship to equip. Must be owned by this user
        :param bool noSaveActive: Give True to delete the currently equipped ship. Give False to move the active ship
                                    to the hangar. (Default False)
        :raise RuntimeError: When given a shipItem that is not owned by this user
        """
        if not self.ownsShip(ship):
            raise RuntimeError("Attempted to equip a ship that isnt owned by this BasedUser")
        if not noSaveActive and self.activeShip is not None:
            self.inactiveShips.addItem(self.activeShip)
        if ship in self.inactiveShips:
            self.inactiveShips.removeItem(ship)
        self.activeShip = ship


    def equipShipIndex(self, index : int):
        """Equip the ship at the given index in the user's inactive ships

        :param int index: The index from the user's inactive ships of the requested ship
        :raise IndexError: When given an index that is out of range of the user's inactive ships
        """
        if not (0 <= index <= self.inactiveShips.numKeys - 1):
            raise IndexError("Index out of range")
        if self.activeShip is not None:
            self.inactiveShips.addItem(self.activeShip)
        self.activeShip = self.inactiveShips[index]
        self.inactiveShips.removeItem(self.activeShip)


    def toDict(self, **kwargs) -> dict:
        """Serialize this BasedUser to a dictionary representation for saving to file.

        :return: A dictionary containing all information needed to recreate this user
        :rtype: dict
        """
        inactiveShipsDict = self.inactiveShips.toDict(**kwargs)["items"]
        inactiveModulesDict = self.inactiveModules.toDict(**kwargs)["items"]
        inactiveWeaponsDict = self.inactiveWeapons.toDict(**kwargs)["items"]
        inactiveTurretsDict = self.inactiveTurrets.toDict(**kwargs)["items"]

        if "saveType" not in kwargs:
            inactiveToolsDict = self.inactiveTools.toDict(saveType=True, **kwargs)["items"]
        else:
            inactiveToolsDict = self.inactiveTools.toDict(**kwargs)["items"]

        alerts = {}
        for alertID in self.userAlerts.keys():
            if isinstance(self.userAlerts[alertID], userAlerts.StateUserAlert):
                alerts[alertID] = self.userAlerts[alertID].state

        return {"credits": self.credits, "lifetimeBountyCreditsWon": self.lifetimeBountyCreditsWon, "bountyCooldownEnd": self.bountyCooldownEnd,
                "systemsChecked": self.systemsChecked, "bountyWins": self.bountyWins,
                "activeShip": self.activeShip.toDict(**kwargs), "inactiveShips": inactiveShipsDict,
                "inactiveModules": inactiveModulesDict, "inactiveWeapons": inactiveWeaponsDict,
                "inactiveTurrets": inactiveTurretsDict, "inactiveTools": inactiveToolsDict,
                "lastSeenGuildId": self.lastSeenGuildId, "duelWins": self.duelWins, "duelLosses": self.duelLosses,
                "duelCreditsWins": self.duelCreditsWins, "bountyWinsToday": self.bountyWinsToday,
                "dailyBountyWinsReset": self.dailyBountyWinsReset.timestamp(), "pollOwned": self.pollOwned,
                "duelCreditsLosses": self.duelCreditsLosses, "homeGuildID": self.homeGuildID,
                "guildTransferCooldownEnd": self.guildTransferCooldownEnd.timestamp()}


    def userDump(self) -> str:
        """Get a string containing key information about the user.

        :return: A string containing the user ID, credits, lifetimeBountyCreditsWon, bountyCooldownEnd, systemsChecked and bountyWins
        :rtype: str
        """
        data = "BasedUser #" + str(self.id) + ": "
        for att in [self.credits, self.lifetimeBountyCreditsWon, self.bountyCooldownEnd, self.systemsChecked, self.bountyWins]:
            data += str(att) + "/"
        return data[:-1]


    def getStatByName(self, stat : str) -> Union[int, float]:
        """Get a user attribute by its string name. This method is primarily used in leaderboard generation.

        :param str stat: One of id, credits, lifetimeBountyCreditsWon, bountyCooldownEnd, systemsChecked, bountyWins or value
        :return: The requested user attribute
        :rtype: int or float
        :raise ValueError: When given an invalid stat name
        """
        if stat == "id":
            return self.id
        elif stat == "credits":
            return self.credits
        elif stat == "lifetimeBountyCreditsWon":
            return self.lifetimeBountyCreditsWon
        elif stat == "bountyCooldownEnd":
            return self.bountyCooldownEnd
        elif stat == "systemsChecked":
            return self.systemsChecked
        elif stat == "bountyWins":
            return self.bountyWins
        elif stat == "value":
            modulesValue = 0
            for module in self.inactiveModules.keys:
                modulesValue += self.inactiveModules.items[module].count * module.getValue()
            turretsValue = 0
            for turret in self.inactiveTurrets.keys:
                turretsValue += self.inactiveTurrets.items[turret].count * turret.getValue()
            weaponsValue = 0
            for weapon in self.inactiveWeapons.keys:
                weaponsValue += self.inactiveWeapons.items[weapon].count * weapon.getValue()
            shipsValue = 0
            for ship in self.inactiveShips.keys:
                shipsValue += self.inactiveShips.items[ship].count * ship.getValue()
            toolsValue = 0
            for tool in self.inactiveTools.keys:
                toolsValue += self.inactiveTools.items[tool].count * tool.getValue()

            return modulesValue + turretsValue + weaponsValue + shipsValue + self.activeShip.getValue() + self.credits
        else:
            raise ValueError("Unknown stat name: " + str(stat))


    def getInactivesByName(self, item : str) -> inventory:
        """Get the all of the user's inactive (hangar) items of the named type.
        The given inventory is mutable, and can alter the contents of the user's inventory.

        :param str item: One of ship, weapon, module or turret
        :return: A inventory containing all of the user's inactive items of the named type.
        :rtype: inventory
        :raise ValueError: When requesting an invalid item type name
        :raise NotImplementedError: When requesting a valid item type name but one that is not yet implemented (e.g commodity)
        """
        if item == "all" or item not in cfg.validItemNames:
            raise ValueError("Invalid item type: " + item)
        elif item == "ship":
            return self.inactiveShips
        elif item == "weapon":
            return self.inactiveWeapons
        elif item == "module":
            return self.inactiveModules
        elif item == "turret":
            return self.inactiveTurrets
        elif item == "tool":
            return self.inactiveTools
        else:
            raise NotImplementedError("Valid, but unrecognised item type: " + item)


    def hasDuelChallengeFor(self, targetBasedUser : BasedUser) -> bool:
        """Decide whether or not this user has an active duel request targetted at the given BasedUser

        :param BasedUser targetBasedUser: The user to check for duel request existence
        :return: True if this user has sent a duel request to the given user, and it is still active. False otherwise
        :rtype: bool
        """
        return targetBasedUser in self.duelRequests


    def addDuelChallenge(self, duelReq : duelRequest.DuelRequest):
        """Store a new duel request from this user to another.
        The duel request must still be active (TODO: Add validation), the source user must be this user,
        the target user must not be this user, and this user must not already have a duel challenge for the target user.

        :param DuelRequest duelReq: The duel request to store
        :raise ValueError: When given a duel request where either: This is not the source user, this is the target user,
                            or a duel request is already stored for the target user (TODO: Move to separate exception types)
        """
        if duelReq.sourceBasedUser is not self:
            raise ValueError("Attempted to add a DuelRequest for a different source user: " + str(duelReq.sourceBasedUser.id))
        if self.hasDuelChallengeFor(duelReq.targetBasedUser):
            raise ValueError("Attempted to add a DuelRequest for an already challenged user: " \
                                + str(duelReq.sourceBasedUser.id))
        if duelReq.targetBasedUser is self:
            raise ValueError("Attempted to add a DuelRequest for self: " + str(duelReq.sourceBasedUser.id))
        self.duelRequests[duelReq.targetBasedUser] = duelReq


    def removeDuelChallengeObj(self, duelReq : duelRequest.DuelRequest):
        """Remove the given duel request object from this user's storage.

        :param DuelRequest duelReq: The DuelRequest to remove
        :raise ValueError: When given a duel request that this user object is unaware of
        """
        if (duelReq.targetBasedUser not in self.duelRequests) or (self.duelRequests[duelReq.targetBasedUser] is not duelReq):
            raise ValueError("Duel request not found: " + str(duelReq.sourceBasedUser.id) + " -> " \
                                + str(duelReq.sourceBasedUser.id))
        del self.duelRequests[duelReq.targetBasedUser]


    def removeDuelChallengeTarget(self, duelTarget : BasedUser.BasedUser):
        """Remove this user's duel request that is targetted at the given user.

        :param BasedUser duelTarget: The target user whose duel request to remove
        """
        self.removeDuelChallengeObj(self.duelRequests[duelTarget])


    async def setAlertByType(self, alertType : type, dcGuild : Guild, bbGuild : basedGuild.BasedGuild, dcMember : Member,
            newState : bool) -> bool:
        """Set the state of one of this users's userAlerts, identifying the alert by its class.

        :param type alertType: The class of the alert whose state to set. Must be a subclass of userAlerts.UABase
        :param discord.Guild dcGuild: The discord guild in which to set the alert state
                                        (currently only relevent for role-based alerts)
        :param bbGuild bbGuild: The bbGuild in which to set the alert state (currently only relevent for role-based alerts,
                                as the role must be looked up)
        :param discord.Member dcMember: This user's member object in dcGuild (TODO: Just grab dcMember from dcGuild in here)
        :param bool newState: The new desired of the alert
        """
        await self.userAlerts[alertType].setState(dcGuild, bbGuild, dcMember, newState)
        return newState


    async def setAlertByID(self, alertID : str, dcGuild : Guild, bbGuild : basedGuild.BasedGuild, dcMember : Member,
                            newState) -> bool:
        """Set the state of one of this users's userAlerts, identifying the alert by its ID as given by
        userAlerts.userAlertsIDsTypes.

        :param str alertID: The ID of the user alert type, as given by userAlerts.userAlertsIDsTypes
        :param discord.Guild dcGuild: The discord guild in which to set the alert state
                                        (currently only relevent for role-based alerts)
        :param bbGuild bbGuild: The bbGuild in which to set the alert state (currently only relevent for role-based alerts,
                                as the role must be looked up)
        :param discord.Member dcMember: This user's member object in dcGuild (TODO: Just grab dcMember from dcGuild in here)
        :param bool newState: The new desired of the alert
        """
        return await self.setAlertType(userAlerts.userAlertsIDsTypes[alertID], dcGuild, bbGuild, dcMember, newState)


    async def toggleAlertType(self, alertType : type, dcGuild : Guild, bbGuild : basedGuild.BasedGuild,
            dcMember : Member) -> bool:
        """Toggle the state of one of this users's userAlerts, identifying the alert by its class.

        :param type alertType: The class of the alert whose state to toggle. Must be a subclass of userAlerts.UABase
        :param discord.Guild dcGuild: The discord guild in which to toggle the alert state
                                        (currently only relevent for role-based alerts)
        :param bbGuild bbGuild: The bbGuild in which to toggle the alert state (currently only relevent for role-based
                                alerts, as the role must be looked up)
        :param discord.Member dcMember: This user's member object in dcGuild (TODO: Just grab dcMember from dcGuild in here)
        """
        return await self.userAlerts[alertType].toggle(dcGuild, bbGuild, dcMember)


    async def toggleAlertID(self, alertID : str, dcGuild : Guild, bbGuild : basedGuild.BasedGuild, dcMember : Member) -> bool:
        """Toggle the state of one of this users's userAlerts, identifying the alert by its ID as given by
        userAlerts.userAlertsIDsTypes.

        :param str alertID: The ID of the user alert type, as given by userAlerts.userAlertsIDsTypes
        :param discord.Guild dcGuild: The discord guild in which to toggle the alert state (currently only relevent for
                                        role-based alerts)
        :param bbGuild bbGuild: The bbGuild in which to toggle the alert state (currently only relevent for role-based alerts,
                                as the role must be looked up)
        :param discord.Member dcMember: This user's member object in dcGuild (TODO: Just grab dcMember from dcGuild in here)
        """
        return await self.toggleAlertType(userAlerts.userAlertsIDsTypes[alertID], dcGuild, bbGuild, dcMember)


    def isAlertedForType(self, alertType : type, dcGuild : Guild, bbGuild : basedGuild.BasedGuild, dcMember : Member) -> bool:
        """Get the state of one of this users's userAlerts, identifying the alert by its class.

        :param type alertType: The class of the alert whose state to get. Must be a subclass of userAlerts.UABase
        :param discord.Guild dcGuild: The discord guild in which to get the alert state (currently only relevent for
                                        role-based alerts)
        :param bbGuild bbGuild: The bbGuild in which to get the alert state (currently only relevent for role-based alerts,
                                as the role must be looked up)
        :param discord.Member dcMember: This user's member object in dcGuild (TODO: Just grab dcMember from dcGuild in here)
        """
        return self.userAlerts[alertType].getState(dcGuild, bbGuild, dcMember)


    def isAlertedForID(self, alertID : str, dcGuild : Guild, bbGuild : basedGuild.BasedGuild, dcMember : Member) -> bool:
        """Get the state of one of this user's userAlerts, identifying the alert by its ID as given by
        userAlerts.userAlertsIDsTypes.

        :param str alertID: The ID of the user alert type, as given by userAlerts.userAlertsIDsTypes
        :param discord.Guild dcGuild: The discord guild in which to get the alert state (currently only relevent
                                        for role-based alerts)
        :param bbGuild bbGuild: The bbGuild in which to get the alert state (currently only relevent for role-based alerts,
                                as the role must be looked up)
        :param discord.Member dcMember: This user's member object in dcGuild (TODO: Just grab dcMember from dcGuild in here)
        """
        return self.isAlertedForType(userAlerts.userAlertsIDsTypes[alertID], dcGuild, bbGuild, dcMember)


    def hasHomeGuild(self) -> bool:
        """Decide whether or not this user has a home guild set.

        :return: True if this user has a home guild, False otherwise
        :rtype: bool
        """
        return self.homeGuildID != -1


    def canTransferGuild(self, now : datetime = None) -> bool:
        """Decide whether this user is allowed to transfer their homeGuildID.
        This is decided based on the time passed since their last guild transfer.

        :param datetime.datetime now: The current time, if known. This optional parameter is included for increasing
                                        efficiency in the case where the current time has already been calculated.
        :return: True if this user has no home guild, or their guild transfer cooldown has completed, false otherwise
        :rtype: bool
        """
        if now is None:
            now = datetime.utcnow()
        return (not self.hasHomeGuild()) or now > self.guildTransferCooldownEnd


    async def transferGuild(self, newGuild : Guild):
        """Transfer the user's homeGuildID to the given guild.
        The user must not be on guild transfer cooldown.

        :param discord.Guild newGuild: The new discord.Guild to set this user's homeGuildID to.
                                        This user must be a member of newGuild.
        :raise ValueError: When this user is still in guild transfer cooldown
        :raise NameError: When this user is not a member of newGuild
        """
        now = datetime.utcnow()
        if not self.canTransferGuild(now=now):
            raise ValueError("This user cannot transfer guild again yet (" \
                                + lib.timeUtil.td_format_noYM(self.guildTransferCooldownEnd) + " remaining)")
        if await newGuild.fetch_member(self.id) is None:
            raise NameError("This user is not a member of the given guild '" + newGuild.name + "#" + str(newGuild.id) + "'")

        self.homeGuildID = newGuild.id
        self.guildTransferCooldownEnd = now + timedelta(**cfg.homeGuildTransferCooldown)


    def getInventoryForItem(self, item):
        if isinstance(item, shipItem.Ship):
            return self.inactiveShips
        elif isinstance(item, primaryWeapon.PrimaryWeapon):
            return self.inactiveWeapons
        elif isinstance(item, turretWeapon.TurretWeapon):
            return self.inactiveTurrets
        elif isinstance(item, toolItem.ToolItem):
            return self.inactiveTools


    def __str__(self) -> str:
        """Get a short string summary of this BasedUser. Currently only contains the user ID and home guild ID.

        :return: A string summar of the user, containing the user ID and home guild ID.
        :rtype: str
        """
        return "<BasedUser #" + str(self.id) + ((" @" + str(self.homeGuildID)) if self.hasHomeGuildID() else "") + ">"


    @classmethod
    def fromDict(cls, userDict: dict, **kwargs) -> BasedUser:
        """Construct a new BasedUser object from the given ID and the information in the
        given dictionary - The opposite of BasedUser.toDict

        :param int id: The discord ID of the user
        :param dict userDict: A dictionary containing all information necessary to construct
                                the BasedUser object, other than their ID.
        :return: A BasedUser object as described in userDict
        :rtype: BasedUser
        """
        if "id" not in kwargs:
            raise NameError("Required kwarg not given: id")
        userID = kwargs["id"]

        activeShip = shipItem.Ship.fromDict(userDict["activeShip"])

        inactiveShips = inventory.TypeRestrictedInventory(shipItem.Ship)
        if "inactiveShips" in userDict:
            for shipListingDict in userDict["inactiveShips"]:
                inactiveShips.addItem(shipItem.Ship.fromDict(shipListingDict["item"]), quantity=shipListingDict["count"])

        inactiveWeapons = inventory.TypeRestrictedInventory(primaryWeapon.PrimaryWeapon)
        if "inactiveWeapons" in userDict:
            for weaponListingDict in userDict["inactiveWeapons"]:
                inactiveWeapons.addItem(primaryWeapon.PrimaryWeapon.fromDict(weaponListingDict["item"]),
                                        quantity=weaponListingDict["count"])

        inactiveModules = inventory.TypeRestrictedInventory(moduleItem.ModuleItem)
        if "inactiveModules" in userDict:
            for moduleListingDict in userDict["inactiveModules"]:
                inactiveModules.addItem(moduleItemFactory.fromDict(moduleListingDict["item"]),
                                        quantity=moduleListingDict["count"])

        inactiveTurrets = inventory.TypeRestrictedInventory(turretWeapon.TurretWeapon)
        if "inactiveTurrets" in userDict:
            for turretListingDict in userDict["inactiveTurrets"]:
                inactiveTurrets.addItem(turretWeapon.TurretWeapon.fromDict(turretListingDict["item"]),
                                        quantity=turretListingDict["count"])

        inactiveTools = inventory.TypeRestrictedInventory(toolItem.ToolItem)
        if "inactiveTools" in userDict:
            for toolListingDict in userDict["inactiveTools"]:
                inactiveTools.addItem(toolItemFactory.fromDict(toolListingDict["item"]), quantity=toolListingDict["count"])

        return BasedUser(**cls._makeDefaults(userDict, ("lifetimeBountyCreditsWon", "lifetimeBountyCreditsWon"), userID=userID,
                                                activeShip=activeShip, inactiveShips=inactiveShips,
                                                inactiveModules=inactiveModules, inactiveWeapons=inactiveWeapons,
                                                inactiveTurrets=inactiveTurrets, inactiveTools=inactiveTools,
                                                lifetimeBountyCreditsWon=userDict.get("lifetimeBountyCreditsWon", userDict.get("lifetimeBountyCreditsWon", 0)),
                                                **{k: datetime.utcfromtimestamp(userDict[k]) \
                                                    for k in ("dailyBountyWinsReset", "guildTransferCooldownEnd") \
                                                    if k in userDict}))
