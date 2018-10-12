#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (c) 2018 World Wide Technology, Inc.
#     All rights reserved.
#
#     author: joel.king@wwt.com
#     written:  22 August 2018
#     linter: flake8
#
ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': '@joelwking'
}
DOCUMENTATION = '''
---
module: tetration_network_policy

short_description: Retrieve network policy from the Tetration Kafka message bus and return as facts to the playbook

version_added: "2.8"

description:
    -  Policies Publisher is an advanced Tetration feature allowing third party vendors to implement their own enforcement
    -  algorithms optimized for network appliances such as load balancers or firewalls.

options:
    broker:
        description:
            - IP address/port of the broker that Kafka Client should use, see file 'kafkaBrokerIps.txt'
            -  The values for broker and topic are obtained by downloading the certificate for the configured Data Tap,
            -  refer to https://<tetration>/#/maintenance/lab_admin/datataps
        required: true

    topic:
        description:
            - "The file 'topic' contains the topic this client can read the messages from. Topics are of the format:"
            - "topic-<root_scope_id> e.g. Tnp-1"
        required: true

    timeout:
        description:
            - KafkaConsumer, consumer_timeout_ms, StopIteration if no message after 'n' ms.
        default: 2000
        required: false

    cert_directory:
        description:
            -  Location where the client certificate was downloaded and uncompressed / untar'ed.
        required: true

    validate_certs:
        description:
            - If your Tetration cluster was configured to use self-signed certificates, you must use a value of False
        default: True
        required: false

    certificate_name:
        description:
            - Obtained by downloading the certificate for the configured Data Tap
        default: KafkaConsumerCA.cert
        required: false

    private_key:
        description:
            - Obtained by downloading the certificate for the configured Data Tap
        default: KafkaConsumerPrivateKey.key
        required: false

author:
    - Joel W. King (@joelwking)
'''

EXAMPLES = '''

- name: Tetration Network Policy
  tetration_network_policy:
      broker: "192.0.2.1:9093"
      topic: "Tnp-2"
      cert_directory: "{{ playbook_dir }}/files/certificates/producer-tnp-2.cert/"
      validate_certs: "no"
      certificate_name: "KafkaConsumerCA.cert"
      private_key: "KafkaConsumerPrivateKey.key"

- name: Tetration Network Policy
  tetration_network_policy:
      broker: "{{ lookup('file', '{{ playbook_dir }}/files/certificates/{{ cert_directory }}/kafkaBrokerIps.txt') }}"
      topic: "{{ lookup('file', '{{ playbook_dir }}/files/certificates/{{ cert_directory }}/topic.txt') }}"
      cert_directory: "{{ playbook_dir }}/files/certificates/{{ cert_directory }}/"
      validate_certs: "{{ validate_certs }}"
  register: tnp

'''
#
#  System Imports
#
import ssl
import sys
import ipaddress
#
#  Application Imports
#
from kafka import KafkaConsumer
#
#  Ansible Imports
#
try:
    from ansible_hacking import AnsibleModule              # Test
    PYCHARM = True
except ImportError:
    from ansible.module_utils.basic import AnsibleModule   # Production
#
#  Protocol Buffer Imports  (User compiled, source is Tetration documentation)
#
# TODO eliminate these path appends
sys.path.append('/home/administrator/tetration/ansible-tetration/library')
sys.path.append('/home/administrator/protobufs/protobuf-3.6.1/python')
import tetration_network_policy_pb2 as tnp_pb2
#
# Constants
#
DEBUG = False
TETRATION_VERSION = 'Version 2.3.1.41-PATCH-2.3.1.49'      # Program tested with this version of Tetration
API_VERSION = (0, 9)                                       # Required by KafkaConsumer, refer to SDK docs
CLIENT_ID = 'NETWORK_POLICY'                               # Identifies this client, server side logging
SSL = 'SSL'                                                # must be capitalized
KAFKA_CONSUMER_CA = 'KafkaConsumerCA.cert'                 # This file contains the KafkaConsumer certificate
KAFKA_PRIVATE_KEY = 'KafkaConsumerPrivateKey.key'          # This file contains the Private Key for the Kafka Consumer
AUTOCOMMIT = True


class PolicySet(object):
    """
    Container for all messages that comprise a Network Policy, stores the Protocol Buffer
    """
    def __init__(self):
        """
        """
        self.result = dict(ansible_facts={})               # Empty dictionary to output JSON to Ansible
        self.buffer = None                                 # Network Policy buffer
        self.update_end_offset = None                      # The message offset of the UPDATE_END record

    def add_fact(self, key, value):
        """
        Add a key and value to the results (ansible_facts) returned to the playbook from this module

        :param key: Add this key to ansible_facts
        :param value: Value for the specified key
        :return:
        """
        self.result["ansible_facts"][key] = value


def debug(msg):
    """
    The debug switch should only be enabled when executing outside Ansible.

    :param msg: a message to ouput for debugging
    :return: None
    """
    if DEBUG:
        print ": {}".format(msg)


