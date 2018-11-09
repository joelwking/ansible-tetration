# ansible-tetration
Ansible interface to Cisco Tetration Network Policy Publisher

This repository is a companion to the AnsibleFest 2018 network breakout session, *Using Ansible Tower to implement security policies and telemetry streaming for hybrid clouds*. 

The focus of the session illustrates using Ansible to facilitate installation of the software sensor on Linux hosts, how Cisco Tetration can be used as a dynamic inventory source for Ansible Playbooks and how policy generated from Tetration Application Dependency Mapping (ADM) Network Policy Publisher can be used to apply policy to a Cisco ACI fabric, Cisco ASA firewall and other network devices.

## Technical Marketing Collateral
### Blog
Refer to the [blog](https://www.wwt.com/all-blog/ansible-tower-implementing-security-policy) post for a summary of the concepts presented in this session at the live event.

### Code Exchange
Cisco DevNet Code exchange [links](https://developer.cisco.com/codeexchange/github/repo/joelwking/ansible-tetration) to this repository.

### Slides and Video
The AnsibleFest 2018 presentation slides are available on [Slideshare](https://www.slideshare.net/joelwking/using-ansible-tower-to-implement-security-policies-and-telemetry-streaming-for-hybrid-clouds).

On 2 November 2018 an update to the presentation was given to the WWT Network Solutions virtual team meeting, [Using Tetration for application security and policy enforcement in multi-vendor environments](https://www.slideshare.net/joelwking/using-tetration-for-application-security-and-policy-enforcement-in-multivendor-environments) A [recording](https://vimeo.com/298660860) of this session is available.

## Playbooks
### view_network_policy.yml
This playbook retrieves network policy from the Tetration Network Policy Publisher and creates a file to view the results. It is a data visualization and debugging tool.

### aci_create_filters.yml
The network policy returned from the publisher is used to create Filters and Filter entries in an ACI fabric. The AnsibleFest presentation includes screen snapshots of this use case.

### asa_create_acl.yml
Configuring a firewall using the published network policy is the primary use case of the Cisco Tetration Analytics Network Policy Publisher. This playbook illustrates how automation can be used to implement a zero-trust policy model on a firewall for defense in depth.

### setup_tetration_sensor.yml
This playbook demonstrates how Ansible can be used to assist in deploying the Tetration software agent on a CentOS virtual machine. Large customers may have hundereds of thousands of virtual machines which require the installation of the agent.

In Tetration release 3.1.1.x, there is a simplified software agent install, which eliminates much of the complexity of installing agents addressed by this playbook.

## Inventory
### sensors.py
This Python program interfaces to the Tetration API to retrieve and create a dynamic inventory file which can be used for Ansible playbooks. One benefit of deploying the Tetration agent on workloads, is using Tetration as another source of truth for network inventory.

The file `sensors.ini` is used to identify the target Tetration cluster and other parameters.

## Google Protocol Buffers
Tetration publishes policy to the Kafka message buffer encoded as protocol buffers. Protobufs provide better speed and efficiency for processing large amounts of data between publisher and subscriber. The source file `files/tetration_network_policy.proto` is the protobuf declaration of Tetration Network Policy's data structures published to Kafka. This file is compiled and imported by the module `tetration_network_policy.py`.

## Author
Joel W. King joel.king@wwt.com GitHub: @joelwking Principal Architect at World Wide Technology
