from ipaddress import IPv4Network

import pytest

from cidr_man import CIDR

from cidr_bottle import Bottle


def test_root():
    root = Bottle()
    assert root.prefix == CIDR("0.0.0.0/0")
    with pytest.raises(ValueError):
        assert root.prefix != CIDR("::/0")
    assert root.passing is True
    assert root.left is None
    assert root.right is None
    assert root.value is None


def test_ipv6_root():
    root = Bottle(prefix=CIDR("::/0"))
    with pytest.raises(ValueError):
        assert root.prefix != CIDR("0.0.0.0/0")
    assert root.prefix == CIDR("::/0")
    assert root.passing is True
    assert root.left is None
    assert root.right is None
    assert root.value is None


def test_insert_left_str():
    root = Bottle()
    root.insert("0.0.0.0/1")
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == CIDR("0.0.0.0/1")


def test_insert_left_network():
    root = Bottle()
    root.insert(CIDR("0.0.0.0/1"))
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == CIDR("0.0.0.0/1")


def test_insert_with_value():
    root = Bottle()
    root.insert(CIDR("0.0.0.0/1"), 1)
    assert root.left.value == 1


def test_multiple_inserts():
    root = Bottle()
    root.insert(CIDR("0.0.0.0/1"), 1)  # left
    root.insert(CIDR("0.0.0.0/2"), 2)  # left left
    root.insert(CIDR("64.0.0.0/2"), 3)  # left right
    root.insert(CIDR("128.0.0.0/1"), 4)  # right
    assert root.left.prefix == CIDR("0.0.0.0/1")
    assert root.left.value == 1
    assert root.right.prefix == CIDR("128.0.0.0/1")
    assert root.right.value == 4
    assert root.left.left.prefix == CIDR("0.0.0.0/2")
    assert root.left.left.value == 2
    assert root.left.right.prefix == CIDR("64.0.0.0/2")
    assert root.left.right.value == 3


def test_insert_right_network():
    root = Bottle()
    root.insert(CIDR("128.0.0.0/1"))
    assert root.left is None
    assert root.right is not None
    assert root.right.prefix == CIDR("128.0.0.0/1")


def test_ipv6_insert_left_str():
    root = Bottle(prefix=CIDR("::/0"))
    root.insert("::/1")
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == CIDR("::/1")


def test_ipv6_insert_left_network():
    root = Bottle(prefix=CIDR("::/0"))
    root.insert(CIDR("::/1"))
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == CIDR("::/1")


def test_ipv6_insert_right_network():
    root = Bottle(prefix=CIDR("::/0"))
    root.insert(CIDR("8000::/1"))
    assert root.left is None
    assert root.right is not None
    assert root.right.prefix == CIDR("8000::/1")


def test_insert_deep_network():
    root = Bottle()
    root.insert(CIDR("192.0.2.0/24"))
    root.insert(CIDR("203.0.113.0/24"))
    assert root.left is None
    assert root.right is not None
    assert root.right.right is not None
    assert root.right.right.left is not None
    assert len(root.children()) == 2
    assert root.right.prefix == CIDR("128.0.0.0/1")
    assert root.children()[0].prefix == CIDR("192.0.2.0/24")


def test_get():
    root = Bottle()
    root.insert(CIDR("128.0.0.0/1"), 1)
    assert isinstance(root.get("128.0.0.0/1"), Bottle)
    assert isinstance(root["128.0.0.0/1"], Bottle)
    assert root.get(CIDR("128.0.0.0/1")).prefix == CIDR("128.0.0.0/1")
    assert root.get(CIDR("128.128.0.0/9")).prefix == CIDR("128.0.0.0/1")
    assert root["128.0.0.0/1"].prefix == CIDR("128.0.0.0/1")
    assert root["128.128.0.0/9"].prefix == CIDR("128.0.0.0/1")


def test_get_exact():
    root = Bottle()
    root.insert(CIDR("128.0.0.0/1"), 1)
    assert root.get(CIDR("128.0.0.0/1"), exact=True).prefix == CIDR("128.0.0.0/1")
    with pytest.raises(KeyError):
        assert root.get(CIDR("128.128.0.0/9"), exact=True).prefix == CIDR("128.0.0.0/1")


def test_prefix():
    root = Bottle(prefix="0.0.0.0/0")
    root.insert("128.0.0.0/1", 1)
    assert isinstance(root.get("128.0.0.0/1").prefix, str)
    assert isinstance(root["128.0.0.0/1"].prefix, str)
    root = Bottle(prefix=CIDR("0.0.0.0/0"))
    root.insert(CIDR("128.0.0.0/1"), 1)
    assert isinstance(root.get("128.0.0.0/1").prefix, CIDR)
    assert isinstance(root["128.0.0.0/1"].prefix, CIDR)
    root = Bottle(prefix=CIDR("0.0.0.0/0"))
    root.insert("128.0.0.0/1", 1)
    assert isinstance(root.get("128.0.0.0/1").prefix, CIDR)
    assert isinstance(root["128.0.0.0/1"].prefix, CIDR)
    root = Bottle(prefix=IPv4Network("0.0.0.0/0"))
    root.insert(CIDR("128.0.0.0/1"), 1)
    assert isinstance(root.get("128.0.0.0/1").prefix, IPv4Network)
    assert isinstance(root["128.0.0.0/1"].prefix, IPv4Network)


def test_contains():
    root = Bottle()
    root.insert(CIDR("128.0.0.0/1"), 1)
    assert CIDR("128.0.0.0/1") in root
    assert CIDR("128.128.0.0/9") in root
    assert root.contains(CIDR("128.0.0.0/1"))
    assert root.contains(CIDR("128.128.0.0/9"))


def test_contains_exact():
    root = Bottle()
    root.insert(CIDR("128.0.0.0/1"), 1)
    assert root.contains(CIDR("128.0.0.0/1"), exact=True)
    assert not root.contains(CIDR("128.128.0.0/9"), exact=True)


def test_delete():
    root = Bottle()
    root.insert(CIDR("128.0.0.0/1"), 1)
    root.insert(CIDR("128.128.0.0/9"), 1)
    assert root[CIDR("128.0.0.0/1")].prefix == CIDR("128.0.0.0/1")
    assert root[CIDR("128.128.0.0/9")].prefix == CIDR("128.128.0.0/9")
    assert not root[CIDR("128.128.0.0/9")].passing
    del root[CIDR("128.128.0.0/9")]
    assert root[CIDR("128.0.0.0/1")].prefix == CIDR("128.0.0.0/1")
    assert root[CIDR("128.128.0.0/9")].prefix == CIDR("128.0.0.0/8")
    assert root[CIDR("128.128.0.0/9")].passing


def test_children():
    root = Bottle()
    subnets = []
    with open("tests/data/children_test_data") as f:
        for line in f:
            root.insert(line.strip())
            subnets.append(line.strip())
    result = [node.prefix.compressed for node in root.children()]
    assert set(result) == set(subnets)
