from ipaddress import IPv4Network, IPv6Network, IPv6Address, IPv4Address
from typing import Union, Optional, Any, Type

from cidr_man import CIDR

from .cidr_bottle_fast import FastBottle


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
            left: "Bottle" = None,
            right: "Bottle" = None,
            parent: "Bottle" = None,
            prefix: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address, None] = None,
            value: Any = None,
            passing: bool = True,
            cls: Type = None):
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
    def prefix(self, prefix: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address, None]):
        if not isinstance(prefix, CIDR):
            self._prefix = CIDR(prefix)
        else:
            self._prefix = prefix
        self._cls = type(prefix)

    def get(
        self, network: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address], exact: bool = False
    ) -> "Bottle":
        if not isinstance(network, CIDR):
            network = CIDR(network)
        node = self._find(network)
        if exact and node.prefix != network:
            raise KeyError("no exact match found")
        return node

    def insert(self, network: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address], value=None):
        if not isinstance(network, CIDR):
            network = CIDR(network)
        node = self.set(network, value=value)
        node._cls = self._cls

    def delete(self, network: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address]):
        if not isinstance(network, CIDR):
            network = CIDR(network)
        self.set(network, delete=True)

    def contains(
        self, network: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address], exact: bool = False
    ) -> bool:
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return super().contains(network, exact)

    def set(
        self, network: Union[str, int, bytes, CIDR, IPv4Network, IPv6Network, IPv4Address, IPv6Address], value=None, delete=False
    ):
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return super().set(network, value, delete)

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

    def __contains__(self, network: Union[str, IPv4Network, IPv6Network]) -> bool:
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return super().contains(network)

    def __getitem__(
        self, network: Union[str, IPv4Network, IPv6Network]
    ) -> Optional["Bottle"]:
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return self.get(network)

    def __setitem__(self, network: Union[str, IPv4Network, IPv6Network], value):
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return super().insert(network, value)

    def __delitem__(self, network: Union[str, IPv4Network, IPv6Network]):
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return super().set(network, delete=True)

    def _find(self, network: Union[str, CIDR, IPv4Network, IPv6Network], create_if_missing: bool = False):
        if not isinstance(network, CIDR):
            network = CIDR(network)
        return super()._find(network, create_if_missing)
