from ipaddress import ip_network

import pytest

from cidr_bottle.cidr_bottle import Bottle


def test_root():
    root = Bottle()
    assert root.prefix == ip_network("0.0.0.0/0")
    assert root.prefix != ip_network("::/0")
    assert root.passing is True
    assert root.left is None
    assert root.right is None
    assert root.value is None


def test_ipv6_root():
    root = Bottle(prefix=ip_network("::/0"))
    assert root.prefix != ip_network("0.0.0.0/0")
    assert root.prefix == ip_network("::/0")
    assert root.passing is True
    assert root.left is None
    assert root.right is None
    assert root.value is None


def test_insert_left_str():
    root = Bottle()
    root.insert("0.0.0.0/1")
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == ip_network("0.0.0.0/1")


def test_insert_left_network():
    root = Bottle()
    root.insert(ip_network("0.0.0.0/1"))
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == ip_network("0.0.0.0/1")


def test_insert_with_value():
    root = Bottle()
    root.insert(ip_network("0.0.0.0/1"), 1)
    assert root.left.value == 1


def test_multiple_inserts():
    root = Bottle()
    root.insert(ip_network("0.0.0.0/1"), 1)  # left
    root.insert(ip_network("0.0.0.0/2"), 2)  # left left
    root.insert(ip_network("64.0.0.0/2"), 3)  # left right
    root.insert(ip_network("128.0.0.0/1"), 4)  # right
    assert root.left.prefix == ip_network("0.0.0.0/1")
    assert root.left.value == 1
    assert root.right.prefix == ip_network("128.0.0.0/1")
    assert root.right.value == 4
    assert root.left.left.prefix == ip_network("0.0.0.0/2")
    assert root.left.left.value == 2
    assert root.left.right.prefix == ip_network("64.0.0.0/2")
    assert root.left.right.value == 3


def test_insert_right_network():
    root = Bottle()
    root.insert(ip_network("128.0.0.0/1"))
    assert root.left is None
    assert root.right is not None
    assert root.right.prefix == ip_network("128.0.0.0/1")


def test_ipv6_insert_left_str():
    root = Bottle(prefix=ip_network("::/0"))
    root.insert("::/1")
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == ip_network("::/1")


def test_ipv6_insert_left_network():
    root = Bottle(prefix=ip_network("::/0"))
    root.insert(ip_network("::/1"))
    assert root.left is not None
    assert root.right is None
    assert root.left.prefix == ip_network("::/1")


def test_ipv6_insert_right_network():
    root = Bottle(prefix=ip_network("::/0"))
    root.insert(ip_network("8000::/1"))
    assert root.left is None
    assert root.right is not None
    assert root.right.prefix == ip_network("8000::/1")


def test_insert_deep_network():
    root = Bottle()
    root.insert(ip_network("192.0.2.0/24"))
    assert root.left is None
    assert root.right is not None
    assert root.right.right is not None
    assert root.right.right.left is not None
    assert len(root.children()) == 1
    assert root.right.prefix == ip_network("128.0.0.0/1")
    assert root.children()[0].prefix == ip_network("192.0.2.0/24")


def test_get():
    root = Bottle()
    root.insert(ip_network("128.0.0.0/1"), 1)
    assert root.get(ip_network("128.0.0.0/1")).prefix == ip_network("128.0.0.0/1")
    assert root.get(ip_network("128.128.0.0/9")).prefix == ip_network("128.0.0.0/1")
    assert root[ip_network("128.0.0.0/1")].prefix == ip_network("128.0.0.0/1")
    assert root[ip_network("128.128.0.0/9")].prefix == ip_network("128.0.0.0/1")


def test_get_exact():
    root = Bottle()
    root.insert(ip_network("128.0.0.0/1"), 1)
    assert root.get(ip_network("128.0.0.0/1"), exact=True).prefix == ip_network(
        "128.0.0.0/1"
    )
    with pytest.raises(KeyError):
        assert root.get(ip_network("128.128.0.0/9"), exact=True).prefix == ip_network(
            "128.0.0.0/1"
        )


def test_contains():
    root = Bottle()
    root.insert(ip_network("128.0.0.0/1"), 1)
    assert ip_network("128.0.0.0/1") in root
    assert ip_network("128.128.0.0/9") in root
    assert root.contains(ip_network("128.0.0.0/1"))
    assert root.contains(ip_network("128.128.0.0/9"))


def test_contains_exact():
    root = Bottle()
    root.insert(ip_network("128.0.0.0/1"), 1)
    assert root.contains(ip_network("128.0.0.0/1"), exact=True)
    assert not root.contains(ip_network("128.128.0.0/9"), exact=True)


def test_delete():
    root = Bottle()
    root.insert(ip_network("128.0.0.0/1"), 1)
    root.insert(ip_network("128.128.0.0/9"), 1)
    assert root[ip_network("128.0.0.0/1")].prefix == ip_network("128.0.0.0/1")
    assert root[ip_network("128.128.0.0/9")].prefix == ip_network("128.128.0.0/9")
    assert not root[ip_network("128.128.0.0/9")].passing
    del root[ip_network("128.128.0.0/9")]
    assert root[ip_network("128.0.0.0/1")].prefix == ip_network("128.0.0.0/1")
    assert root[ip_network("128.128.0.0/9")].prefix == ip_network("128.0.0.0/8")
    assert root[ip_network("128.128.0.0/9")].passing
