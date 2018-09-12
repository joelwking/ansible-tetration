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
#  Protocol Buffer Imports  (User compliled, source is Tetration documentation)
#
sys.path.append('/home/administrator/tetration/ansible-tetration/library')
sys.path.append('/home/administrator/protobufs/protobuf-3.6.1/python')
import tetration_network_policy_pb2
#
# Constants
#
DEBUG = True
TETRATION_VERSION = '2.3.1.49'                             # Program tested with this version of Tetration
API_VERSION = (0,9)                                        # Required by KafkaConsumer, a guess based on the documentation
KAFKA_CONSUMER_CA = 'KafkaConsumerCA.cert'                 # This file contains the KafkaConsumer certificate
KAFKA_PRIVATE_KEY = 'KafkaConsumerPrivateKey.key'          # This file contains the Private Key for the Kafka Consumer


class PolicySet(object):
    """
    Container for all messages that comprise a Policy
    """
    def __init__(self):
        """
        """
        self.buffers = []                                # Create an empty list to hold all buffers
        self.ending_offset_value = None                  # The message offset for the UPDATE_END record


def set_arguments():
    """
    THIS IS Temporary, only used for development
    """
    return dict(certs='/home/administrator/tetration/ansible-tetration/files/certificates/producer-tnp-2.cert/',
                broker='10.253.239.14:9093', # kafkaBrokerIps.txt - IP address/portthat Kafka Client should use
                topic='Tnp-2')               # topic - file contains the topic this client can read the messages from.
                                             # Topics are of the format topic-<root_scope_id>
   
def debug(msg):
    """
    The debug switch should only be enabled when executing outside Ansible.
    """
    if DEBUG:
        print msg

def create_ssl_context(cert_dir):
    """
    Our Tetration cluster was created using a self-signed certificate.
    KafkaConsumer provides a means to provide our own SSL context, enabling
    CERT_NONE, no certificates from the server are required (or looked at if provided))

    https://<tetration>/documentation/ui/lab/managed_datatap.html

    :return: ssl context 
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.load_cert_chain("{}{}".format(cert_dir, KAFKA_CONSUMER_CA),
                        keyfile="{}{}".format(cert_dir, KAFKA_PRIVATE_KEY),
                        password=None)
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def create_consumer(args):
    """
    """
    consumer =  KafkaConsumer(args.get('topic'),             
                              api_version=API_VERSION,
                              bootstrap_servers=args.get('broker'), 
                              auto_offset_reset='earliest',           # consume earliest available messages,
                              enable_auto_commit=False,               # don't commit offsets
                              consumer_timeout_ms=1000,               # StopIteration if no message after 1 secone
                              security_protocol='SSL',                # must be capitalized
                              ssl_context= create_ssl_context(args.get('certs'))
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
            
        Notes:
            # if len(message.value) == 8:                  # End records are observed to have a length of 8 bytes
    """

    input_data = create_consumer(args)                     # Attach to the message bus, this is our INPUT data
    policy = PolicySet()                                   # Object to hold Network Policy for processing
    found_start = False                                    # skip all the messages until the next UPDATE_START message.

    protobuf = tetration_network_policy_pb2.KafkaUpdate()  # Create object for Tetration Network Policy
    tmp_pbuf = tetration_network_policy_pb2.KafkaUpdate()  # work area for decoding what type

    for count, message in enumerate(input_data):
        # Kafka messages are comprised of a topic, partition, offset, key and value
        # In testing, the key is always a value of 2
        # debug("count:%d message_offset:%d len(value):%s" % (count, message.offset, len(message.value)))


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
            # generates too much output debug("listfields {}".format(protobuf.ListFields()))
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
                    debug("{} protocol:{} ports:{} {}".format(intent.meta_data.intent_id, proto.protocol, ports.end_port, ports.start_port))
    return

def get_json(buffer):
    """
    :param buffer: 
    :return: 
    """
    json_string = json_format.MessageToJson(buffer)
    debug("JSON: {}".format(json_string))
    return

def main():
    """
    """
    args = set_arguments()                                 # Get arguments into the program
    network_policy = get_policy_update(args)               # Returned is discrete network policy, one unit of policy
    for policy in network_policy.buffers:
        # get_json(policy)
        decode_policy(policy)
    debug('TODO process ending offset value: {}'.format(network_policy.ending_offset_value))
    return

if __name__ == '__main__':
    
    ####
    import pydevd
    pydevd.settrace('192.168.56.1', stdoutToServer=True, stderrToServer=True)
    ####
    main()
