#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (c) 2019 World Wide Technology, Inc.
#     All rights reserved.
#
#     author: joel.king@wwt.com (@joelwking)
#     written:  28 June 2019
#
#     description:  Kafka debugger using methods and classes from tetration_network_policy.py
#
#     refer to: https://developer.cisco.com/codeexchange/github/repo/joelwking/ansible-tetration
#
#               To tail the log file in Tetration 'Explore'
#               POST happobat-1  tail?args=-200 /local/logs/tetration/adhocsched/current
#
#     usage:
#             $ export PYTHONPATH="/usr/share/ansible:/usr/share/"
#             $ python2.7 kafka_debugger.py  <input_json_file>
#
#
from kafka import KafkaConsumer
from tetration_network_policy import create_consumer, create_ssl_context, debug, PolicySet

import ssl
import time
import json
import sys

DEBUG = True
CLIENT_ID = 'NETWORK_POLICY'
AUTOCOMMIT = True
SSL = 'SSL'
API_VERSION = (0, 9)


def main(params, iterations=10):
    """
        Verify connectivity to the Kafka broker and output the message offset and the length of the message (value)
    """
    print(json.dumps(params, indent=4, sort_keys=True))

    policy = PolicySet()
    input_data = create_consumer(params, policy)

    print(json.dumps(policy.result, indent=4, sort_keys=True))

    print("\n{} ...waiting for Kafka messages".format(time.asctime()))
    for count, message in enumerate(input_data):
        print("%s count:%d message_offset:%d len(value):%s" % (time.asctime(), count, message.offset, len(message.value)))
        if count > iterations:
            return
    print("\n{} ...no messages returned within timeout of {} ms".format(time.asctime(), params.get('timeout')))
    return


if __name__ == "__main__":
    """
         Create a JSON file with the key, values shown below and specify the file name as arg 1
         You must code a trailing slash on the directory.
    """
    params = {
              "cert_directory": "/tmp/policy-stream-12-pub-vrf/files/certificates/policy-stream-12-pub-vrf.cert/",
              "validate_certs": "no",
              "topic": "Policy-Stream-12",
              "broker": "10.253.239.14:443",
              "certificate_name": "KafkaConsumerCA.cert",
              "private_key": "KafkaConsumerPrivateKey.key",
              "timeout": 62000,
              "start_at": "latest",
              "start_at_offset": 0
            }

    # Optionally read the above from an input file specified as arg 1
    if len(sys.argv) > 1:
        try:
            jsonfile = open(sys.argv[1], 'r')
            params = json.loads(jsonfile.read())
            jsonfile.close()
        except IOError:
            print "input file: %s not found!" % sys.argv[1]
            sys.exit(1)

    params['validate_certs'] = False

    main(params)