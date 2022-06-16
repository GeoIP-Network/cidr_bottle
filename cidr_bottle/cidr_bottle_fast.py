from dataclasses import field
from typing import Optional, Any, Type

from cidr_man import CIDR
from cidr_man.cidr import max_prefix


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
        self, prefix: CIDR, exact: bool = False, covering: bool = False
    ) -> "FastBottle":
        node = self._find(prefix, covering=covering)
        if exact and node._prefix != prefix:
            raise KeyError("no exact match found")
        return node

    def insert(self, prefix: CIDR, value: Any = None, aggregate: bool = False):
        self.set(prefix, value=value, aggregate=aggregate)

    def delete(self, prefix: CIDR):
        self.set(prefix, delete=True)

    def contains(self, prefix: CIDR, exact: bool = False) -> bool:
        try:
            self.get(prefix, exact)
            return True
        except KeyError:
            return False

    def set(
        self, prefix: CIDR, value=None, delete=False, aggregate=False
    ) -> "FastBottle":
        self._changed = True
        if prefix.version != self._prefix.version:
            raise ValueError("incompatible network version")
        if prefix.prefix_len < self._prefix.prefix_len:
            raise ValueError("network is less specific than node")
        node = self._find(prefix, not delete)
        if delete:
            if node._prefix != prefix:
                raise KeyError(
                    f"attempting to delete non-existent key {prefix.compressed}"
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
            parent = node.parent
            if aggregate and parent.passing:
                while None not in (parent.left, parent.right) and not (
                    parent.left.passing or parent.right.passing
                ):
                    parent.passing = False
                    if parent.value is None:
                        parent.value = node.value
                    if parent.parent is not None:
                        parent = parent.parent
                    else:
                        break
        return node

    def children(self):
        if self._changed:
            descendants = {}
            node = self
            passed = {}
            while True:
                prefix = (node._prefix.ip, node._prefix.prefix_len)
                if not node.passing and prefix not in descendants:
                    descendants[prefix] = node
                if prefix in passed:
                    node = node.parent
                elif (
                    node.left is not None
                    and (node.left._prefix.ip, node.left._prefix.prefix_len)
                    not in passed
                ):
                    node = node.left
                elif (
                    node.right is not None
                    and (node.right._prefix.ip, node.right._prefix.prefix_len)
                    not in passed
                ):
                    node = node.right
                elif node.parent is not None:
                    passed[prefix] = True
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

    def __contains__(self, prefix: CIDR) -> bool:
        return self.contains(prefix)

    def __getitem__(self, prefix: CIDR) -> Optional["FastBottle"]:
        return self.get(prefix)

    def __setitem__(self, prefix: CIDR, value):
        self.insert(prefix, value)

    def __delitem__(self, prefix: CIDR):
        self.set(prefix, delete=True)

    def _create_node(self, prefix: CIDR, parent: "FastBottle") -> "FastBottle":
        return self.__class__(parent=parent, prefix=prefix)

    def _find(
        self, prefix: CIDR, create_if_missing: bool = False, covering: bool = False
    ):
        shift_bit = max_bits = max_prefix(self._prefix.version)
        max_shift = max_bits - prefix.prefix_len
        ip = prefix.ip
        mask = max_bits - self._prefix.prefix_len
        if (self._prefix.ip >> mask) != (ip >> mask):
            return None
        node = self
        most_recent_non_passing = None
        while shift_bit > max_shift and node is not None:
            shift_bit -= 1
            if ip >> shift_bit & 1:
                if node.right is None:
                    if create_if_missing:
                        node.right = self._create_node(node._prefix.right, node)
                    else:
                        break
                node = node.right
            else:
                if node.left is None:
                    if create_if_missing:
                        node.left = self._create_node(node._prefix.left, node)
                    else:
                        break
                node = node.left
            if not node.passing:
                most_recent_non_passing = node
        if covering and node.passing:
            node = most_recent_non_passing
        return node
