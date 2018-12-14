
# CONFIGURATION_GUIDE.md

## Intended Audience
This guide is a reference for installing the prerequisite software to install and execute the `tetration_network_policy` module on a control node running Ansible Engine and Ansible Tower. This guide does not describe how to configure Cisco Tetration, for that, refer to the documentation at www.cisco.com/go/tetration. 

The Network Policy Publisher is a Tetration feature which augments the zero trust enforcement of policy on hosts using the enforcement agent, by publishing the policy to a a Kafka instance running on the Tetration cluster. Authentication of the clients is enabled by downloading Kafka client certificates, the assigned Kafka topic and the broker IP address and port number.

The `tetration_network_policy` can be invoked from an Ansible playbook, retrieve the published policies, and then translate them to formats understood by security devices (firewalls and ACLs on routers) and load balancers.

This approach provides defense in depth, by implementing the same policy on the end host as well as on network and security devices.

## Network Policy Publisher 
The Tetration Network Policy Publisher uses a Kafka message broker for publishing network policy, which are serialized using Google Protocol Buffers. For a client to consume these messages using Python, a Kafka Python package (SDK) is installed, along with the protocol buffer library. To compile the source protocol buffer definition file, the protocol buffer compiler is also installed. Installing the compiler is optional, as the complied source is included in this repository.

### Kafka Python

The Kafka Python package was selected rather than the Confluent Kafka package. Confluent does not provide a means to disable certification checking. The Tetration cluster installed in the Advanced Technology Center (ATC) uses a self-signed certificate. In order to authenticate and bypass the certificate checking, the program creates an SSL context with CERT_NONE, no certificates from the server are required (or looked at if provided)) and provide the context to Kafka Python.

