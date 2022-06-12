from ipaddress import IPv4Network, IPv6Network, IPv6Address, IPv4Address
from typing import Union, Optional, Any, Type

from cidr_man import CIDR

from .cidr_bottle_fast import FastBottle


PREFIX_UNION_T = Union[
    str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address
]


class Bottle(FastBottle):
    """
    cidr_bottle.Bottle is a Patricia Trie specifically designed for parsing and validating routing tables.
    Unlike other implementations it supports both sub-tree checking and longest-prefix matching.

    Grab a bottle!
    """

    left: "Bottle"
    right: "Bottle"
    parent: "Bottle"
    _prefix: CIDR
    _cls: Type
    value: Any
    passing: bool

    def __init__(
        self,
        left: Optional["Bottle"] = None,
        right: Optional["Bottle"] = None,
        parent: Optional["Bottle"] = None,
        prefix: Optional[PREFIX_UNION_T] = None,
        value: Optional[Any] = None,
        passing: Optional[bool] = True,
        cls: Optional[Type] = None,
    ):
        super().__init__()
        self.left = left
        self.right = right
        self.parent = parent
        if prefix is None:
            self._prefix = CIDR("0.0.0.0/0")
        elif not isinstance(prefix, CIDR):
            self._prefix = CIDR(prefix)
        else:
            self._prefix = prefix
        self._cls = cls if cls is not None else prefix.__class__
        self.value = value
        self.passing = passing

    @property
    def prefix(self):
        return self.__convert(self._prefix)

    @prefix.setter
    def prefix(
        self,
        prefix: PREFIX_UNION_T,
    ):
        if not isinstance(prefix, CIDR):
            self._prefix = CIDR(prefix)
        else:
            self._prefix = prefix
        self._cls = type(prefix)

    def get(
        self,
        prefix: PREFIX_UNION_T,
        exact: Optional[bool] = False,
        covering: Optional[bool] = False,
    ) -> "Bottle":
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        node = self._find(prefix, covering)
        if exact and node.prefix != prefix:
            raise KeyError("no exact match found")
        return node

    def insert(
        self,
        prefix: PREFIX_UNION_T,
        value=None,
    ):
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        node = self.set(prefix, value=value)
        node._cls = self._cls

    def delete(
        self,
        prefix: PREFIX_UNION_T,
    ):
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        self.set(prefix, delete=True)

    def contains(
        self,
        prefix: PREFIX_UNION_T,
        exact: bool = False,
    ) -> bool:
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return super().contains(prefix, exact)

    def set(
        self,
        prefix: PREFIX_UNION_T,
        value=None,
        delete=False,
    ):
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return super().set(prefix, value, delete)

    def children(self):
        return [self.__convert(child) for child in super().children()]

    def __convert(self, prefix):
        if self._cls is CIDR:
            return prefix
        elif self._cls is str:
            return str(prefix)
        elif self._cls is int:
            return int(prefix)
        elif self._cls is bytes:
            return bytes(prefix)
        elif self._cls in [IPv4Network, IPv4Address]:
            return IPv4Network(str(prefix))
        elif self._cls in [IPv6Network, IPv6Address]:
            return IPv6Network(str(prefix))
        return prefix

    def __contains__(self, prefix: PREFIX_UNION_T) -> bool:
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return super().contains(prefix)

    def __getitem__(self, prefix: PREFIX_UNION_T) -> Optional["Bottle"]:
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return self.get(prefix)

    def __setitem__(self, prefix: PREFIX_UNION_T, value):
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return super().insert(prefix, value)

    def __delitem__(self, prefix: PREFIX_UNION_T):
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return super().set(prefix, delete=True)

    def _find(
        self,
        prefix: PREFIX_UNION_T,
        create_if_missing: bool = False,
        covering: bool = False,
    ):
        if not isinstance(prefix, CIDR):
            prefix = CIDR(prefix)
        return super()._find(prefix, create_if_missing, covering=covering)
