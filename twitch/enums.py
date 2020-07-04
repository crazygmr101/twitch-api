from enum import IntEnum


class UserType(IntEnum):
    STAFF = 1
    ADMIN = 2
    GLOBAL_MOD = 3
    NONE = 0


class BroadcasterType(IntEnum):
    PARTNER = 1
    AFFILIATE = 2
    NONE = 0
