from ipaddress import IPv4Network, IPv6Network

from cidr_bottle.subnets import subnet_of


def test_valid_subnet_of():
    target = IPv4Network("10.0.0.0/24").subnet_of(IPv4Network("10.0.0.0/16"))
    result = subnet_of(IPv4Network("10.0.0.0/16"), IPv4Network("10.0.0.0/24"))
    assert target == result


def test_equal_subnet_of():
    target = IPv4Network("10.0.0.0/16").subnet_of(IPv4Network("10.0.0.0/16"))
    result = subnet_of(IPv4Network("10.0.0.0/16"), IPv4Network("10.0.0.0/16"))
    assert target == result


def test_supernet_subnet_of():
    target = IPv4Network("10.0.0.0/16").subnet_of(IPv4Network("10.0.0.0/24"))
    result = subnet_of(IPv4Network("10.0.0.0/24"), IPv4Network("10.0.0.0/16"))
    assert target == result


def test_invalid_subnet_of():
    target = IPv4Network("127.0.0.0/24").subnet_of(IPv4Network("10.0.0.0/16"))
    result = subnet_of(IPv4Network("10.0.0.0/16"), IPv4Network("127.0.0.0/24"))
    assert target == result


def test_valid_subnet_of_2():
    target = IPv4Network("64.0.0.0/2").subnet_of(IPv4Network("0.0.0.0/1"))
    result = subnet_of(IPv4Network("0.0.0.0/1"), IPv4Network("64.0.0.0/2"))
    assert target == result


def test_valid_subnet_of_ipv6():
    target = IPv6Network("2001:db8::/56").subnet_of(IPv6Network("2001:db8::/32"))
    result = subnet_of(IPv6Network("2001:db8::/32"), IPv6Network("2001:db8::/56"))
    assert target == result


def test_valid_subnet_of_ipv6_2():
    target = IPv6Network("2001:4200::/32").subnet_of(IPv6Network("::/0"))
    result = subnet_of(IPv6Network("::/0"), IPv6Network("2001:4200::/32"))
    assert target == result


def test_invalid_subnet_of_ipv6():
    target = IPv6Network("2001:db8::/56").subnet_of(IPv6Network("2001:fb8::/32"))
    result = subnet_of(IPv6Network("2001:fb8::/32"), IPv6Network("2001:db8::/56"))
    assert target == result
