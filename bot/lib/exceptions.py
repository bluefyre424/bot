class UnrecognisedCustomEmoji(Exception):
    """Exception raised when creating a BasedEmoji instance, but the client could not match an emoji to the given ID.

    :var id: The ID that could not be matched
    :vartype id: int
    """

    def __init__(self, comment: str, id: int):
        """
        :param str comment: Description of the exception
        :param int id: The ID that could not be matched
        """
        super().__init__(comment)
        self.id = id


class UnrecognisedEmojiFormat(Exception):
    """Exception raised when creating a BasedEmoji from a string,
    but the string could not be pattern-matched as an emoji.
    Unfortunately this will also get raised when using an emoji that is not registered with the emoji consortium,
    because I can't disambiguate this case.

    :var char: The string that does not look like an emoji
    :vartype char: str
    """

    def __init__(self, comment: str, char: str):
        """
        :param str comment: Description of the exception
        :param str char: The string which does not look like an emoji
        """
        super().__init__(comment)
        self.char = char


class IncorrectCommandCallContext(Exception):
    """Exception used to indicate when a non-DMable command is called from DMs.
    May be used in the future to indicate the opposite; a command that can only be called from DMs is
    called from outside of DMs.
    """
    pass


class NoneDCGuildObj(Exception):
    """Raised when constructing a guild object, but the corresponding dcGuild was either not given or invalid.
    """
    pass


class InvalidGameObjectFolder(Exception):
    """Raised when attempting to load in a game object configuration folder with
    """
    def __init__(self, filePath, reason):
        super().__init__("Invalid game object configuration folder (" + reason + "): " + filePath)
        self.filePath = filePath
        self.reason = reason
