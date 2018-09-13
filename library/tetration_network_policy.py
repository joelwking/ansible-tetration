#!/usr/bin/env python
"""

    Copyright (c) 2018 World Wide Technology, Inc.
    All rights reserved.

    author: joel.king@wwt.com
    written:  22 August 2018
    description:
        
        Policies Publisher is an advanced Tetration feature allowing third party vendors to implement their own enforcement 
        algorithms optimized for network appliances such as load balancers or firewalls. 

    usage:
        TODO

    resources:
        Kafka
          https://github.com/confluentinc/confluent-kafka-python
          http://www.kafkatool.com/download.html
          https://www.confluent.io/confluent-cloud/
          https://gitlab.com/rtortori/tetration-alfred
          Global configuration properties
          https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
          
          https://stackoverflow.com/questions/42987129/kafka-10-python-client-with-authentication-and-authorization
          https://www.cloudkarafka.com/blog/2016-12-13-part2-3-apache-kafka-for-beginners_example-and-sample-code-python.html
          https://github.com/CloudKarafka/python-kafka-example
          
          https://kafka-python.readthedocs.io/en/1.1.1/apidoc/KafkaConsumer.html
          #    https://media.readthedocs.org/pdf/kafka-python/master/kafka-python.pdf
          
        Google Protocol Buffers
          https://developers.google.com/protocol-buffers/docs/pythontutorial
          https://developers.google.com/protocol-buffers/docs/reference/python/google.protobuf.message.Message-class
        
        Tetration
          https://10.253.239.4/documentation/ui/adm/policies.html?highlight=kafka#policies-publisher
          
          This link provides description of the files downloaded when you save the certificates.
              https://10.253.239.4/documentation/ui/lab/managed_datatap.html
          
        Others:
          https://github.com/remiphilippe/ansible-tetsensor
          https://github.com/mrlesmithjr/cisco-tetration-management
        
        SSL:
          https://github.com/edenhill/librdkafka/wiki/Using-SSL-with-librdkafka
          https://stackoverflow.com/questions/35766702/how-to-verify-ssl-is-working-for-kafka
          https://docs.python.org/2/library/ssl.html
          openssl s_client -debug -connect localhost:9093 -tls1
         
        debug:
          sudo tcpdump -A -X -nni enp0s3 host 10.253.239.14 -vv  

    linter: flake8
"""
#
#  System Imports
#
import ssl
import sys
#
#  Application Imports
#
from kafka import KafkaConsumer
#
#  Protocol Buffer Imports  (User compiled, source is Tetration documentation)
#
sys.path.append('/home/administrator/tetration/ansible-tetration/library')
sys.path.append('/home/administrator/protobufs/protobuf-3.6.1/python')
import tetration_network_policy_pb2
#
# Constant Imports
#
from tetration_network_policy_constants import *
from ip_protocols import ProtocolMap
#
# Ansible Imports
#
try:
    from ansible_hacking import AnsibleModule              # Test
except ImportError:
    from ansible.module_utils.basic import *               # Production


class PolicySet(object):
    """
    Container for all messages that comprise a Network Policy, it creates a list of Protocol Buffers
    """
    def __init__(self):
        """
        """
        self.buffers = []                                # Create an empty list to hold all buffers
        self.ending_offset_value = None                  # The message offset of the UPDATE_END record


def debug(msg, level=LOG_INFO):
    """
    The debug switch should only be enabled when executing outside Ansible.
    The constants are specified in the tetration_network_policy_constants.py file
    
    :param msg: a message to ouput for debugging 
    :param level: if provided, a means of enabling debug levels 0-7
    :return: None
    """
    if DEBUG and level <= DEBUG_LEVEL:
        print "{}: {}".format(level,msg)

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
    ctx.load_cert_chain("{}{}".format(args['cert_directory'], args['certificate_name']),
                        keyfile="{}{}".format(args['cert_directory'], args['private_key']),
                        password=None)
    ctx.verify_mode = ssl.CERT_NONE                        # TODO Enable verification
    return ctx

def create_consumer(args):
    """
    Refer to Python package kafka-python, a high-level message consumer of Kafka brokers.
    The consumer iterator returns consumer records, which expose basic message 
    attributes: topic, partition, offset, key, and value.

    :param args: Input arguments
    :return: KafkaConsumer object 
    """
    consumer =  KafkaConsumer(args.get('topic'),             
                              api_version=API_VERSION,
                              bootstrap_servers=args.get('broker'), 
                              auto_offset_reset='earliest',           # consume earliest available messages,
                              enable_auto_commit=False,               # don't commit offsets
                              consumer_timeout_ms=args.get('timeout'),# StopIteration if no message after 1 second
                              security_protocol='SSL',                # must be capitalized
                              ssl_context= create_ssl_context(args)
                             )

    debug("All the topics available :{}".format(consumer.topics()))
    debug("Subscription:{}".format(consumer.subscription()))
    debug("Partitions for topic:{}".format(consumer.partitions_for_topic(args.get('topic'))))
    debug("TopicPartitions:{}".format(consumer.assignment()))
    debug("Beginning offsets:{}".format(consumer.beginning_offsets(consumer.assignment())))
    debug("End offsets:{}\n".format(consumer.end_offsets(consumer.assignment())))

    return consumer