def format_ip(ip_address):
    """
    Convert IP address from integer to string,
    The value has been observed to be a null string which will throw exception
    ipaddress.AddressValueError '' does not appear to be an IPv4 or IPv6 address.
    Did you pass in a bytes (str in Python 2) instead of a unicode object?

    :param ip_address: integer
    :return: ip_address: dotted decimal IPv4 or IPv6 address
    """
    try:
        ip_address = ipaddress.ip_address(ip_address).__str__()
    except ipaddress.AddressValueError:
        pass                                               # Invalid IPv4 or IPv6 address.
    return ip_address


def create_ssl_context(args):
    """
    Our Tetration cluster was created using a self-signed certificate.
    KafkaConsumer provides a means to provide our own SSL context, enabling
    CERT_NONE, no certificates from the server are required (or looked at if provided))

    Refer to : https://<tetration>/documentation/ui/lab/managed_datatap.html

    :param cert_dir: directory where the certificate files are stored
    :return: ssl context
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.load_cert_chain(
        "{}{}".format(args['cert_directory'], args['certificate_name']),
        keyfile="{}{}".format(args['cert_directory'], args['private_key']),
        password=None
    )
    ctx.verify_mode = ssl.CERT_NONE                        # TODO Enable verification
    return ctx


def create_consumer(args, policy):
    """
    Refer to Python package kafka-python, a high-level message consumer of Kafka brokers.
    The consumer iterator returns consumer records, which expose basic message
    attributes: topic, partition, offset, key, and value.

    :param args: Input arguments
    :param policy: Object to store Network Policy for processing
    :return: KafkaConsumer object, messages from the message bus for processing
    """
    consumer = KafkaConsumer(args.get('topic'),
                             api_version=API_VERSION,
                             bootstrap_servers=args.get('broker'),
                             client_id=CLIENT_ID,                       # name passed to servers for identification
                             auto_offset_reset='earliest',              # consume earliest available messages,
                             enable_auto_commit=AUTOCOMMIT,             # autocommit offsets?
                             consumer_timeout_ms=args.get('timeout'),   # StopIteration if no message after 'n' seconds
                             security_protocol=SSL,
                             ssl_context=create_ssl_context(args)
                             )

    # Returned values are of type Set
    msg = ["All the topics available :{}".format(consumer.topics()),
           "Subscription:{}".format(consumer.subscription()),
           "Partitions for topic:{}".format(consumer.partitions_for_topic(args.get('topic'))),
           "TopicPartitions:{}".format(consumer.assignment())
           ]
    policy.add_fact('consumer_debug', msg)
    # Offsets are type Int
    policy.add_fact('beginning_offsets', str(consumer.beginning_offsets(consumer.assignment())))
    policy.add_fact('end_offsets', str(consumer.end_offsets(consumer.assignment())))

    return consumer


def get_policy_update(policy, input_data):
    """
        Refer to the documentation at: https://<tetration>/documentation/ui/adm/policies.html
        for information on how network policy messages are published.

        Kafka messages are comprised of a topic, partition, offset, key and value.

        The key (message.key), for all records, have a value of 2. The message value
        (message.value) is a string which we load into the protocol buffer for decoding.
        We need to determine the field 'type' in the protocol buffer, to determine if it is an
        UPDATE, UPDATE_START, or UPDATE_END. End records (UPDATE_END) have a length of 8 bytes,
          e.g.  if len(message.value) == 8:
        and contain no data. Start (UPDATE_START) message contain data. Have not observed
        UPDATE records in testing, raise a ValueError exception to flag for future development.

        :param policy: Object to store Network Policy for processing
        :param input_data: messages from the Kafka Broder
        :return:
    """
    found_start = False                                    # skip all the messages until the next UPDATE_START message.

    protobuf = tnp_pb2.KafkaUpdate()                       # Create object for Tetration Network Policy
    tmp_pbuf = tnp_pb2.KafkaUpdate()                       # Work area for decoding the protocol buffer type.

    for count, message in enumerate(input_data):
        debug("count:%d message_offset:%d len(value):%s" % (count, message.offset, len(message.value)))
        tmp_pbuf.ParseFromString(message.value)            # Load the message value into the protocol buffer

        if tmp_pbuf.type > 2:
            # Any types other than 0,1,2 are unexpected
            raise ValueError("Unknown type:{} at message offset:{}".format(protobuf.type, message.offset))

        if tmp_pbuf.type == protobuf.UPDATE and found_start:
            protobuf.MergeFromString(message.value)
            policy.buffer = protobuf                       # Replace what was saved when we found_start
            raise ValueError("Encountered UPDATE record at message offset:{}, logic not tested".format(message.offset))
            # continue   TODO Once tested, you should remove the exception and continue

        if tmp_pbuf.type == protobuf.UPDATE_END and found_start:
            policy.update_end_offset = message.offset
            debug("Found UPDATE_END at message offset:{}".format(message.offset))
            break

        if tmp_pbuf.type == protobuf.UPDATE_START:
            found_start = True
            protobuf.ParseFromString(message.value)        # Load the message value into the protocol buffer
            debug("Found UPDATE_START at message offset:{}".format(message.offset))

        if found_start:
            policy.buffer = protobuf
            # debug("listfields {}".format(protobuf.ListFields()))
            continue
        else:
            debug("Skipping message offset:{}".format(message.offset))
            continue

    return


def decode_catch_all(policy):
    """
    Decode the Catch All policy

    :param policy: Object to store Network Policy for processing
    :return:
    """
    tnp = policy.buffer.tenant_network_policy
    policy.add_fact('tenant_name', tnp.tenant_name)

    for item in tnp.network_policy:
        policy.add_fact('catch_all', tnp_pb2.CatchAllPolicy.Action.Name(item.catch_all.action))

    return


def decode_filters(policy):
    """
    Decode the Inventory Filters

    ipaddress.ip_address("4\330\201\003").__str__() convertx binary IPv4/IPv6 addresses
    to dotted decimal string, u'52.216.129.3' or u'2001:0:9d38:90d7:3cc4:271:f502:146a'

    :param policy: Object to store Network Policy for processing
    :return:
    """
    tnp = policy.buffer.tenant_network_policy
    inventory_filters = []

    for item in tnp.network_policy:
        for inventory_filter in item.inventory_filters:
            invy_items = []
            for invy_item in inventory_filter.inventory_items:
                invy_items.append(dict(start_ip_addr=format_ip(invy_item.address_range.start_ip_addr),
                                       end_ip_addr=format_ip(invy_item.address_range.end_ip_addr),
                                       addr_family=tnp_pb2.IPAddressFamily.Name(invy_item.address_range.addr_family)))

            inventory_filters.append(dict(id=inventory_filter.id,
                                          query=inventory_filter.query,
                                          inventory_items=invy_items))

    policy.add_fact('inventory_filters', inventory_filters)
    return


def decode_intents(policy):
    """
    Decode the Intents, creating ACL lines to apply to a 'firewall'

    :param policy: Object to store Network Policy for processing
    :return:
    """
    tnp = policy.buffer.tenant_network_policy
    acl = []                                               # Empty list to hold ACL lines

    for item in tnp.network_policy:
        for intent in item.intents:
            for proto in intent.flow_filter.protocol_and_ports:
                for ports in proto.port_ranges:
                    acl_line = dict(
                        action=tnp_pb2.Intent.Action.Name(intent.action),             # ALLOW or DROP
                        intent_id=intent.id,
                        consumer_filter_id=intent.flow_filter.consumer_filter_id,
                        provider_filter_id=intent.flow_filter.provider_filter_id,
                        ip_protocol=tnp_pb2.IPProtocol.Name(proto.protocol).lower(),  # tcp must be lower case for ACI
                        dst_port_start=ports.start_port,                              # 135
                        dst_port_end=ports.end_port                                   # 135
                    )

                    acl.append(acl_line)

    policy.add_fact('acl', acl)
    return


def main():
    """
    Main Logic
    First do some basic checking of input parameters, create an object to hold the Network Policy for
    processing. Iterate over the Kafka messages and locate the starting message for a network policy, and
    return when the ending message is located.

    Network Policy is broken into three parts:
        Catch All Policy
        Intents
        Inventory Filters

    We decode the three sections of the policy and store the fields of interest as ansible_facts.
    """
    module = AnsibleModule(
        argument_spec=dict(
            broker=dict(required=True),
            topic=dict(required=True),
            timeout=dict(default=2000, type='int', required=False),
            private_key=dict(default=KAFKA_PRIVATE_KEY, required=False),
            certificate_name=dict(default=KAFKA_CONSUMER_CA, required=False),
            cert_directory=dict(required=True),
            validate_certs=dict(default=True, required=False, type='bool')
        ),
        supports_check_mode=False
    )

    if module.params.get('validate_certs'):
        module.fail_json(msg='TODO: Validate certs not implemented')

    if not module.params.get('cert_directory').endswith('/'):
        module.params['cert_directory'] = '{}/'.format(module.params['cert_directory'])

    # Connect to the Kafka broker and retrieve a network policy
    policy = PolicySet()                                   # Object to hold Network Policy for processing
    input_data = create_consumer(module.params, policy)    # Attach to the message bus, this is our INPUT data
    get_policy_update(policy, input_data)                  # Iterate over messages and locate a network policy

    if policy.buffer:                                      # Got a policy, decode it
        decode_intents(policy)                             # Intents
        decode_catch_all(policy)                           # Catch_all and Tenant Name
        decode_filters(policy)                             # Inventory Filters
    else:
        module.fail_json(msg='No messages returned from Kafka broker!')

    input_data.close(autocommit=AUTOCOMMIT)                # TODO verify autoommit
    policy.add_fact('update_end_offset', policy.update_end_offset)

    module.exit_json(changed=False, **policy.result)


if __name__ == '__main__':
    """ Logic for remote debugging with Pycharm Pro, use SSH_CLIENT to derive the IP address of the laptop
    """
    try:
        PYCHARM
    except NameError:
        pass
    else:
        import pydevd
        import os
        pydevd.settrace(os.getenv("SSH_CLIENT").split(" ")[0], stdoutToServer=True, stderrToServer=True)

    main()
