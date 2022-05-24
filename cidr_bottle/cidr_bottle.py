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

    def get(
        self, network: Union[str, IPv4Network, IPv6Network], exact: bool = False
    ) -> "Bottle":
        if isinstance(network, str):
            network = ip_network(network)
        node = self._find(network)
        if exact and node.prefix != network:
            raise KeyError("no exact match found")
        return node

    def insert(self, network: Union[str, IPv4Network, IPv6Network], value=None):
        self.set(network, value=value)

    def delete(self, network: Union[str, IPv4Network, IPv6Network]):
        self.set(network, delete=True)

    def contains(
        self, network: Union[str, IPv4Network, IPv6Network], exact: bool = False
    ) -> bool:
        try:
            self.get(network, exact)
            return True
        except KeyError:
            return False

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
        if network.prefixlen < self.prefix.prefixlen:
            raise ValueError("network is less specific than node")
        node = self._find(network, not delete)
        if delete:
            if node.prefix != network:
                raise KeyError(
                    f"attempting to delete non-existent key {network.compressed}"
                )
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
            elif node.parent is not None:
                passed[node.prefix] = True
                node = node.parent
            else:
                break
        return descendants

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

    def _create_node(self, prefix: Union[IPv4Network, IPv6Network], parent: "Bottle") -> "Bottle":
        node = type(self)()
        node.prefix = prefix
        node.parent = parent
        return node

    def _find(self, network: Union[str, IPv4Network, IPv6Network], create_if_missing: bool = False):
        node = self
        while node.prefix != network:
            left, right = node.prefix.subnets()
            is_left = subnet_of(left, network)
            if not subnet_of(node.prefix, network):
                return None
            if (node.left is None) and is_left and create_if_missing:
                node.left = self._create_node(left, node)
            elif node.left is not None and is_left:
                node = node.left
            elif (node.right is None) and not is_left and create_if_missing:
                node.right = self._create_node(right, node)
            elif node.right is not None and not is_left:
                node = node.right
            else:
                break
        return node
