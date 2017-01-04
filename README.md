# Network device config parser

NDCP is a network device config parser. Given either a snippet of configuration or a full configuration along with a yaml file describing the config, a visual representation of the parsed config and resulting structured data file in yaml format will be presented.

***This is an early release which has not been fully tested or documented. Please use with caution.  The code is undocumented and has little error checking.***

![screenshot](https://github.com/cidrblock/parse/raw/master/screenshot.png)

## Dependancies

1. bower
2. python
3. flask (pip install)

## Installing

1. Clone this repo
2. Install dependancies
```
cd parse
bower install
```
3. Start the server
```
./server.py
```
Point your web browser to http://localhost:5000/

## Overview

The screen is broken into four sections:
1. The config or configlet to parse
2. The parsing template in yaml format
3. The post parsed config
4. The resulting structured data

Once sections one and two are populated, the submit the config with ctrl/command-shift-r.

Additionally, the parsing template can be sorted with ctrl/command-shift-s.

## Getting Started

The parsing template is best explained with examples. Parsing happens left to right, top to bottom in the config.

The parsing template is made up of lists and dictionaries, keywords and variables.

### Example 1:

Given the following configlet and template:

```
!
logging buffered informational

!

!
```
```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  logging:
    buffered:

```

Blank lines will be removed, and the parser will look for the the keyword `logging` followed by `buffered`.  The following result will be produced:

```
logging:
  buffered:
    values:
    - informational
```
Anything not parsed, will simple reside in a list of values.

### Example 2:

Variables can be used instead of hard-coded keywords.  Variables start with a `$`.  The variable (less the `$`)
will be the keyword in the resulting output.


Configlet:
```
logging buffered informational
logging console informational
logging monitor informational
```
Template:
```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  logging:
  - $type
```
Result:
```
logging:
- type: buffered
  values:
  - informational
- type: console
  values:
  - informational
- type: monitor
  values:
  - informational
```
### Example 3:

By default, the remainder of the line will be placed in a list of values as above.  This can be overwritten with a remainders dictionary.

Configlet:

```
service timestamps debug datetime msec localtime show-timezone
service timestamps log datetime msec localtime show-timezone

```

Template:

```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  service:
    timestamps:
    - $type
    - remainder: modify
```
Result:

```
service:
  timestamps:
  - modify:
    - datetime msec localtime show-timezone
    type: debug
  - modify:
    - datetime msec localtime show-timezone
    type: log
```

if the remainder keyword is plural (ends in s), the remainder will be split into a list of values rather than a string.

Template:
```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  service:
    timestamps:
    - $type
    - remainder: modifiers
```
Result:
```
service:
  timestamps:
  - modifiers:
    - datetime
    - msec
    - localtime
    - show-timezone
    type: debug
  - modifiers:
    - datetime
    - msec
    - localtime
    - show-timezone
    type: log
```
### Example 4:

Multiline configlets can be parsed into lists of entries.

Configlet:
```
access-list 5 permit 10.0.0.1
access-list 5 permit 10.0.0.2
access-list 5 permit 10.0.0.3
access-list 5 permit 10.0.0.4

access-list 16 deny   10.1.0.0 0.0.0.255
access-list 16 deny   10.2.0.0 0.0.0.255
access-list 16 permit any
```
Template:
```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  access-list:
    $number:
    - $action
    - $src
    - $src_mask
```
Result:
```
access-list:
- entries:
  - action: permit
    src: 10.0.0.1
  - action: permit
    src: 10.0.0.2
  - action: permit
    src: 10.0.0.3
  - action: permit
    src: 10.0.0.4
  number: '5'
- entries:
  - action: deny
    src: 10.1.0.0
    src_mask: 0.0.0.255
  - action: deny
    src: 10.2.0.0
    src_mask: 0.0.0.255
  - action: permit
    src: any
  number: '16'
```
In the case the access-list number was stored as number: XXX and the entries are a list of entries, each with a dictionary of values.  The line was parsed left to right using the list of variables.

### Example 5:

Keywords can be removed from the config by duplicating variable names. For instance, there is little value in storing the `use-vrf` keyword in the result.

Configlet:
```
ntp server 10.1.1.2 use-vrf blue
ntp server 10.1.1.3 use-vrf red
ntp server 10.1.1.4 use-vrf green
ntp server 10.1.1.5 use-vrf yellow
```
Template:
```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  ntp:
    server:
      $ip:
      - $vrf
      - $vrf
```
Result:
```
ntp:
  server:
  - entries:
    - vrf: blue
    ip: 10.1.1.2
  - entries:
    - vrf: red
    ip: 10.1.1.3
  - entries:
    - vrf: green
    ip: 10.1.1.4
  - entries:
    - vrf: yellow
    ip: 10.1.1.5
```
Because the `$vrf` keyword was repeated, it was initially set to `use-vrf` but then overwritten with the vrf name.

### Example 6:

Working with contexts.  (indented configuration sections).  Parsing a line's context is only different than parsing global configuration in that the context's parsing keywords should be stored in the context keyword.

Configlet:
```
ip access-list standard test
 permit 1.1.1.1
 permit 1.1.1.3
 permit 1.1.1.2
 permit 1.1.1.4

interface GigabitEthernet0/0/1
 description uplink
 ip address 10.0.0.1 255.255.255.0
 ip flow ingress
 ip flow egress
 ip pim sparse-dense-mode
 negotiation auto
 service-policy input qo-global-core-ingress-lan
!
interface GigabitEthernet2/10
 description connection to switch
 switchport
 switchport trunk encapsulation dot1q
 switchport trunk native vlan 5
 switchport trunk allowed vlan 99,2199,2299,2399,2499,2599,2699
 switchport trunk allowed vlan add 2799,2899,2999,3099,3199,3299,3399
 switchport trunk allowed vlan add 3485,3499,3599,3699
 switchport mode trunk
 speed nonegotiate
 mls qos trust dscp
```
Template:
```
config:
  remove_lines:
  - ^!.*$
  - ^$
global_keywords:
  interface:
  - $name
  - context:
      description:
      ip:
        address:
        - $ip
        - $mask
        flow:
        - $direction
        pim:
        - $mode
      mls:
      negotiation:
      service-policy:
      - $direction
      - $policy_name
      speed:
      switchport:
        mode:
        trunk:
          allowed:
          encapsulation:
          native:
          - $vlan
          - $vlan
  ip:
    access-list:
      standard:
      - $name
      - context:
        - $action
        - $src
        - $src_mask
```
Result:
```
interface:
- context:
    description:
      values:
      - uplink
    ip:
      address:
      - ip: 10.0.0.1
        mask: 255.255.255.0
      flow:
      - direction: ingress
      - direction: egress
      pim:
      - mode: sparse-dense-mode
    negotiation:
      values:
      - auto
    service-policy:
    - direction: input
      policy_name: qo-global-core-ingress-lan
  name: GigabitEthernet0/0/1
- context:
    description:
      values:
      - connection to switch
    mls:
      values:
      - qos trust dscp
    speed:
      values:
      - nonegotiate
    switchport:
      mode:
        values:
        - trunk
      trunk:
        allowed:
          values:
          - vlan 99,2199,2299,2399,2499,2599,2699
          - vlan add 2799,2899,2999,3099,3199,3299,3399
          - vlan add 3485,3499,3599,3699
        encapsulation:
          values:
          - dot1q
        native:
        - vlan: '5'
  name: GigabitEthernet2/10
ip:
  access-list:
    standard:
    - context:
      - action: permit
        src: 1.1.1.1
      - action: permit
        src: 1.1.1.3
      - action: permit
        src: 1.1.1.2
      - action: permit
        src: 1.1.1.4
      name: test
```
Each context for each global line is stored as `context` in the result.

All other parsing rules apply.

Note: The 'trunk allowed' lines above are one of the use cases not covered, that is conditional keywords.  Two of the lines have the `add`, one does not.

## Built With

* angular
* python
* angular-ui-ace
* flask
* bower
* ace editor
* highlightjs

## Contributing

Please do.

## Versioning

soon.

## Authors

* **Bradley Thornton** - *Initial work* - [cidrblock](https://github.com/cidrblock)

## License

This project is licensed under the MIT License. [MIT License](http://www.opensource.org/licenses/MIT).

## Acknowledgments

* Angular, Ace, Python
