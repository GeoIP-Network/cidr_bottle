from dataclasses import dataclass, field
from ipaddress import IPv4Network, IPv6Network, ip_network
from typing import Union, Optional, Any

from .subnets import subnet_of


@dataclass()
class Bottle:
    """
    cidr_bottle.Bottle is a Patricia Trie specifically designed for parsing and validating routing tables.
    Unlike other implementations it supports both sub-tree checking and longest-prefix matching.

    Grab a bottle!
    """

    left: "Bottle" = field(default=None)
    right: "Bottle" = field(default=None)
    parent: "Bottle" = field(default=None)
    prefix: Union[IPv4Network, IPv6Network] = field(default=IPv4Network("0.0.0.0/0"))
    value: Any = field(default=None)
    passing: bool = field(default=True)

    def insert(self, network: Union[str, IPv4Network, IPv6Network], value=None):
        self.set(network, value=value)

    def set(
        self, network: Union[str, IPv4Network, IPv6Network], value=None, delete=False
    ):
        if isinstance(network, str):
            network = ip_network(network)
        if (
            self.prefix != IPv4Network("0.0.0.0/0")
            and network.version != self.prefix.version
        ):
            raise ValueError("incompatible network version")
        if network < self.prefix:
            raise ValueError("network is smaller than node")
        node = self
        while node.prefix != network:
            left, right = node.prefix.subnets()
            if subnet_of(left, network):
                if (node.left is None) and not delete:
                    node.left = type(self)()
                    node.left.prefix = left
                    node.left.parent = node
                elif node.left is None:
                    raise KeyError(
                        f"attempting to delete non-existent key {network.compressed}"
                    )
                node = node.left
            else:
                if (node.right is None) and not delete:
                    node.right = type(self)()
                    node.right.prefix = right
                    node.right.parent = node
                elif node.right is None:
                    raise KeyError(
                        f"attempting to delete non-existent key {network.compressed}"
                    )
                node = node.right
        if delete:
            left, right = node.parent.prefix.subnets()
            if node.prefix == left:
                node.parent.left = None
            else:
                node.parent.right = None
            node.parent = None
        else:
            node.value = value
            node.passing = False

    def children(self):
        descendants = []
        node = self
        passed = {}
        while True:
            if not node.passing:
                descendants.append(node)
            if node.prefix in passed:
                node = node.parent
            elif node.left is not None and node.left.prefix not in passed:
                node = node.left
            elif node.right is not None and node.right.prefix not in passed:
                node = node.right
            elif node.parent != None:
                passed[node.prefix] = True
                node = node.parent
            else:
                break
        return descendants

    def get(
        self, network: Union[str, IPv4Network, IPv6Network], exact: bool = False
    ) -> "Bottle":
        if isinstance(network, str):
            network = ip_network(network)
        node = self
        while node.prefix != network:
            if not subnet_of(node.prefix, network):
                return None
            if node.left is not None and subnet_of(node.left.prefix, network):
                node = node.left
            elif node.right is not None:
                node = node.right
            else:
                break
        if exact and node.prefix != network:
            raise KeyError("no exact match found")
        return node

    def contains(
        self, network: Union[str, IPv4Network, IPv6Network], exact: bool = False
    ) -> bool:
        try:
            self.get(network, exact)
            return True
        except KeyError:
            return False

    def delete(self, network: Union[str, IPv4Network, IPv6Network]):
        self.set(network, delete=True)

    def __str__(self):
        return self.prefix.compressed

    def __repr__(self):
        return f"{type(self).__name__}(prefix={self.prefix}, value={self.value}, passing={self.passing})"

    def __contains__(self, network: Union[str, IPv4Network, IPv6Network]) -> bool:
        return self.contains(network)

    def __getitem__(
        self, network: Union[str, IPv4Network, IPv6Network]
    ) -> Optional["Bottle"]:
        return self.get(network)

    def __setitem__(self, network: Union[str, IPv4Network, IPv6Network], value):
        self.insert(network, value)

    def __delitem__(self, network: Union[str, IPv4Network, IPv6Network]):
        self.set(network, delete=True)
