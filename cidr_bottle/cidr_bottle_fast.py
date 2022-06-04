from dataclasses import dataclass, field
from typing import Optional, Any, Type

from cidr_man import CIDR
from cidr_man.cidr import max_prefix


@dataclass(init=False)
class FastBottle:
    """
    Similar to cidr_bottle.Bottle, cidr_bottle.FastBottle is a Patricia Trie specifically designed for parsing and validating routing tables.
    FastBottle however only supports cidr_man.CIDR objects as input to prefix fields.
    """

    _cls: Type
    left: "FastBottle" = field(default=None)
    right: "FastBottle" = field(default=None)
    parent: "FastBottle" = field(default=None)
    _prefix: CIDR = field(default_factory=CIDR)
    value: Any = field(default=None)
    passing: bool = field(default=True)
    _children: Optional[list] = field(default=None)
    _changed: bool = field(default=True)

    def __init__(
        self,
        left: "FastBottle" = None,
        right: "FastBottle" = None,
        parent: "FastBottle" = None,
        prefix: CIDR = None,
        value: Any = None,
        passing: bool = True,
    ):
        self.left = left
        self.right = right
        self.parent = parent
        if prefix is None:
            self._prefix = CIDR("0.0.0.0/0")
        else:
            self._prefix = prefix
        self.value = value
        self.passing = passing
        self._children = None
        self._changed = True

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: CIDR):
        self._prefix = prefix

    def get(
        self, network: CIDR, exact: bool = False, covering: bool = False
    ) -> "FastBottle":
        node = self._find(network, covering=covering)
        if exact and node._prefix != network:
            raise KeyError("no exact match found")
        return node

    def insert(self, network: CIDR, value=None):
        self.set(network, value=value)

    def delete(self, network: CIDR):
        self.set(network, delete=True)

    def contains(self, network: CIDR, exact: bool = False) -> bool:
        try:
            self.get(network, exact)
            return True
        except KeyError:
            return False

    def set(self, network: CIDR, value=None, delete=False) -> "FastBottle":
        self._changed = True
        if network.version != self._prefix.version:
            raise ValueError("incompatible network version")
        if network.prefix_len < self._prefix.prefix_len:
            raise ValueError("network is less specific than node")
        node = self._find(network, not delete)
        if delete:
            if node._prefix != network:
                raise KeyError(
                    f"attempting to delete non-existent key {network.compressed}"
                )
            left, right = node.parent._prefix.subnets()
            if node._prefix == left:
                node.parent.left = None
            else:
                node.parent.right = None
            node.parent = None
        else:
            node.value = value
            node.passing = False
        return node

    def children(self):
        if self._changed:
            descendants = {}
            node = self
            passed = {}
            while True:
                if not node.passing and node.prefix not in descendants:
                    descendants[node.prefix] = node
                if node._prefix in passed:
                    node = node.parent
                elif node.left is not None and node.left._prefix not in passed:
                    node = node.left
                elif node.right is not None and node.right._prefix not in passed:
                    node = node.right
                elif node.parent is not None:
                    passed[node._prefix] = True
                    node = node.parent
                else:
                    break
            self._children = list(descendants.values())
            self._changed = False
        return self._children

    def __str__(self):
        return self._prefix.compressed

    def __repr__(self):
        return f"{type(self).__name__}(prefix={self._prefix}, value={self.value}, passing={self.passing})"

    def __contains__(self, network: CIDR) -> bool:
        return self.contains(network)

    def __getitem__(self, network: CIDR) -> Optional["FastBottle"]:
        return self.get(network)

    def __setitem__(self, network: CIDR, value):
        self.insert(network, value)

    def __delitem__(self, network: CIDR):
        self.set(network, delete=True)

    def _create_node(self, prefix: CIDR, parent: "FastBottle") -> "FastBottle":
        node = type(self)()
        node._prefix = prefix
        node.parent = parent
        return node

    def _find(
        self, network: CIDR, create_if_missing: bool = False, covering: bool = False
    ):
        if not self._prefix.contains(network):
            return None
        node = self
        shift_bit = max_bits = max_prefix(self._prefix.version)
        while shift_bit > (max_bits - network.prefix_len) and node is not None:
            shift_bit -= 1
            is_right = bool(network.ip >> shift_bit & 1)
            has_left = node.left is not None
            has_right = node.right is not None
            if not create_if_missing and (
                (not is_right and not has_left) or (is_right and not has_right)
            ):
                break
            if is_right:
                if not has_right and create_if_missing:
                    node.right = self._create_node(
                        node._prefix.right, node
                    )
                node = node.right
            else:
                if not has_left and create_if_missing:
                    node.left = self._create_node(
                        node._prefix.left, node
                    )
                node = node.left
        if covering and node.passing:
            while node is not None and node.passing:
                node = node.parent
        return node
