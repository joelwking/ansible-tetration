
# CONFIGURATION_GUIDE.md

## Network Policy Publisher 
The Tetration Network Policy Publisher uses a Kafka message broker for publishing network policy, which are seralized using Google ProtoBuffers.

### Kafka Python

I used the Kafka Python package rather than the Confluent Kafka package as Confluent did not provide a means to disable certification checking. The Tetration cluster installed in the Advanced Technology Center (ATC) used a self-signed certificate. In order to authenticate and bypass the certificate checking, I had to create an SSL context with CERT_NONE, no certificates from the server are required (or looked at if provided)) and reference the context to Kafka Python.

The Kafka Python [documentation.](https://media.readthedocs.org/pdf/kafka-python/master/kafka-python.pdf)

The KafaConsumer method requires Snappy for decompression. Python-snappy requires the Snappy C library. There is an example playbook later in this document which illustrates installing `libsnappy-dev`, `kafka-python`, and `python-snappy`.

### Protocol Buffers
The Tetration Kafka broker transports the Network Policy as a Google Protocol Buffer. To use Protocol Buffers in Python, you need three things:

* Tetration .proto definition file
* Python Protocol Buffer library
* Protocol buffer compiler

#### Definition file

#### Python Library

#### Compiler

### Setup for my Ubuntu development environment
##### Release
My development environment is running Ubuntu 16.04.05
```
$ lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 16.04.5 LTS
Release:        16.04
Codename:       xenial
```
##### Installing Required Packages

```YAML
#!/usr/bin/ansible-playbook
---
#      setup_ubuntu.yml
#
#
#      Copyright (c) 2018 World Wide Technology, Inc.
#      All rights reserved.
#
#      Author: joel.king@wwt.com
#
#      Usage: sudo ansible-playbook setup_ubuntu.yml --ask-become-pass
#
- name: Installs packages for my development environment
  hosts: localhost

  vars:
    packages:
      apt:
          - python-pip
          - python-dev
          - git
          - unzip                           # unzip utility
          - libsnappy-dev                   # install Snappy C library for python-snappy
      pip:
          - tetpyclient                    # Tetration 1.0.7
          - xlsxwriter                     # Tetration (Bruce Clounie)
          - pandas                         # Tetration (Bruce Clounie)
          - pymongo                        # MongoDB  3.6.1
          - netaddr                        # manulipulate network addresses 0.7.19
          - pyopenssl                      # ACI modules when using certificates for authentication 18.0.0
          - kafka-python                   # Kafka for Tetration 1.4.3
          - python-snappy                  # KafkaConsumer Snappy decompression (requires libsnappy-dev)  0.5.3
          - pydevd                         # Remote debugger for PyCharm 1.4.0

  tasks:
    - name: Determine OS
      debug:
         msg:  "{{ansible_pkg_mgr}}"           # 'apt' or 'yum'

    - name: Install the apt packages
      apt:
        name: "{{item}}"
        state: latest
      with_items: "{{packages.apt}}"
      when: ansible_pkg_mgr == 'apt'

    - name: Upgrade pip 
      command: "pip install --upgrade pip"

    - name: Install the python packages
      pip:
        name: "{{item}}"
        state: latest
        use_mirrors: no
      with_items: "{{packages.pip}}"

    - name: Upgrade all packages to the latest version
      apt:
      #  name: "*"
        state: latest
      become: true 
      when: ansible_pkg_mgr == 'apt'

    - name: Update all packages to the latest version
      apt:
        upgrade: dist
      become: true
      when: ansible_pkg_mgr == 'apt'
#          
```          
### Reference code
Example code provided by our Cisco counter parts.

[Policy consumer client implementation reference written in Go](https://github.com/tetration-exchange/pol-client-go)
[Tetration Network Policy Enforcement Client](https://github.com/tetration-exchange/pol-client-java)
