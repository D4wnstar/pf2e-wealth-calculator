from dataclasses import dataclass, field
from enum import Enum
import typing


class OriginError(Exception):
    """Mismatched origin in operation between Money objects."""

    def __init__(self, message):
        super().__init__(message)


class Origins(Enum):
    ITEM = "item"
    ART_OBJECT = "art object"
    CURRENCY = "currency"
    TOTAL = "total"


@dataclass
class Money:
    """Simple data structure for cp/sp/gp amounts."""

    cp: int = 0
    sp: int = 0
    gp: int = 0
    origin: Origins = Origins.ITEM
    check_origin: bool = True

    def __add__(self, val):
        if type(val) == int:
            return Money(
                self.cp + val,
                self.sp + val,
                self.gp + val,
                self.origin,
                self.check_origin,
            )

        if type(val) == Money:
            if self.check_origin and val.check_origin and self.origin != val.origin:
                raise OriginError("Origins don't match")
            return Money(
                self.cp + val.cp,
                self.sp + val.sp,
                self.gp + val.gp,
                self.origin,
                self.check_origin,
            )

        raise TypeError(
            f"Unsupported sum operation for type {type(val)} on class Money"
        )

    def __radd__(self, val):
        return self.__add__(val)

    def __mul__(self, val):
        if type(val) == int:
            return Money(
                self.cp * val,
                self.sp * val,
                self.gp * val,
                self.origin,
                self.check_origin,
            )

        else:
            raise TypeError(
                f"Unsupported multiplication operation for type {type(val)} on class Money"
            )

    def __rmul__(self, val):
        return self.__mul__(val)


@dataclass(frozen=True)
class ItemInfo:
    """Data structure that contains information on a given item."""

    name: str = "item"
    price: Money = field(default_factory=Money)
    category: str = "none"
    subcategory: str = "none"
    level: int = 0
    rarity: str = "common"
    bulk: typing.Union[int, str] = 0


class PathState(Enum):
    VALID = 0
    NONEXISTANT_DIR = 1
    EXISTING_FILE = 2
    WRONG_EXTENSION = 3
