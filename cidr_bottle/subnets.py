from ipaddress import IPv4Network, IPv6Network
from typing import Union


def subnet_of(
    supernet: Union[IPv4Network, IPv6Network], subnet: Union[IPv4Network, IPv6Network]
) -> bool:
    """
    author: WatchMeSegfault (contributed on 2022-05-23 via Twitch)
    description: A faster (approx. 6.5x) subnet checker
    """
    if supernet.version != subnet.version:
        raise ValueError("ip version mismatch")
    if supernet.prefixlen > subnet.prefixlen:
        return False
    a = int(supernet.network_address)
    b = int(subnet.network_address)
    mask = supernet.prefixlen
    return (a >> supernet.max_prefixlen - mask) == (b >> supernet.max_prefixlen - mask)
