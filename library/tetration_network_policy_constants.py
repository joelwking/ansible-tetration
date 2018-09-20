"""
    Copyright (c) 2018 World Wide Technology, Inc.
    All rights reserved.

    author: joel.king@wwt.com
    written:  13 September 2018
"""
#
#  Logging Level Constants
#
LOG_DEBUG = 7
LOG_INFO = 6
LOG_NOTICE = 5
LOG_WARNING = 4
LOG_ERR = 3
LOG_CRIT = 2
LOG_ALERT = 1
LOG_EMERG = 0
DEBUG = False
DEBUG_LEVEL = LOG_INFO
#
# Constants
#
TETRATION_VERSION = 'Version 2.3.1.41-PATCH-2.3.1.49'      # Program tested with this version of Tetration
API_VERSION = (0,9)                                        # Required by KafkaConsumer, a guess based on the documentation
KAFKA_CONSUMER_CA = 'KafkaConsumerCA.cert'                 # This file contains the KafkaConsumer certificate
KAFKA_PRIVATE_KEY = 'KafkaConsumerPrivateKey.key'          # This file contains the Private Key for the Kafka Consumer