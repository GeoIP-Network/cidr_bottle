from ipaddress import IPv4Network, IPv6Network
from typing import Union


def subnet_of(
    supernet: Union[IPv4Network, IPv6Network], subnet: Union[IPv4Network, IPv6Network]
) -> bool:
    """
    author: WatchMeSegfault (contributed on 2022-05-23 via Twitch)
    description: A faster (approx. 6.5x) subnet checker
    """
    super_version = 4 if isinstance(supernet, IPv4Network) else 6
    super_addr = int(supernet.network_address)
    super_prefix = supernet.prefixlen
    sub_version = 4 if isinstance(subnet, IPv4Network) else 6
    sub_addr = int(subnet.network_address)
    sub_prefix = subnet.prefixlen
    max_prefix = 32 if super_version == 4 else 128
    if super_version != sub_version:
        raise ValueError("ip version mismatch")
    if super_prefix > sub_prefix:
        return False
    mask = max_prefix - super_prefix
    return (super_addr >> mask) == (sub_addr >> mask)
