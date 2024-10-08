from __future__ import annotations
from discord import Embed, channel, Client, Forbidden, Guild, Member, Message, HTTPException, NotFound
from typing import List, Dict, Union
from datetime import timedelta

from .. import botState, lib
from ..gameObjects import guildShop
from ..databases import bountyDB
from ..gameObjects.bounties.bountyBoards import bountyBoardChannel
from ..userAlerts import userAlerts
from ..cfg import cfg, bbData
from ..scheduling.timedTask import TimedTask, DynamicRescheduleTask
from ..gameObjects.bounties import bounty
from ..baseClasses import serializable


class BasedGuild(serializable.Serializable):
    """A class representing a guild in discord, and storing extra bot-specific information about it.

    :var id: The ID of the guild, directly corresponding to a discord guild's ID.
    :vartype id: int
    :var dcGuild: This guild's corresponding discord.Guild object
    :vartype dcGuild: discord.Guild
    :var announceChannel: The discord.channel object for this guild's announcements chanel.
                            None when no announce channel is set for this guild.
    :vartype announceChannel: discord.channel.TextChannel
    :var playChannel: The discord.channel object for this guild's bounty playing chanel.
                        None when no bounty playing channel is set for this guild.
    :vartype playChannel: discord.channel.TextChannel
    :var shop: This guild's guildShop object
    :vartype shop: guildShop
    :var alertRoles: A dictionary of user alert IDs to guild role IDs.
    :vartype alertRoles: dict[str, int]
    :var bountyBoardChannel: A bountyBoardChannel object implementing this guild's bounty board channel if it has one,
                                None otherwise.
    :vartype bountyBoardChannel: bountyBoardChannel
    :var hasBountyBoardChannel: Whether this guild has a bounty board channel or not
    :vartype hasBountyBoardChannel: bool
    :var ownedRoleMenus: The number of ReactionRolePickers present in this guild
    :vartype ownedRoleMenus: int
    :var bounties: This guild's active bounties
    :vartype bounties: bountyDB.bountyDB
    :var bountiesDisabled: Whether or not to disable this guild's bountyDB and bounty spawning
    :vartype bountiesDisabled: bool
    :var shopDisabled: Whether or not to disable this guild's guildShop and shop refreshing
    :vartype shopDisabled: bool
    """

    def __init__(self, id: int, dcGuild: Guild, bounties: bountyDB.BountyDB, commandPrefix: str = cfg.defaultCommandPrefix,
            announceChannel : channel.TextChannel = None, playChannel : channel.TextChannel = None,
            shop : guildShop.GuildShop = None, bountyBoardChannel : bountyBoardChannel.bountyBoardChannel = None,
            alertRoles : Dict[str, int] = {}, ownedRoleMenus : int = 0, bountiesDisabled : bool = False,
            shopDisabled : bool = False):
        """
        :param int id: The ID of the guild, directly corresponding to a discord guild's ID.
        :param discord.Guild dcGuild: This guild's corresponding discord.Guild object
        :param bountyDB.bountyDB bounties: This guild's active bounties
        :param discord.channel announceChannel: The discord.channel object for this guild's announcements chanel.
                                                None when no announce channel is set for this guild.
        :param discord.channel playChannel: The discord.channel object for this guild's bounty playing chanel.
                                            None when no bounty playing channel is set for this guild.
        :param guildShop shop: This guild's guildShop object
        :param dict[str, int] alertRoles: A dictionary of user alert IDs to guild role IDs.
        :param BoardBoardChannel bountyBoardChannel: A bountyBoardChannel object implementing this guild's bounty board
                                                        channel if it has one, None otherwise.
        :param int ownedRoleMenus: The number of ReactionRolePickers present in this guild
        :param bool bountiesDisabled: Whether or not to disable this guild's bountyDB and bounty spawning
        :param bool shopDisabled: Whether or not to disable this guild's guildShop and shop refreshing
        :raise TypeError: When given an incompatible argument type
        """

        if dcGuild is None:
            raise lib.exceptions.NoneDCGuildObj("Given dcGuild of type '" + type(dcGuild).__name__ \
                                                + "', expecting discord.Guild")

        self.id = id
        self.dcGuild = dcGuild
        if not commandPrefix:
            raise ValueError("Empty command prefix provided")
        self.commandPrefix = commandPrefix

        if type(id) == float:
            id = int(id)
        elif type(id) != int:
            raise TypeError("id must be int, given " + str(type(id)))

        self.announceChannel = announceChannel
        self.playChannel = playChannel

        self.shopDisabled = shopDisabled
        if shopDisabled:
            self.shop = None
        else:
            self.shop = guildShop.GuildShop() if shop is None else shop

        self.alertRoles = {}
        for alertID in userAlerts.userAlertsIDsTypes.keys():
            if issubclass(userAlerts.userAlertsIDsTypes[alertID], userAlerts.GuildRoleUserAlert):
                self.alertRoles[alertID] = alertRoles[alertID] if alertID in alertRoles else -1

        self.ownedRoleMenus = ownedRoleMenus
        self.bountiesDB = bounties
        self.bountiesDisabled = bountiesDisabled

        bountyDelayGenerators = {"random": lib.timeUtil.getRandomDelay,
                                "fixed-routeScale": self.getRouteScaledBountyDelayFixed,
                                "random-routeScale": self.getRouteScaledBountyDelayRandom}

        bountyDelayGeneratorArgs = {"random": {"min": timedelta(**cfg.timeouts.newBountyDelayRandomMin),
                                                "max": timedelta(**cfg.timeouts.newBountyDelayRandomMax)},
                                    "fixed-routeScale": cfg.newBountyFixedDelta,
                                    "random-routeScale": {"min": timedelta(**cfg.timeouts.newBountyDelayRandomMin),
                                                            "max": timedelta(**cfg.timeouts.newBountyDelayRandomMax)}}

        if bountiesDisabled:
            self.newBountyTT = None
            self.bountyBoardChannel = None
            self.hasBountyBoardChannel = False
        else:
            self.bountyBoardChannel = bountyBoardChannel
            self.hasBountyBoardChannel = bountyBoardChannel is not None

            if cfg.newBountyDelayType == "fixed":
                self.newBountyTT = TimedTask(expiryDelta=timedelta(**cfg.newBountyFixedDelta),
                                                autoReschedule=True, expiryFunction=self.spawnAndAnnounceRandomBounty)
            else:
                try:
                    delayGenerator = bountyDelayGenerators[cfg.newBountyDelayType]
                    generatorArgs = bountyDelayGeneratorArgs[cfg.newBountyDelayType]
                except KeyError:
                    raise ValueError("cfg: Unrecognised newBountyDelayType '" + cfg.newBountyDelayType + "'")
                else:
                    self.newBountyTT = DynamicRescheduleTask(delayGenerator,
                                                            delayTimeGeneratorArgs=generatorArgs,
                                                            autoReschedule=True,
                                                            expiryFunction=self.spawnAndAnnounceRandomBounty)

            botState.newBountiesTTDB.scheduleTask(self.newBountyTT)


    def getAnnounceChannel(self) -> channel:
        """Get the discord channel object of the guild's announcements channel.

        :return: the discord.channel of the guild's announcements channel
        :rtype: discord.channel.TextChannel
        :raise ValueError: If this guild does not have an announcements channel
        """
        if not self.hasAnnounceChannel():
            raise ValueError("This guild has no announce channel set")
        return self.announceChannel


    def getPlayChannel(self) -> channel:
        """Get the discord channel object of the guild's bounty playing channel.

        :return: the discord channel object of the guild's bounty playing channel
        :raise ValueError: If this guild does not have a play channel
        :rtype: discord.channel.TextChannel
        """
        if not self.hasPlayChannel():
            raise ValueError("This guild has no play channel set")
        return self.playChannel


    def setAnnounceChannel(self, announceChannel : channel.TextChannel):
        """Set the discord channel object of the guild's announcements channel.

        :param int announceChannel: The discord channel object of the guild's new announcements channel
        """
        self.announceChannel = announceChannel


    def setPlayChannel(self, playChannel : channel.TextChannel):
        """Set the discord channel of the guild's bounty playing channel.

        :param int playChannel: The discord channel object of the guild's new bounty playing channel
        """
        self.playChannel = playChannel


    def hasAnnounceChannel(self) -> bool:
        """Whether or not this guild has an announcements channel

        :return: True if this guild has a announcements channel, False otherwise
        :rtype bool:
        """
        return self.announceChannel is not None


    def hasPlayChannel(self) -> bool:
        """Whether or not this guild has a play channel

        :return: True if this guild has a play channel, False otherwise
        :rtype bool:
        """
        return self.playChannel is not None


    def removePlayChannel(self):
        """Remove and deactivate this guild's announcements channel.

        :raise ValueError: If this guild does not have a play channel
        """
        if not self.hasPlayChannel():
            raise ValueError("Attempted to remove play channel on a BasedGuild that has no playChannel")
        self.playChannel = None


    def removeAnnounceChannel(self):
        """Remove and deactivate this guild's play channel.

        :raise ValueError: If this guild does not have an announcements channel
        """
        if not self.hasAnnounceChannel():
            raise ValueError("Attempted to remove announce channel on a BasedGuild that has no announceChannel")
        self.announceChannel = None



    def getUserAlertRoleID(self, alertID : str) -> int:
        """Get the ID of this guild's alerts role for the given alert ID.

        :param str alertID: The alert ID for which the role ID should be fetched
        :return: The ID of the discord role that this guild mentions for the given alert ID.
        :rtype: int
        """
        return self.alertRoles[alertID]


    def setUserAlertRoleID(self, alertID : str, roleID : int):
        """Set the ID of this guild's alerts role for the given alert ID.

        :param str alertID: The alert ID for which the role ID should be set
        :param int roleID: The ID of the role which this guild should mention when alerting alertID
        """
        self.alertRoles[alertID] = roleID


    def removeUserAlertRoleID(self, alertID : str):
        """Remove the stored role and deactivate alerts for the given alertID

        :param str alertID: The alert ID for which the role ID should be removed
        """
        self.alertRoles[alertID] = -1


    def hasUserAlertRoleID(self, alertID : str) -> bool:
        """Decide whether or not this guild has a role set for the given alert ID.

        :param str alertID: The alert ID for which the role existence should be tested
        :return: True if this guild has a role set to mention for alertID
        :rtype: bool
        :raise KeyError: If given an unrecognised alertID
        """
        if alertID in self.alertRoles:
            return self.alertRoles[alertID] != -1
        raise KeyError("Unknown GuildRoleUserAlert ID: " + alertID)


    async def addBountyBoardChannel(self, channel : channel.TextChannel, client : Client, factions : List[str]):
        """Set this guild's bounty board channel.

        :param discord.Channel channel: The channel where bounty listings should be posted
        :param discord.Client client: A logged in client used to fetch the channel and any existing listings.
        :param list[str] factions: A list of faction names with which bounty listings can be associated
        :raise RuntimeError: If the guild already has an active bountyBoardChannel
        """
        if self.hasBountyBoardChannel:
            raise RuntimeError("Attempted to assign a bountyboard channel for guild " + str(self.id) \
                                + " but one is already assigned")
        self.bountyBoardChannel = bountyBoardChannel.bountyBoardChannel(channel.id, {}, -1)
        await self.bountyBoardChannel.init(client, factions)
        self.hasBountyBoardChannel = True


    def removeBountyBoardChannel(self):
        """Deactivate this guild's bountyBoardChannel. This does not remove any active bounty listing messages.

        :raise RuntimeError: If this guild does not have an active bountyBoardChannel.
        """
        if not self.hasBountyBoardChannel:
            raise RuntimeError("Attempted to remove a bountyboard channel for guild " + str(self.id) \
                                + " but none is assigned")
        self.bountyBoardChannel = None
        self.hasBountyBoardChannel = False


    async def makeBountyBoardChannelMessage(self, bounty : bounty.Bounty, msg : str = "", embed : Embed = None) -> Message:
        """Create a new bountyBoardChannel listing for the given bounty, in the given guild.
        guild must own a bountyBoardChannel.

        :param bounty.Bounty bounty: The bounty for which to create a listing
        :param str msg: The text to display in the listing message content (Default "")
        :param discord.Embed embed: The embed to display in the listing message - this will be removed immediately in place
                                    of the embed generated during bountyBoardChannel.updateBountyMessage,
                                    so is only really useful in case updateBountyMessage fails. (Default None)
        :return: The new discord message containing the BBC listing
        :rtype: discord.Message
        :raise ValueError: If guild does not own a bountyBoardChannel
        """
        if not self.hasBountyBoardChannel:
            raise ValueError("The requested BasedGuild has no bountyBoardChannel")
        bountyListing = await self.bountyBoardChannel.channel.send(msg, embed=embed)
        await self.bountyBoardChannel.addBounty(bounty, bountyListing)
        await self.bountyBoardChannel.updateBountyMessage(bounty)
        return bountyListing


    async def removeBountyBoardChannelMessage(self, bounty : bounty.Bounty):
        """Remove guild's bountyBoardChannel listing for bounty.

        :param bounty bounty: The bounty whose BBC listing should be removed
        :raise ValueError: If guild does not own a BBC
        :raise KeyError: If the guild's BBC does not have a listing for bounty
        """
        if not self.hasBountyBoardChannel:
            raise ValueError("The requested BasedGuild has no bountyBoardChannel")
        if self.bountyBoardChannel.hasMessageForBounty(bounty):
            try:
                await self.bountyBoardChannel.getMessageForBounty(bounty).delete()
            except HTTPException:
                botState.logger.log("Main", "rmBBCMsg",
                                    "HTTPException thrown when removing bounty listing message for criminal: " \
                                    + bounty.criminal.name, category='bountyBoards', eventType="RM_LISTING-HTTPERR")
            except Forbidden:
                botState.logger.log("Main", "rmBBCMsg",
                                    "Forbidden exception thrown when removing bounty listing message for criminal: " \
                                    + bounty.criminal.name, category='bountyBoards', eventType="RM_LISTING-FORBIDDENERR")
            except NotFound:
                botState.logger.log("Main", "rmBBCMsg",
                                    "Bounty listing message no longer exists, BBC entry removed: " + bounty.criminal.name,
                                    category='bountyBoards', eventType="RM_LISTING-NOT_FOUND")
            await self.bountyBoardChannel.removeBounty(bounty)
        else:
            raise KeyError("The requested BasedGuild (" + str(self.id) \
                            + ") does not have a bountyBoardChannel listing for the given bounty: " + bounty.criminal.name)


    async def updateBountyBoardChannel(self, bounty : bounty.Bounty, bountyComplete : bool = False):
        """Update the BBC listing for the given bounty in the given server.

        :param bounty bounty: The bounty whose listings should be updated
        :param bool bountyComplete: Whether or not the bounty has now been completed.
                                    When True, bounty listings will be removed rather than updated. (Default False)
        """
        if self.hasBountyBoardChannel:
            if bountyComplete and self.bountyBoardChannel.hasMessageForBounty(bounty):
                await self.removeBountyBoardChannelMessage(bounty)
            else:
                if not self.bountyBoardChannel.hasMessageForBounty(bounty):
                    await self.makeBountyBoardChannelMessage(bounty, "A new bounty is now available from **" \
                                                                    + bounty.faction.title() + "** central command:")
                else:
                    await self.bountyBoardChannel.updateBountyMessage(bounty)


    def getRouteScaledBountyDelayFixed(self, baseDelayDict : Dict[str, int]) -> timedelta:
        """New bounty delay generator, scaling a fixed delay by the length of the presently spawned bounty.

        :param dict baseDelayDict: A timedelta-compliant dictionary describing the amount of time to wait
                                    after a bounty is spawned with route length 1
        :return: A datetime.timedelta indicating the time to wait before spawning a new bounty
        :rtype: datetime.timedelta
        """
        timeScale = cfg.fallbackRouteScale if self.bountiesDB.latestBounty is None else \
                    len(self.bountiesDB.latestBounty.route)
        delay = timedelta(**baseDelayDict) * timeScale * cfg.newBountyDelayRouteScaleCoefficient
        botState.logger.log("Main", "routeScaleBntyDelayFixed",
                            "New bounty delay generated, " \
                                + ("no latest criminal." if self.bountiesDB.latestBounty is None else \
                                + ("latest criminal: '" + self.bountiesDB.latestBounty.criminal.name + "'. Route Length " \
                                + str(len(self.bountiesDB.latestBounty.route)))) + "\nDelay picked: " + str(delay),
                            category="newBounties",
                            eventType="NONE_BTY" if self.bountiesDB.latestBounty is None else "DELAY_GEN", noPrint=True)
        return delay


    def getRouteScaledBountyDelayRandom(self, baseDelayDict : Dict[str, int]) -> timedelta:
        """New bounty delay generator, generating a random delay time between two points,
        scaled by the length of the presently spawned bounty.

        :param dict baseDelayDict: A dictionary describing the minimum and maximum time in seconds to wait after a bounty is
                                    spawned with route length 1
        :return: A datetime.timedelta indicating the time to wait before spawning a new bounty
        :rtype: datetime.timedelta
        """
        timeScale = cfg.fallbackRouteScale if self.bountiesDB.latestBounty is None else \
                    len(self.bountiesDB.latestBounty.route)
        delay = lib.timeUtil.getRandomDelay({"min": baseDelayDict["min"] * timeScale \
                                                        * cfg.newBountyDelayRouteScaleCoefficient,
                                                    "max": baseDelayDict["max"] * timeScale \
                                                        * cfg.newBountyDelayRouteScaleCoefficient})
        botState.logger.log("Main", "routeScaleBntyDelayRand",
                            "New bounty delay generated, " \
                                + ("no latest criminal." if self.bountiesDB.latestBounty is None else \
                                    ("latest criminal: '" + self.bountiesDB.latestBounty.criminal.name \
                                + "'. Route Length " + str(len(self.bountiesDB.latestBounty.route)))) + "\nRange: " \
                                + str((baseDelayDict["min"] * timeScale * cfg.newBountyDelayRouteScaleCoefficient) / 60) \
                                + "m - " \
                                + str((baseDelayDict["max"] * timeScale * cfg.newBountyDelayRouteScaleCoefficient) / 60) \
                                + "m\nDelay picked: " + str(delay), category="newBounties",
                            eventType="NONE_BTY" if self.bountiesDB.latestBounty is None else "DELAY_GEN", noPrint=True)
        return delay


    async def announceNewBounty(self, newBounty : bounty.Bounty):
        """Announce the creation of a new bounty to this guild's announceChannel, if it has one

        :param bounty newBounty: the bounty to announce
        """
        # Create the announcement embed
        bountyEmbed = lib.discordUtil.makeEmbed(titleTxt=lib.discordUtil.criminalNameOrDiscrim(newBounty.criminal),
                                                desc="⛓ __New Bounty Available__",
                                                col=bbData.factionColours[newBounty.faction],
                                                thumb=newBounty.criminal.icon, footerTxt=newBounty.faction.title())
        bountyEmbed.add_field(name="Reward:", value=str(newBounty.reward) + " Credits")
        bountyEmbed.add_field(name="Possible Systems:", value=len(newBounty.route))
        bountyEmbed.add_field(name="See the culprit's route with:",
                                value="`" + self.commandPrefix + "route " \
                                        + lib.discordUtil.criminalNameOrDiscrim(newBounty.criminal) + "`",
                                inline=False)
        # Create the announcement text
        msg = "A new bounty is now available from **" + newBounty.faction.title() + "** central command:"

        if self.hasBountyBoardChannel:
            try:
                if self.hasUserAlertRoleID("bounties_new"):
                    msg = "<@&" + str(self.getUserAlertRoleID("bounties_new")) + "> " + msg
                # announce to the given channel
                bountyListing = await self.bountyBoardChannel.channel.send(msg, embed=bountyEmbed)
                await self.bountyBoardChannel.addBounty(newBounty, bountyListing)
                await self.bountyBoardChannel.updateBountyMessage(newBounty)
                return bountyListing

            except Forbidden:
                botState.logger.log("BasedGuild", "anncBnty",
                                    "Failed to post BBCh listing to guild " + botState.client.get_guild(self.id).name + "#" \
                                    + str(self.id) + " in channel " + self.bountyBoardChannel.channel.name + "#" \
                                    + str(self.bountyBoardChannel.channel.id), category="bountyBoards",
                                    eventType="BBC_NW_FRBDN")

        # If the guild has an announceChannel
        elif self.hasAnnounceChannel():
            # ensure the announceChannel is valid
            currentChannel = self.getAnnounceChannel()
            if currentChannel is not None:
                try:
                    if self.hasUserAlertRoleID("bounties_new"):
                        # announce to the given channel
                        await currentChannel.send("<@&" + str(self.getUserAlertRoleID("bounties_new")) + "> " + msg,
                                                    embed=bountyEmbed)
                    else:
                        await currentChannel.send(msg, embed=bountyEmbed)
                except Forbidden:
                    botState.logger.log("BasedGuild", "anncBnty",
                                        "Failed to post announce-channel bounty listing to guild " \
                                        + botState.client.get_guild(self.id).name + "#" + str(self.id) + " in channel " \
                                        + currentChannel.name + "#" + str(currentChannel.id), eventType="ANNCCH_SND_FRBDN")

            # TODO: may wish to add handling for invalid announceChannels - e.g remove them from the BasedGuild object


    async def spawnAndAnnounceRandomBounty(self):
        """Generate a completely random bounty, spawn it, and announce it if this guild has
        an appropriate channel selected.
        """
        if self.bountiesDisabled:
            raise ValueError("Attempted to spawn a bounty into a guild where bounties are disabled")
        # ensure a new bounty can be created
        if self.bountiesDB.canMakeBounty():
            newBounty = bounty.Bounty(owningDB=self.bountiesDB)
            # activate and announce the bounty
            self.bountiesDB.addBounty(newBounty)
            await self.announceNewBounty(newBounty)


    async def announceBountyWon(self, bounty : bounty.Bounty, rewards : Dict[int, Dict[str, Union[int, bool]]],
            winningUser : Member):
        """Announce the completion of a bounty
        Messages will be sent to the playChannel if one is set

        :param bounty bounty: the bounty to announce
        :param dict rewards: the rewards dictionary as defined by bounty.calculateRewards
        :param discord.Member winningUser: the guild member that won the bounty
        """
        if self.dcGuild is not None:
            if self.hasPlayChannel():
                winningUserId = winningUser.id
                # Create the announcement embed
                rewardsEmbed = lib.discordUtil.makeEmbed(titleTxt="Bounty Complete!",
                                                        authorName=lib.discordUtil.criminalNameOrDiscrim(bounty.criminal) \
                                                        + " Arrested", icon=bounty.criminal.icon,
                                                        col=bbData.factionColours[bounty.faction],
                                                        desc="`Suspect located in '" + bounty.answer + "'`")

                # Add the winning user to the embed
                rewardsEmbed.add_field(name="1. 🏆 " + str(rewards[winningUserId]["reward"]) + " credits:",
                                        value=winningUser.mention + " checked " \
                                        + str(int(rewards[winningUserId]["checked"])) + " system" \
                                        + ("s" if int(rewards[winningUserId]["checked"]) != 1 else ""), inline=False)

                # The index of the current user in the embed
                place = 2
                # Loop over all non-winning users in the rewards dictionary
                for userID in rewards:
                    if not rewards[userID]["won"]:
                        rewardsEmbed.add_field(name=str(place) + ". " + str(rewards[userID]["reward"]) + " credits:",
                                                value="<@" + str(userID) + "> checked " \
                                                + str(int(rewards[userID]["checked"])) + " system" \
                                                + ("s" if int(rewards[userID]["checked"]) != 1 else ""), inline=False)
                        place += 1

                # Send the announcement to the guild's playChannel
                await self.getPlayChannel().send(":trophy: **You win!**\n**" + winningUser.display_name \
                                                    + "** located and EMP'd **" + bounty.criminal.name \
                                                    + "**, who has been arrested by local security forces. :chains:",
                                                    embed=rewardsEmbed)

        else:
            botState.logger.log("Main", "AnncBtyWn",
                                "None dcGuild received when posting bounty won to guild " \
                                + botState.client.get_guild(self.id).name + "#" + str(self.id) + " in channel ?#" \
                                + str(self.getPlayChannel().id), eventType="DCGUILD_NONE")


    def enableBounties(self):
        """Enable bounties for this guild.
        Sets up a new bounties DB and bounty spawning TimedTask.

        :raise ValueError: If bounties are already enabled in this guild
        """
        if not self.bountiesDisabled:
            raise ValueError("Bounties are already enabled in this guild")

        self.bountiesDB = bountyDB.BountyDB(bbData.bountyFactions)

        bountyDelayGenerators = {"random": lib.timeUtil.getRandomDelay,
                                "fixed-routeScale": self.getRouteScaledBountyDelayFixed,
                                "random-routeScale": self.getRouteScaledBountyDelayRandom}

        bountyDelayGeneratorArgs = {"random": {"min": cfg.timeouts.newBountyDelayRandomMin,
                                                "max": cfg.timeouts.newBountyDelayRandomMax},
                                    "fixed-routeScale": cfg.newBountyFixedDelta,
                                    "random-routeScale": {"min": cfg.timeouts.newBountyDelayRandomMin,
                                                            "max": cfg.timeouts.newBountyDelayRandomMax}}

        if cfg.newBountyDelayType == "fixed":
            self.newBountyTT = TimedTask(expiryDelta=timedelta(**cfg.newBountyFixedDelta),
                                            autoReschedule=True, expiryFunction=self.spawnAndAnnounceRandomBounty)
        else:
            try:
                generatorArgs = bountyDelayGeneratorArgs[cfg.newBountyDelayType]
                self.newBountyTT = DynamicRescheduleTask(bountyDelayGenerators[cfg.newBountyDelayType],
                                                            delayTimeGeneratorArgs=generatorArgs,
                                                            autoReschedule=True,
                                                            expiryFunction=self.spawnAndAnnounceRandomBounty)
            except KeyError:
                raise ValueError("cfg: Unrecognised newBountyDelayType '" + cfg.newBountyDelayType + "'")

        botState.newBountiesTTDB.scheduleTask(self.newBountyTT)
        self.bountiesDisabled = False


    def disableBounties(self):
        """Disable bounties for this guild.
        Removes any bountyboard if one is present, and removes the guild's bounties DB and bounty spawning TimedTask.

        :raise ValueError: If bounties are already disabled in this guild
        """
        if self.bountiesDisabled:
            raise ValueError("Bounties are already disabled in this guild")

        if self.hasBountyBoardChannel:
            self.removeBountyBoardChannel()
        botState.newBountiesTTDB.unscheduleTask(self.newBountyTT)
        self.newBountyTT = None
        self.bountiesDisabled = True
        self.bountiesDB = None


    def enableShop(self):
        """Enable the shop for this guild.
        Creates a new guildShop object for this guild.

        :raise ValueError: If the shop is already enabled in this guild
        """
        if not self.shopDisabled:
            raise ValueError("The shop is already enabled in this guild")

        self.shop = guildShop.GuildShop(noRefresh=True)
        self.shopDisabled = False


    def disableShop(self):
        """Disable the shop for this guild.
        Removes the guild's guildShop object.

        :raise ValueError: If the shop is already disabled in this guild
        """
        if self.shopDisabled:
            raise ValueError("The shop is already disabled in this guild")

        self.shop = None
        self.shopDisabled = True


    async def announceNewShopStock(self):
        """Announce to the guild's play channel that this guild's shop stock has been refreshed.
        If no playChannel has been set, does nothing.

        :raise ValueError: If this guild's shop is disabled
        """
        if self.shopDisabled:
            raise ValueError("Attempted to announceNewShopStock on a guild where shop is disabled")
        if self.hasPlayChannel():
            playCh = self.getPlayChannel()
            msg = "The shop stock has been refreshed!\n**        **Now at tech level: **" \
                    + str(self.shop.currentTechLevel) + "**"
            try:
                if self.hasUserAlertRoleID("shop_refresh"):
                    # announce to the given channel
                    await playCh.send(":arrows_counterclockwise: <@&" \
                                        + str(self.getUserAlertRoleID("shop_refresh")) + "> " + msg)
                else:
                    await playCh.send(":arrows_counterclockwise: " + msg)
            except Forbidden:
                botState.logger.log("Main", "anncNwShp",
                                    "Failed to post shop stock announcement to " + self.dcGuild.name + "#" + str(self.id) \
                                    + " in channel " + playCh.name + "#" + str(playCh.id), category="shop",
                                    eventType="PLCH_NONE")


    def toDict(self, **kwargs) -> dict:
        """Serialize this BasedGuild into dictionary format to be saved to file.

        :return: A dictionary containing all information needed to reconstruct this BasedGuild
        :rtype: dict
        """
        data = {    "announceChannel":  self.announceChannel.id if self.hasAnnounceChannel() else -1,
                    "playChannel":      self.playChannel.id if self.hasPlayChannel() else -1,
                    "alertRoles":       self.alertRoles,
                    "ownedRoleMenus":   self.ownedRoleMenus,
                    "bountiesDisabled": self.bountiesDisabled,
                    "shopDisabled":     self.shopDisabled}

        if self.commandPrefix != cfg.defaultCommandPrefix:
            data["commandPrefix"] = self.commandPrefix

        if not self.bountiesDisabled:
            data["bountyBoardChannel"] = self.bountyBoardChannel.toDict(**kwargs) if self.hasBountyBoardChannel else None
            data["bountiesDB"] = self.bountiesDB.toDict(**kwargs)

        if not self.shopDisabled:
            data["shop"] = self.shop.toDict(**kwargs)

        return data


    @classmethod
    def fromDict(cls, guildDict: dict, **kwargs) -> BasedGuild:
        """Factory function constructing a new BasedGuild object from the information
        in the provided guildDict - the opposite of BasedGuild.toDict

        :param int guildID: The discord ID of the guild
        :param dict guildDict: A dictionary containing all information required to build the BasedGuild object
        :param bool dbReload: Whether or not this guild is being created during the initial database loading phase of
                                bountybot. This is used to toggle name checking in bounty contruction.
        :return: A BasedGuild according to the information in guildDict
        :rtype: BasedGuild
        """
        if "guildID" not in kwargs:
            raise NameError("Required kwarg missing: guildID")
        guildID = kwargs["guildID"]
        dbReload = kwargs.get("dbReload", False)

        dcGuild = botState.client.get_guild(guildID)
        if dcGuild is None:
            raise lib.exceptions.NoneDCGuildObj("Could not get guild object for id " + str(guildID))

        announceChannel = guildDict.get("announceChannel", -1)
        announceChannel = dcGuild.get_channel(announceChannel) if announceChannel != -1 else None
        playChannel = guildDict.get("playChannel", -1)
        playChannel = dcGuild.get_channel(playChannel) if playChannel != -1 else None

        if guildDict.get("bountiesDisabled", False):
            bountiesDB = None
            bbc = None
        else:
            if "bountiesDB" in guildDict:
                bountiesDB = bountyDB.BountyDB.fromDict(guildDict["bountiesDB"], dbReload=dbReload)
            else:
                bountiesDB = bountyDB.BountyDB(bbData.bountyFactions)
            
            if guildDict.get("bountyBoardChannel", -1) != -1:
                bbc = bountyBoardChannel.bountyBoardChannel.fromDict(guildDict["bountyBoardChannel"])
        
        if not guildDict.get("shopDisabled", True):
            shop = None
        else:
            if "shop" in guildDict:
                shop = guildShop.GuildShop.fromDict(guildDict["shop"])
            else:
                shop = guildShop.GuildShop()
        

        return BasedGuild(**cls._makeDefaults(guildDict, ("bountiesDB",),
                                                id=guildID, dcGuild=dcGuild, bounties=bountiesDB,
                                                announceChannel=announceChannel, playChannel=playChannel,
                                                shop=shop, bountyBoardChannel=bbc))
