class CommandError(Exception):
    pass


class CommandRegisteredError(CommandError):
    def __init__(self, command: str, *args):
        self.message = f"Command {command} has already been registered"

    def __str__(self):
        return self.message