def get_policy_update(args):
    """
        Refer to the documentation at: https://<tetration>/documentation/ui/adm/policies.html
        this is an excerpt from the documentation
        
            // The network policy updates we send over Kafka can be large; over a couple of
            // GB each. Given that it is recommended to keep individual Kafka messages under
            // 10MB we split each policy update into several smaller Kafka messages. To
            // enable clients to correctly reconstruct the state and handle error scenarios
            // we wrap each Kafka message under KafkaUpdate proto. Every policy update will
            // have a begin marker UPDATE_START and end marker UPDATE_END.
            // To reiterate every Policy update will have following set of messages:
            //           - UPDATE_START indicates a new policy update begins.
            //           - Several UPDATE messages with increasing sequence numbers.
            //           - UPDATE_END indicates the new policy update is complete.
            // Note that the first message's (UPDATE_START) sequence number is zero and
            // subsequent message's sequence numbers are strictly incremented by one.
            // A client reading these updates should read all the messages from UPDATE_START
            // to UPDATE_END. If any message is missing then client should skip all the
            // messages until the next UPDATE_START message.
            

        Kafka messages are comprised of a topic, partition, offset, key and value.        
            
        The key (message.key), for all records, have a value of 2. The message value 
        (message.value) is a string which we load into the protocol buffer for decoding.
        We need to determine the field 'type' in the protocol buffer, to determine if it is an
        UPDATE, UPDATE_START, or UPDATE_END. End records (UPDATE_END) have a length of 8 bytes,
          e.g.  if len(message.value) == 8:
        and contain no data. Start (UPDATE_START) message contain data. Have not observed 
        UPDATE records in testing, raise a ValueError exception to flag for future development.
        
    """
    input_data = create_consumer(args)                     # Attach to the message bus, this is our INPUT data
    policy = PolicySet()                                   # Object to hold Network Policy for processing
    found_start = False                                    # skip all the messages until the next UPDATE_START message.

    protobuf = tetration_network_policy_pb2.KafkaUpdate()  # Create object for Tetration Network Policy
    tmp_pbuf = tetration_network_policy_pb2.KafkaUpdate()  # Work area for decoding the protocol buffer type.

    for count, message in enumerate(input_data):
        debug("count:%d message_offset:%d len(value):%s" % (count, message.offset, len(message.value)), level=LOG_DEBUG)
        tmp_pbuf.ParseFromString(message.value)            # Load the message value into the protocol buffer

        if tmp_pbuf.type > 2:
            # Any types other than 0,1,2 are unexpected
            raise ValueError("Unknown type:{} at message offset:{}".format(protobuf.type, message.offset))

        if tmp_pbuf.type == protobuf.UPDATE and found_start:
            protobuf.MergeFromString(message.value)
            raise ValueError("Encountered UPDATE record at message offset:{}, logic not tested".format(message.offset))
            # continue   TODO Once tested, you should remove the exception and continue

        if tmp_pbuf.type == protobuf.UPDATE_END and found_start:
            policy.ending_offset_value = message.offset
            debug("Found UPDATE_END at message offset:{}".format(message.offset))
            break

        if tmp_pbuf.type == protobuf.UPDATE_START:
            found_start = True
            protobuf.ParseFromString(message.value)        # Load the message value into the protocol buffer
            debug("Found UPDATE_START at message offset:{}".format(message.offset))

        if found_start:
            policy.buffers.append(protobuf)
            debug("listfields {}".format(protobuf.ListFields()), level=LOG_DEBUG)
            continue
        else:
            debug("Skipping message offset:{}".format(message.offset))
            continue

    return policy

def decode_policy(policy):
    """
    :param policy: 
    :return: 
    """
    # debug("Tenant Network Policy {}".format(policy.tenant_network_policy))

    for item in policy.tenant_network_policy.network_policy:
        debug("Catch_all: %s" % item.catch_all.action)
        for intent in item.intents:
            # debug("Intent_id: %s" % intent.meta_data.intent_id)
            for proto in intent.flow_filter.protocol_and_ports:
                # debug("protocol:%s " % (proto.protocol))
                for ports in proto.port_ranges:
                    debug("{} protocol:{} ports:{} {}".format(intent.meta_data.intent_id, ProtocolMap().get_keyword(proto.protocol), ports.end_port, ports.start_port))
    return

def get_json(buffer):
    """
    TODO NOT IMPLEMENTED
    :param buffer: 
    :return: 
    """
    json_string = json_format.MessageToJson(buffer)
    debug("JSON: {}".format(json_string))
    return

def main():
    """ 
                                             # kafkaBrokerIps.txt - IP address/portthat Kafka Client should use
                                             # topic - file contains the topic this client can read the messages from.
                                             # Topics are of the format topic-<root_scope_id>
    """
    module = AnsibleModule(
        argument_spec=dict(
            broker=dict(required=True),
            topic=dict(required=True),
            timeout=dict(default=1000, type='int', required=False),
            private_key=dict(default=KAFKA_PRIVATE_KEY, required=False),
            certificate_name=dict(default=KAFKA_CONSUMER_CA, required=False),
            cert_directory=dict(required=True),
            validate_certs=dict(default=True, required=False, type='bool')
        ),
        supports_check_mode=False
    )

    if module.params.get('validate_certs') != 'no':
        module.fail_json(msg='TODO: Validate certs not implemented')
    debug('{}'.format(module.params))

    network_policy = get_policy_update(module.params)        # Returned is discrete network policy, one unit of policy
    if len(network_policy.buffers) > 1:
        raise ValueError('TODO: Never encountered UPDATE records, need to test Merging')
    try:
        decode_policy(network_policy.buffers[0])
    except IndexError:
        module.fail_json(msg='No messages returned, consider increasing the default timeout of 1000 ms.')

    debug('TODO process ending offset value: {}'.format(network_policy.ending_offset_value))
    return

if __name__ == '__main__':
    
    ####
    import pydevd
    pydevd.settrace(PYDEVD_HOST, stdoutToServer=True, stderrToServer=True)
    ####
    main()
