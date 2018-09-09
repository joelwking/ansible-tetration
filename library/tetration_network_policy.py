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
#  
#
from kafka import KafkaConsumer
import ssl
#
#  Protocol Buffers
#

# export PYTHONPATH="/usr/share/ansible:$HOME/protobufs/protobuf-3.6.1/python"
import tetration_network_policy_pb2
#
#
#
TETRATION_VERSION = '2.3.1.49'
API_VERSION = (0,9)
KAFKA_CONSUMER_CA = 'KafkaConsumerCA.cert'        # This file contain the KafkaConsumer certificate.
KAFKA_PRIVATE_KEY = 'KafkaConsumerPrivateKey.key' # This file contains the Private Key for the Kafka Consumer.

def set_arguments():
    """
    THIS IS Temporary, only used for development
    """
    return dict(certs='/ansible-tetration/files/certificates/producer-tnp-2.cert/',
                broker='10.253.239.14:9093', # kafkaBrokerIps.txt - IP address/portthat Kafka Client should use
                topic='Tnp-2')               # topic - file contains the topic this client can read the messages from.
                                             # Topics are of the format topic-<root_scope_id>
   
def debug(consumer, args):
    """
    """
    topic = args.get('topic')
    print "All the topics available {}".format(consumer.topics())
    print "Subscription {}".format(consumer.subscription())
    print "Partitions for topic {}".format(consumer.partitions_for_topic(topic))
    print "TopicPartitions {}".format(consumer.assignment())
    print "Beginning offsets {}".format(consumer.beginning_offsets(consumer.assignment()))
    print "End offsets {}".format(consumer.end_offsets(consumer.assignment()))


def create_ssl_context(cert_dir):
    """
    Our Tetration cluster was created using a self-signed certificate.
    KafkaConsumer provides a means to provide our own SSL context, enabling
    CERT_NONE, no certificates from the server are required (or looked at if provided))

    https://<tetration>/documentation/ui/lab/managed_datatap.html?highlight=kafkaconsumerca

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
    return KafkaConsumer(args.get('topic'),             
                              api_version=API_VERSION,
                              bootstrap_servers=args.get('broker'), 
                              auto_offset_reset='earliest',           # consume earliest available messages,
                              enable_auto_commit=False,               # don't commit offsets
                              consumer_timeout_ms=1000,               # StopIteration if no message after 1 secone
                              security_protocol='SSL',
                              ssl_context= create_ssl_context(args.get('certs'))
                            )           

def main():
    """
    """
    args = set_arguments()
    consumer = create_consumer(args)
    debug(consumer, args)

    for message in consumer:
        print "%s:%d:%d key=%s len of value=%s" % (message.topic, message.partition, message.offset, message.key, len(message.value))
        break

if __name__ == '__main__':
    main()