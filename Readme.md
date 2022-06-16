# CIDR-Bottle
![Release Badge](https://gitlab.com/geoip.network/cidr_bottle/-/badges/release.svg)
![Pipeline Badge](https://gitlab.com/geoip.network/cidr_bottle/badges/main/pipeline.svg)

CIDR-Bottle is yet another implementation of a Patricia Trie for handling network routing information (such as ROAs & Routing Tables) for reconciliation.
However, unlike other implementations it supports both sub-tree checking and longest-prefix matching.

![An attractive screenshot of the example code below](https://gitlab.com/geoip.network/cidr_bottle/-/raw/a57fe64864d8b05d71dde9ba32687319ca4fdbb8/screenshots/screenshot.png)

CIDR-Bottle was designed specifically to be used for reconciling RIR Allocation & Assignment records with actual BGP Announcements.
It isn't designed to be the fastest (it's written in pure python), but it should be the most full-featured implementation. 
That said, unless you're writing a routing engine in python (in which case I'd be really interested to know why), speed shouldn't be a significant issue.

## Dependencies
* [CIDR-Man](https://pypi.org/project/cidr-man/) *Thwip, Thwip!*

## Usage
### Initialisation
By default, a CIDR-Bottle is in IPv4 mode, to use IPv6 mode you must supply an IPv6 CIDR.

The root Bottle does not need to be the entire IP space, it can be any subnet.
```python
from cidr_bottle import Bottle
from ipaddress import IPv4Network, IPv6Network

## Defaults to IPv4
root = Bottle()  # 0.0.0.0/0

## IPv6 mode is initialised by passing an IPv6 CIDR (either as an instance of ipaddress.IPv6Network) 
root6 = Bottle(prefix=IPv6Network("::/0"))  # ::/0

## Supports detached (not starting at either 0.0.0.0/0 or ::/0) roots
detached_root = Bottle(prefix=IPv4Network("198.51.100.0/24"))
```

### Racking a Bottle (Inserting a node)
```python
## Supports insert with str
root.insert("198.51.100.0/24")

## Supports insert with instances of ipaddress.IPv4Network
root.insert(IPv4Network("198.51.100.0/24"))

## Supports insert with instances of ipaddress.IPv6Network
root.insert(IPv6Network("2001:db8::/48"))

## Supports attaching any json serializable objects to nodes **This is important for future planned releases**
root.insert("198.51.100.0/24", {"example": "dict"})
root.insert("198.51.100.0/24", "string example")

## Supports automatic aggregation on insert.
root.insert(CIDR("192.0.2.128/25"), value="a")
root.insert(CIDR("192.0.2.0/25"), value="b", aggregate=True)
root.insert(CIDR("192.0.3.0/24"), value="c", aggregate=True)
if root.get(CIDR("192.0.2.0/23")).value == "c":  
    ## This will evaluate as True as the two /25's will trigger the creation of the /24 and the addition of the other adjacent /24
    ## will trigger the creation of the /23 

## Supports dict-style indexing
root["198.51.100.0/24"] = "string example"
```

*Note: Setting `aggregate=True` will (if`node.parent.left` and `node.parent.right` are populated) insert the node as normal, automatically set the parent object to `passing=False`, 
and copy the `value` from the current insert to the `parent`.* 

### Contains CIDR?
Returns `True` where there is a covering prefix, otherwise false.
*NOTE: This means that it returns true 100% of the time when the root is `0.0.0.0/0` or `::/0`*
```python
if "198.51.100.0/24" in root:
    ## do something
### or
if root.contains("198.51.100.0/24"):
    ## do something
```
You can enforce exact matches by passing `exact=True` to the `contains` method.
```python
if not root.contains("198.51.100.128/25", exact=True):
    ## do something
```

### Drinking a Bottle (Get node)
This will return a matching covering prefix if present. 
In the case of a detached root, this means that it can return `None` if no such covering prefix exists.
*NOTE: This is longest prefix matching*
```python
print(root["198.51.100.0/24"])
### or
print(root.get("198.51.100.0/24"))
```
Similar to the `.contains(...)` method, you can enforce exact matches by passing `exact=True` to the `get` method. 
This will raise a `KeyError` if there is no exact match.
```python
print(root.get("198.51.100.128/25"), exact=True)  # will raise a KeyError("no exact match found")
```

### Children / Sub-Tree checking
With CIDR-Bottle you can retrieve all the defined children of a bottle(node).
```python
root.insert("198.51.100.0/25")
root.insert("198.51.100.128/25")
print(root["198.51.100.0/24"].children())
```

### Smashing bottles (Deleting Nodes)
Deleting an edge node removes it completely.

Deleting an intermediate node, converts it into a "passing" node, and does not affect any descendants of that node.
```python
del root["198.51.100.0/24"]
### or
root.delete("198.51.100.0/24")
```


## *More Speed*
If you want to squeeze out every last drop of performance and don't mind the limitation of being forced to use [CIDR-Man's](https://pypi.org/project/cidr-man/) `CIDR` then you can use `FastBottle` instead of `Bottle`.


## Installation (from pip):
```shell
pip install cidr_bottle
```

## Installation (from source):
```shell
git clone https://gitlab.com/geoip.network/cidr_bottle
poetry install
```