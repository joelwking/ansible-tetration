# ansible-tetration
Ansible interface to Cisco Tetration Network Policy Publisher

This solution exposes the security policy generated from Tetration Analytics Application Dependency Mapping (ADM) Network Policy Publisher to data center switches, firewalls, load balancers and other network devices supported by the Ansible network modules.  Ansible playbooks can call the module `tetration_network_policy` to retrieve policy from the Tetration Kafka broker. The module returns the policy to the playbook as *ansible_facts* - which can be referenced by subsequent tasks to apply the policy to devices, write it to a file, or load it to CMDB for reference.

## DevNet Code Exchange
This repository is featured on the Cisco DevNet Code Exchange.

[![published](https://static.production.devnetcloud.com/codeexchange/assets/images/devnet-published.svg)](https://developer.cisco.com/codeexchange/github/repo/joelwking/ansible-tetration)

## Articles and Blogs
Cisco has featured this solution in several blog posts published in the developer section of [blogs.cisco.com](https://blogs.cisco.com) and in [ComputerWeekly.com](https://www.computerweekly.com) leading to DevNet Create 2019.

* [Introducing Cisco DevNet Exchange](https://blogs.cisco.com/developer/introducing-devnet-exchange)
* [Using Tetration for Application Security and Policy Enforcement](https://blogs.cisco.com/developer/tetration-for-security)
* [Coders and developers: The new heroes of the network?](https://www.computerweekly.com/news/252457087/Coders-and-developers-the-new-heroes-of-the-network)

## DevNet Create 2019

At [devnetcreate.io](https://devnetcreate.io) this solution is part of the Tech Talk on Wednesday Apr 24, 2019 2:20pm - 2:40pm at the Computer History Museum titled *Analytics for Application Security and Policy Enforcement in Cloud Managed Networks*. The presentation is available on SlideShare at [https://www.slideshare.net/joelwking/analytics-for-application-security-and-policy-enforcement-in-cloud-managed-networks](https://www.slideshare.net/joelwking/analytics-for-application-security-and-policy-enforcement-in-cloud-managed-networks).

Development of this solution gained recognition as a DevNet Creator community contributor during the [Key Note](https://youtu.be/XyK_8ethwNk?t=4601) session.

There is a video interview hosted by Silvia K. Spiva, community manager DevNet with [DevNet Creator Joel King](https://youtu.be/mxn_zxmhe3s).

## Ansible Durham Meetup

[*Enabling policy migration in the Data Center with Ansible*](https://www.meetup.com/Ansible-Durham/events/260264063/) - Wednesday, April 17, 2019

The internal World Wide Technology IT department is migrating from a traditional Nexus fabric to Application Centric Infrastructure (ACI). This talk describes how Ansible is used to migrate policy to, and automate the configuration of, the new data center fabric.

## AnsibleFest Austin 2018 
This repository is a companion to the AnsibleFest 2018 network breakout session, *Using Ansible Tower to implement security policies and telemetry streaming for hybrid clouds*. 

The focus of the session illustrates using Ansible to facilitate installation of the software sensor on Linux hosts, how Cisco Tetration can be used as a dynamic inventory source for Ansible Playbooks and how policy generated from Tetration Application Dependency Mapping (ADM) Network Policy Publisher can be used to apply policy to a Cisco ACI fabric, Cisco ASA firewall, and other network devices.

A recap of AnsibleFest in this [blog](https://www.wwt.com/all-blog/ansible-tower-implementing-security-policy) post summarizes the concepts presented in this session at the live event.

The AnsibleFest 2018 presentation slides are available on [Slideshare](https://www.slideshare.net/joelwking/using-ansible-tower-to-implement-security-policies-and-telemetry-streaming-for-hybrid-clouds).

On 2 November 2018, an update to the presentation was given to the WWT Network Solutions virtual team meeting, [Using Tetration for application security and policy enforcement in multi-vendor environments](https://www.slideshare.net/joelwking/using-tetration-for-application-security-and-policy-enforcement-in-multivendor-environments). A [recording](https://vimeo.com/298660860) of this session is available.

Red Hat has published the collateral from [AnsibleFest Austin 2018](https://www.ansible.com/resources/videos/ansiblefest-austin-2018) this session is at [https://www.ansible.com/using-ansible-tower-to-implement-security-policies-telemetry-streaming](https://www.ansible.com/using-ansible-tower-to-implement-security-policies-telemetry-streaming).

## Configuration Guide
This solution has been verified and tested using Ansible 2.7.4 running with Ansible Tower 3.3.2. The `CONFIGURATION_GUIDE.md` provides a reference for installing the software for the target environment. The group referenced by Ansible Tower 'projects' is at this URL: [https://gitlab.com/tetration-network-policy-publisher](https://gitlab.com/tetration-network-policy-publisher).

## Playbooks
Several sample Ansible playbooks are included and are described in the following section.

### view_network_policy.yml
This playbook retrieves network policy from the Tetration Network Policy Publisher and creates a file to view the results. It is a data visualization and debugging tool.

### view_network_policy_decrypt.yml
This playbook resides on GitLab, as [view_network_policy_decrypt.yml](https://gitlab.com/tetration-network-policy-publisher/policy-stream-12-pub-vrf/blob/master/view_network_policy_decrypt.yml). The GitLab repo, https://gitlab.com/tetration-network-policy-publisher/policy-stream-12-pub-vrf is an example of how to organize credentials and playbooks for multiple applications, under a single 'group', [tetration-network-policy-publisher](https://gitlab.com/tetration-network-policy-publisher). For example, under the group, each application identifed by an Application Dependency Mapping (ADM), is identified by the topic assigned by Tetration. One example is the 'producer-tnp-12' repo in the group.

This is a public repo and the credentials are AES256 encrypted with Ansible Vault. The playbook provides an example of how to decrypt and temporarily store the credentials on Tower, execute the playbook and then delete the decrypted files at the end of the playbook.

### asa_create_acl_decrypt.yml 
This playbook resides on GitLab, as [asa_create_acl_decrypt.yml](https://gitlab.com/tetration-network-policy-publisher/policy-stream-12-pub-vrf/blob/master/asa_create_acl_decrypt.yml). It illustrates how to apply policy from Tetration to a Cisco ASA firewall as an access-list. The tenant name from the policy is used as the access-list name in the ASA configuration

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
Joel W. King joel.king@wwt.com GitHub/GitLab: @joelwking Principal Architect at World Wide Technology
