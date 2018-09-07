#!/usr/bin/env python
"""

    Copyright (c) 2018 World Wide Technology, Inc.
    All rights reserved.

    author: joel.king@wwt.com
    written:  22 August 2018
    description:
        TODO

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
          
        Google Protocol Buffers
          https://developers.google.com/protocol-buffers/docs/pythontutorial
        
        Tetration
          https://10.253.239.4/documentation/ui/adm/policies.html?highlight=kafka#policies-publisher
          
        Others:
          https://github.com/remiphilippe/ansible-tetsensor
          https://github.com/mrlesmithjr/cisco-tetration-management
        
        SSL:
          https://github.com/edenhill/librdkafka/wiki/Using-SSL-with-librdkafka
          https://stackoverflow.com/questions/35766702/how-to-verify-ssl-is-working-for-kafka
          openssl s_client -debug -connect localhost:9093 -tls1
          
    linter: flake8
"""
# System Imports
#
# I completed the Tetration setup such that the topic for policy is published.  The app is Entseg:CMBT.
# KafkaTool typically contacts the Kafka server on the Zookeeper port of 2181.
#
# https://github.com/confluentinc/confluent-kafka-python
#
#  When you download the certificate, file kafkaBrokerIps.txt contains the IP address and port number. You
#  could read this file and include the value into the program using a 'lookup' plug in
#  File topic.txt contains the name of the topic, e.g. Tnp-1
#
#
#   Confluent KAFKA SDK https://github.com/confluentinc/confluent-kafka-python
#
from confluent_kafka import Consumer, KafkaError
import ssl
#
#   https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
#
directory = "/ansible-tetration/files/certificates/producer-tnp-1.cert/"

c = Consumer({
    'bootstrap.servers': '10.253.239.14:9093',
    'group.id': '1',                                       # Tnp-1
    'default.topic.config': {'auto.offset.reset': 'smallest'},
    'security.protocol': 'ssl',
    'ssl.ca.location': directory + 'KafkaCA.cert',
    'ssl.certificate.location' : directory + 'KafkaConsumerCA.cert',
    'ssl.key.location': directory + 'KafkaConsumerPrivateKey.key',
    'fetch.message.max.bytes': '10485760',
    'debug': 'security',
    "auto.offset.reset": "latest"

})
#  KafkaException: KafkaError{code=_INVALID_ARG,val=-186,str="Java TrustStores are not supported, use `ssl.ca.location` and a certificate file instead. See https://github.com/edenhill/librdkafka/wiki/Using-SSL-with-librdkafka for more information."}

c.subscribe(['Tnp-1'])

#
#
#     sudo tcpdump -A -X -nni enp0s3 host 10.253.239.14 -vv
#    Documentation
#    https://media.readthedocs.org/pdf/kafka-python/master/kafka-python.pdf
#
from kafka import KafkaConsumer
import ssl

directory = "/ansible-tetration/files/certificates/producer-tnp-2.cert/"
def no_verify_ssl():
    """
    https://docs.python.org/2/library/ssl.html
    This link provides description of the files downloaded when you save the certificates.
    https://10.253.239.4/documentation/ui/lab/managed_datatap.html
    
    :return: 
    """
    ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    ctx.verify_mode = ssl.CERT_NONE           # no certificates from the server are required (or looked at if provided)
    ctx.load_cert_chain(directory + 'KafkaConsumerCA.cert',
                        keyfile=directory + 'KafkaConsumerPrivateKey.key',
                        password=None)
    return ctx

consumer = KafkaConsumer('Tnp-2',          # topic - file contains the topic this client can read the messages from.
                          # group_id='1',    Topics are of the format topic-<root_scope_id>
                          api_version=(0,9),
                          bootstrap_servers='10.253.239.14:9093', # kafkaBrokerIps.txt - IP address/portthat Kafka Client should use
                          auto_offset_reset='earliest',           # consume earliest available messages,
                          enable_auto_commit=False,               # don't commit offsets
                          consumer_timeout_ms=1000,               # StopIteration if no message after 1sec
                          security_protocol='SSL',
                          ssl_context= no_verify_ssl()
                         )

print "All the topics available {}".format(consumer.topics())
print "Subscription {}".format(consumer.subscription())
print "Partitions for topic {}".format(consumer.partitions_for_topic('Tnp-2'))
print "TopicPartitions {}".format(consumer.assignment())
print "Beginning offsets {}".format(consumer.beginning_offsets(consumer.assignment()))
print "End offsets {}".format(consumer.end_offsets(consumer.assignment()))
#
print "seek to beginning {}".format(consumer.seek_to_beginning(consumer.partitions_for_topic('Tnp-2')))

# print ("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition, message.offset, message.key, message.value))
for message in consumer:
    print "%s:%d:%d:" % (message.topic, message.partition, message.offset)

# export PYTHONPATH="/usr/share/ansible:$HOME/protobufs/protobuf-3.6.1/python"
import tetration_network_policy_pb2
