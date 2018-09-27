
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

The .proto definition file `tetration_network_policy.proto` is used by the compiler to generate a Python file `tetration_network_policy_pb2.py` for import to your program. 

#### Definition file
You will need the source code for the TetrationNetworkPolicyProto definition file. It is available from the Tetration appliance GUI, or you could download from the tetration-exchange repo:

```
https://github.com/tetration-exchange/pol-client-java/blob/master/proto/network_enforcement/tetration_network_policy.proto
```
This definition file is compiled by the protocol buffer compiler.

#### Python Library

Following instructions from the Google Python tutorial, at  [https://developers.google.com/protocol-buffers/docs/pythontutorial](https://developers.google.com/protocol-buffers/docs/pythontutorial]), download the Python library.
```

~/protobufs$ wget https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protobuf-python-3.6.1.tar.gz
~/protobufs$gunzip protobuf-python-3.6.1.tar.gz
```
In our program, we `import tetration_network_policy_pb2`, which requires using your PYTHONPATH to be configured so the directories of the Python library and the compiled protocol buffer definition is available.
```
~/protobufs/protobuf-3.6.1/python
~ tetration/ansible-tetration/library
```

#### Compiler Install instructions for Protocobuf3

We are installing a precompiled binary version of the protocol buffer compiler (protoc).

I used [these](https://gist.github.com/rvegas/e312cb81bbb0b22285bc6238216b709b) instructions as a guide.

Download and unzip the file. I have a directory at `~/protobufs` as a work area. I used [https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protoc-3.6.1-linux-x86_64.zip](https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protoc-3.6.1-linux-x86_64.zip).

```
~/protobufs$ wget https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protoc-3.6.1-linux-x86_64.zip
~/protobufs$ unzip protoc-3.6.1-linux-x86_64.zip -d protoc3
```
###### Move protoc to /usr/local/bin/
```
sudo mv protoc3/bin/* /usr/local/bin/
```
###### Move protoc3/include to /usr/local/include/
```
sudo mv protoc3/include/* /usr/local/include/
```
At this point, the only files remaining in `~/protobufs/protoc3` will be the readme.txt. You can remove the directory if you wish.

###### Optional: change owner
```
sudo chown $USER /usr/local/bin/protoc
sudo chown -R $USER /usr/local/include/google
```
###### Verify the version
```
~/protobufs$ which protoc
/usr/local/bin/protoc
administrator@flint:~/protobufs$ protoc --version
libprotoc 3.6.1
```

#### Compile the .proto file
The Google tutorial provides the syntax for compilation of the .proto file:
```
protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto
```
Assuming we have saved the .proto file as `/files/tetration_network_policy.proto` and we want to write the output to the same directory as our source code `/library/`, invoke the compiller:
```
protoc -I=/ansible-tetration/files/ --python_out=/ansible-tetration/library/ /ansible-tetration/files/tetration_network_policy.proto
```
You can view the source code but do not edit the file.

#### Print help

You can use the interactive Python interpreter to print the help from the compiled .proto file:

```python
import tetration_network_policy_pb2

import pydoc
help = pydoc.render_doc(tetration_network_policy_pb2, "Help on %s")
f = open("/tmp/tetration_network_policy_pb2.txt", 'w+')
print >>f, help
f.close()
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

### Authenticating with the Kafka Broker

THIS SECTION INTENTIONALLY LEFT BLANK

### Tips for using the protocol buffer methods
There are limited tutorials on using Python and protocol buffers, here are some notes:

Review the `.proto` file, for example:

```
// CatchAll policy action.
message CatchAllPolicy {
  enum Action {
    INVALID = 0;
    // Allow the corresponding flows.
    ALLOW = 1;
    // DROP the corresponding flows.
    DROP = 2;
  };
  Action action = 1;
}
```
We can derive a meaningful name to the value of catch_all.action with:
```python
import tetration_network_policy_pb2 

    ### assume the buffer is stored in policy.buffer 
    tnp = policy.buffer.tenant_network_policy
    for item in tnp.network_policy:
        print ('catch_all', tetration_network_policy_pb2.CatchAllPolicy.Action.Name(item.catch_all.action))

('catch_all', 'ALLOW')        
```
The same goes for things like IPAddressFamily:
```
enum IPAddressFamily {
  INVALID = 0;
  IPv4 = 1;
  IPv6 = 2;
};
```
You can use the Name method to decode the values provided.
```
>>> import tetration_network_policy_pb2 as tnp
>>> tnp.IPAddressFamily.Name(0)
'INVALID'
>>> tnp.IPAddressFamily.Name(1)
'IPv4'
>>> tnp.IPAddressFamily.Name(2)
'IPv6'
>>> try:
...     tnp.IPAddressFamily.Name(3)
... except ValueError as e:
...     print e
...
Enum IPAddressFamily has no name defined for value 3
>>>
```

### Reference and notes
Example code in the `tetration-exchange` repo:

[Policy consumer client implementation reference written in Go](https://github.com/tetration-exchange/pol-client-go)
[Tetration Network Policy Enforcement Client](https://github.com/tetration-exchange/pol-client-java)

My development environment is running Ubuntu 16.04.05
```
$ lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 16.04.5 LTS
Release:        16.04
Codename:       xenial
```
## Author
joel.king@wwt.com GitHub / GitLab @joelwking 