The Kafka Python [documentation](https://media.readthedocs.org/pdf/kafka-python/master/kafka-python.pdf) is used as reference.

The KafaConsumer method requires Snappy for decompression. Python-snappy requires the Snappy C library. Installing `libsnappy-dev`, `kafka-python`, and `python-snappy` is required to execute the program.

#### Install Ansible Engine
These instructions assume that Ansible has been installed to the target host. The software was developed using Ansible 2.6.4
and this configuration guide was validated using Ansible 2.7.4. Refer to the installation instructions for installing Ansible, at http://docs.ansible.com/ansible/intro_installation.html.

The development environment is running Ubuntu 16.04.05, refer to the output of  `lsb_release -a` to validate your release. The following commands are used to install Ansible on Ubuntu.

```
$ sudo apt-get install software-properties-common
$ sudo apt-add-repository ppa:ansible/ansible
$ sudo apt-get update
$ sudo apt-get install ansible
```

### Installing Required Packages
The following 'apt' and 'pip' packages and SDKs are required used this software. 

```YAML
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
          - ipaddress                      # manipulates IP addresses
          - pyopenssl                      # ACI modules when using certificates for authentication 18.0.0
          - kafka-python                   # Kafka for Tetration 1.4.3
          - python-snappy                  # KafkaConsumer Snappy decompression (requires libsnappy-dev)  0.5.3
          - pydevd                         # Remote debugger for PyCharm 1.4.0 (Optional)

```   

### Protocol Buffers
The Tetration Kafka broker transports the Network Policy as a Google Protocol Buffer. To use Protocol Buffers in Python, you need three things:

* Tetration .proto definition file
* Python Protocol Buffer library
* Protocol buffer compiler

The .proto definition file `tetration_network_policy.proto` is used by the compiler to generate a Python file `tetration_network_policy_pb2.py`. The module `tetration_network_policy.py` imports the compiled definition file. It in turn, imports from the Python Protocol Buffer library.

**tetration_network_policy.py**
```python
    import ansible.module_utils.network.tetration.tetration_network_policy_pb2     
```
**tetration_network_policy_pb2.py**
```python
        from google.protobuf import ...   
        # and so on
```
For these import statements to gain access to the code of the imported module, the modules must be referenced from the default Python path(s). The following steps install, copy or create the appropriate symbolic links.

#### Tetration .proto definition file  **REQUIRED**

The protocol buffer source file used in solution development was cut 'n past'ed from the Tetration appliance (version 2.3.1.41) at this URL, *https://<tetration_host>/documentation/ui/adm/policies.html#protobuf-definition-file* and saved as `files/tetration_network_policy.proto`.

This definition file is compiled by the protocol buffer compiler. The output generated is comprised of Python classes and methods to decode the policy generated by Tetration. The compiled protocol buffer is provided in the directory `/library`. You do not need to install the compiler and compile the .proto definition file. The instructions provided are for reference, should you wish to create your own .proto definition file for other applications.

If you choose not to install and compiler and compile the source .proto file, simply copy `tetration_network_policy_pb2.py` from `library`  to  `/usr/share/ansible/module_utils/network/tetration` and `sudo touch __init__.py` in that directory.

#### Python Protocol Buffer library **REQUIRED**

Refer to the Google Python tutorial, at  [https://developers.google.com/protocol-buffers/docs/pythontutorial](https://developers.google.com/protocol-buffers/docs/pythontutorial]), download the Python library.
```
$ cd /usr/share
$ sudo mkdir protobufs
$ cd protobufs
$ sudo wget https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protobuf-python-3.6.1.tar.gz
$ sudo gunzip protobuf-python-3.6.1.tar.gz
$ sudo tar xvf protobuf-python-3.6.1.tar
$ sudo rm protobuf-python-3.6.1.tar
```
Version 3.6.1 of the protocol buffer library is at this directory:
```
/usr/share/protobufs/protobuf-3.6.1
```
#### Create the target directory **REQUIRED**
You can either compile the source .proto file or download the compiled result, `tetration_network_policy_pb2.py` from `library`. In either case, you must verify the Python module can be imported.

```
cd /usr/share/
$ sudo mkdir ansible ansible/module_utils ansible/module_utils/network  ansible/module_utils/network/tetration
```
Make Python treat the directory as containing a package.
```
$ sudo touch /usr/share/ansible/module_utils/network/tetration/__init__.py 
```

#### Protocol buffer compiler **OPTIONAL**
This section includes instructions for installing the Protocobuf3 compiler. These [instructions](https://gist.github.com/rvegas/e312cb81bbb0b22285bc6238216b709b) are a useful reference.

Install the precompiled binary version of the protocol buffer compiler (protoc).

Download and unzip the [file](https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protoc-3.6.1-linux-x86_64.zip). Given a work directory at `/usr/share/protobufs` . 

```
$ cd /usr/share/protobufs
$ sudo wget https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protoc-3.6.1-linux-x86_64.zip
$ sudo unzip protoc-3.6.1-linux-x86_64.zip -d protoc3
```
###### Move protoc to /usr/local/bin/
```
sudo mv protoc3/bin/* /usr/local/bin/
```
###### Move protoc3/include to /usr/local/include/
```
sudo mv protoc3/include/* /usr/local/include/
```
The only file remaining in `~/protobufs/protoc3` is the readme.txt. The work directory can be removed if desired.

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
###### Optionally delete the zip file
``` 
sudo rm  protoc-3.6.1-linux-x86_64.zip
```

##### Compile the .proto file
This section documents how to compile a source .proto file and create the resulting Python classes and methods. The Google tutorial syntax for compilation of the .proto file is:
```
protoc -I=$SRC_DIR --python_out=$DST_DIR $SRC_DIR/addressbook.proto
```

In the following steps, you must create the target directory. You have the option to either compile the protocol definition file `.proto`, or simply download the compiled result, the generated Python file.

##### Compile from source
Follow these steps if you wish to compile from source.

###### Download the source file
If you wish to compile the source file, download the `.proto` source file.
```
$ cd /usr/share/ansible/module_utils/network/tetration/
$ sudo wget https://raw.githubusercontent.com/joelwking/ansible-tetration/master/files/tetration_network_policy.proto
```
###### Run the compiler
Assuming the .proto file is `/usr/share/ansible/module_utils/network/tetration/tetration_network_policy.proto`, write the output to the same directory as the source code `/usr/share/ansible/module_utils/network/tetration/`, invoke the compiler:
```
$ sudo protoc -I=/usr/share/ansible/module_utils/network/tetration --python_out=/usr/share/ansible/module_utils/network/tetration /usr/share/ansible/module_utils/network/tetration/tetration_network_policy.proto
```

#### Download the generated Python file **OPTIONAL**
If you skipped compiling the `.proto` file, download the compiled result, `tetration_network_policy_pb2.py' tetration_network_policy_pb2.py` from `library`.

```
$ cd /usr/share/ansible/module_utils/network/tetration/
$ sudo wget https://raw.githubusercontent.com/joelwking/ansible-tetration/master/library/tetration_network_policy_pb2.py
```

#### Verify the resulting Python module

The protocol compiler generates a Python module which imports modules from the Python Protocol Buffer library. Set the environmental variable PYTHONPATH.
```
export PYTHONPATH=/usr/share/protobufs/protobuf-3.6.1/python
```
Invoke the interactive Python interpreter to verify the compiled .proto file.
```
$ cd /usr/share/ansible/module_utils/network/tetration/
$ python
Python 2.7.12 (default, Nov 12 2018, 14:36:49)
[GCC 5.4.0 20160609] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import tetration_network_policy_pb2
```
If the import statement raises an `ImportError` there is a likely an issue with the .proto file.

##### View the documentation
Issue the following command to view the documentation of the compiled .proto file.
```
$ pydoc tetration_network_policy_pb2
```

##### Tutorial on using the Tetration Network Policy protocol buffer
There are limited tutorials on using Python and protocol buffers. Protocol buffers are efficient by using integers instead of strings to represent keys and values. For example, the CatchAllPolicy for an intent is either ALLOW or DENY. These are values are transmitted between publisher and client as a value of 1 or 2.

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
To 'decode' the value of 1 or 2, we can derive a meaningful name to the value of `catch_all.action` with:

```
>>> import tetration_network_policy_pb2 as tnp
>>> tnp.CatchAllPolicy.Action.Name(1)
'ALLOW'
>>>>
```
IPAddressFamily example:
```
enum IPAddressFamily {
  INVALID = 0;
  IPv4 = 1;
  IPv6 = 2;
};
```
Use the Name method to decode the values provided.
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

#### Ansible Configuration file
The Ansible configuration file, `ansible.cfg` must specify a location to look for the `tetration_network_policy.py` module and the protocol buffer module, `tetration_network_policy_pb2.py`.

Modify the `/etc/ansible/ansible.cfg` file to include:
```
library        = /usr/share/ansible/
module_utils   = /usr/share/ansible/module_utils/
```
and copy (or move) `tetration_network_policy.py` to the directory specified as the `library` and  `tetration_network_policy_pb2.py` to the directory specified by the `module_utils`.

```
$ cd /usr/share/ansible
$ sudo wget https://raw.githubusercontent.com/joelwking/ansible-tetration/master/library/tetration_network_policy.py
$ chmod 755 tetration_network_policy.py
```

##### Verify configuration updates
The configured module search path now references directory `/usr/share/ansible`.
```
$ ansible --version
ansible 2.7.4
  config file = /etc/ansible/ansible.cfg
  configured module search path = [u'/usr/share/ansible']
  ansible python module location = /usr/lib/python2.7/dist-packages/ansible
  executable location = /usr/bin/ansible
  python version = 2.7.12 (default, Nov 12 2018, 14:36:49) [GCC 5.4.0 20160609]
```
Verify Ansible can located the module, issue the `ansible-doc` command.
```
$ ansible-doc tetration_network_policy
```

#### Create symbolic link for the Python Protocol Buffer library
Creating a symbolic link provides a means to import the library and install multiple versions of the library.

```
$ cd /usr/lib/python2.7/dist-packages
$ sudo ln -s /usr/share/protobufs/protobuf-3.6.1/python/google google
```

#### Create symbolic link for the complied protocol buffer source file
Creating this symbolic link enables referencing the Tetration protocol buffer definition.
```
$ cd /usr/lib/python2.7/dist-packages/ansible/module_utils/network
$ sudo ln -s /usr/share/ansible/module_utils/network/tetration tetration
```

#### Verification
Verify the complied protocol buffer file can be imported using the interactive Python interpreter.
```
$ unset PYTHONPATH
$ cd /usr/share/ansible
$ python
Python 2.7.12 (default, Nov 12 2018, 14:36:49)
[GCC 5.4.0 20160609] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import ansible.module_utils.network.tetration.tetration_network_policy_pb2
>>>
```

Verify running `tetration_network_policy.py` as an Ansible module.

```
$ ansible localhost -m tetration_network_policy -a "broker='192.0.2.1:9093' topic='Tnp-12'"                    
[WARNING]: provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'

localhost | FAILED! => {
    "changed": false,
    "msg": "missing required arguments: cert_directory
```    
The above error message is expected, as the certificate directory has not been specified. This error does, however, validate the import statements have executed successfully.

### Library 
This table represents where the components of this solution are installed on the target system.

| **Diretory**                     | **Source**   | **Target Description**       |
|----------------------------------|--------------|-------------------------------|
| /usr/share/protobufs/   | https://github.com/protocolbuffers/protobuf/releases/download/v3.6.1/protobuf-python-3.6.1.tar.gz | unzip / tar |
| /usr/share/protobufs/protobuf-3.6.1/python/google | n/a | target of symlink |
| /usr/lib/python2.7/dist-packages | symlink      |  google -> /home/administrator/protobufs/protobuf-3.6.1/python/google       |           
| /usr/lib/python2.7/dist-packages/ansible/module_utils/network  | symlink      |  tetration -> /usr/share/ansible/module_utils/network/tetration  |
| /usr/share/ansible               | ansible.cfg  | library        = /usr/share/ansible/ |
| /usr/share/ansible/tetration_network_policy.py | cp | tetration_network_policy.py from {{playbook_dir}}/library |
| /usr/share/ansible/module_utils  | ansible.cfg  | module_utils = /usr/share/ansible/module_utils/ |
| /usr/share/ansible/module_utils/network/tetration | cp |  tetration_network_policy_pb2.py from {{playbook_dir}}/library |


### Install Ansible Tower
Ansible engine has been installed to the control node and we have verified execution of the program, install Ansible Tower by following these instructions:

[Ansible Tower Quick Installation Guide v3.3.2](
https://docs.ansible.com/ansible-tower/latest/html/quickinstall/prepare.html)

After installation, apply your license via the GUI. Tested using Tower 3.3.2 and Ansible 2.7.4.
  
#### Authenticating with the Kafka Broker

To access the Kafka Broker, download the certificates, name of the Kafka topic, broker IP address and port number.

Refer to [Using Tetration for application security and policy enforcement in multi-vendor environments](https://www.slideshare.net/joelwking/using-tetration-for-application-security-and-policy) specifically slide 21 for an overview of configuring the Tetration Network Policy Publisher. The URL to download the compressed tar file is `https://<tetration>/#/maintenance/lab_admin/datataps`. 

The filename will be include the Kafka topic name, for example, `producer-tnp-12.cert.tar.gz`.  Uncompress and extract the files. The result should look like the following:
```
producer-tnp-12.cert
├── kafkaBrokerIps.txt
├── KafkaCA.cert
├── KafkaConsumerCA.cert
├── KafkaConsumerPrivateKey.key
└── topic.txt
```
Note: These **files are not encrypted!** Treat the contents as credentials, which they are.

#### Encrypt the credentials with Ansible Vault
Encrypting the credentials enables storing them within the version control system along with the playbooks to retrieve and apply the policy to network devices using the suite of Ansible network modules.
```
$ ansible-vault encrypt  KafkaConsumerPrivateKey.key --ask-vault
New Vault password:
Confirm New Vault password:
Encryption successful
```
Make a note of the password, it will later need be stored as a credential on Ansible Tower.

#### Configure Ansible Tower
Ansible Tower offers a GUI and API for configuration and management. Rather than document the Ansible Tower configuration using screen snapshots, the following uses tower-cli, a command line tool for Ansible Tower. It allows Tower commands to be run from the UNIX command line. 

##### Install tower-cli
It is possible to install the tower-cli package on the control node running Ansible Tower. Alternately, use Vagrant and VirtualBox on a laptop to create a Linux instance.  The following is a sample `vagrantfile` which creates an ephemerial VM to configure the control node.
```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :
#
# All Vagrant configuration for Ansible Tower CLI
#
Vagrant.configure(2) do |config|

  config.vm.box = "ubuntu/xenial64"
  config.vm.provision "shell", inline: <<-SHELL
  sudo apt-get update
  sudo apt-get install python-pip -y
  sudo pip install ansible-tower-cli
  SHELL
end
```
Use `vagrant up` and when the VM is running, connect using  `vagrant ssh` and issue the commands in the next sections. When complete, exit the shell and issue `vagrant destroy` to destroy the VM.

##### Set credentials
In this example, the Tower control node is `ansible-tower-33.sandbox.wwtatc.local`. Specify the username and password used for administration.

```

tower-cli config host ansible-tower-33.sandbox.wwtatc.local
tower-cli config username admin
tower-cli config password redacted
tower-cli config verify_ssl  no
```
#### Store the vault credentials
Previously Ansible Vault was used to encrypt the credentials downloaded from Tetration. Create a vault credential in Tower. The variable `credential-type` is set with a value of 3, which indicates a vault credential type.

```
tower-cli credential create  --name producer-tnp-12 \
     --description joel.king@wwt.com \
     --credential-type 3 \
     --organization 1 \
     --inputs '{"vault_password": "redacted", "vault_id": ""}'
Resource changed.
== =============== ===============
id      name       credential_type
== =============== ===============
 7 producer-tnp-12               3
== =============== ===============
```
Make a note of the credential id number  from the command output. It will be needed in a subsequent step.

#### Create a project
Projects are associated with a repository containing playbooks and files. Review the sample repository at https://gitlab.com/tetration-network-policy-publisher/producer-tnp-12. In step **Authenticating with the Kafka Broker**, the credentials, topic and broker IP address and port were downloaded from Tetration. The credentials were encrypted with Vault. Upload these files to your repo. Use the directory format conventions from the sample repository.

Create the project.

```
 tower-cli project create --name producer-tnp-12 \
 --description joel.king@wwt.com \
 --scm-type git \
 --scm-url  https://gitlab.com/tetration-network-policy-publisher/producer-tnp-12.git \
 --scm-branch  master \
 --scm-clean true \
 --scm-delete-on-update true \
 --scm-update-on-launch true
Resource changed.
== =============== ======== ========================================================================= ====================
id      name       scm_type                                  scm_url                                       local_path
== =============== ======== ========================================================================= ====================
13 producer-tnp-12 git      https://gitlab.com/tetration-network-policy-publisher/producer-tnp-12.git _13__producer_tnp_12
== =============== ======== ========================================================================= ====================
```
Make a note of the project id from the command output. It will be needed in a subsequent step.

#### Inventory
Because this solution runs in the control node, there is no requirement to create an inventory on the Ansible Tower machine. The default 'localhost' is sufficient. Either create an inventory or use the default inventory. You will need to specify an inventory id in a subsequent step.

##### List available inventory
Issue the following command to list all available inventory. Make a note of the appropriate inventory id.

```
tower-cli inventory list
== ============== ============
id      name      organization
== ============== ============
 1 Demo Inventory            1
== ============== ============
```

#### Create a job template
Create a job template to execute a playbook. The job template references the vault credentials, the project and the inventory. The playbook referenced must be present in the repository specified in the project.

Substitute the project, inventory and credential id in the following configuration.
```
tower-cli job_template create --name view_network_policy \
--description joel.king@wwt.com \
--job-type run \
--project 13 \
--playbook view_network_policy_decrypt.yml \
--vault-credential 7 \
--inventory 1
Resource changed.
== =================== ========= ======= ===============================
id        name         inventory project            playbook
== =================== ========= ======= ===============================
14 view_network_policy         1      13 view_network_policy_decrypt.yml
== =================== ========= ======= ===============================
```

#### Execute the playbook
The job template can be executed from the Tower GUI or launched by
```
tower-cli job launch -J 14
```
The sample playbook returns the latest network policy published to the message bus and formats the output representing the CLI commands needed to create an access list on a Cisco ASA firewall. For each port and protocol in the policy you should see a debug message line which looks similar to the following.

```
"msg": "access-list OUTSIDE line 1 extended permit udp any object-group SERVERS eq 161",
```

#### Examples
Source code for the TetrationNetworkPolicyProto definition file is available from the Tetration appliance GUI, or can be downloaded from the tetration-exchange repo: https://github.com/tetration-exchange/pol-client-java/blob/master/proto/network_enforcement/tetration_network_policy.proto. 

Example code in the `tetration-exchange` repo:

* [Policy consumer client implementation reference written in Go](https://github.com/tetration-exchange/pol-client-go)
* [Tetration Network Policy Enforcement Client](https://github.com/tetration-exchange/pol-client-java)

## Author
joel.king@wwt.com GitHub / GitLab @joelwking 