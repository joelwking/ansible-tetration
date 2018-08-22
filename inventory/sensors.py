#!/usr/bin/env python
"""

    Copyright (c) 2018 World Wide Technology, Inc.
    All rights reserved.

    author: joel.king@wwt.com
    written:  22 August 2018
    description:
        Pulls a list of software sensors from the Tetration API and creates a dynamic inventory

    usage:
        $ ansible-playbook ping.yml -i ~/tetration/ansible-tetration/inventory/sensors.py
        $ ansible-inventory --list  -i ~/tetration/ansible-tetration/inventory/sensors.py
        $ ansible-inventory --vars NO_MGT_IP --graph  -i ./inventory/sensors.py
        $ ansible-inventory --host WPN-SRV3  -i ./inventory/sensors.py

    linter: flake8
"""
# System Imports
import sys
import os
import json
import ConfigParser
from dns import reversename
from dns import resolver
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

try:
    from tetpyclient import RestClient
except ImportError:
    print "\n\nImport error, TetPyClient must be installed.\n {}".format(__doc__)
    sys.exit()


class Session(object):
    """  Session class for Tetration API calls
    """
    OK = (200,)
    TRANSPORT = "https://"
    LOOPBACK = "127.0.0.1"
    NO_MGMT_IP = "NO_MGT_IP"

    def __init__(self, host="192.0.2.1", credentials="./credentials.json", transport=TRANSPORT):
        self.transport = transport
        self.api_endpoint = self.transport + host
        self.credential_file = credentials
        self.response = None
        self.inventory = {"_meta": {"hostvars": {}}}       # Empty inventory
        self.restclient = RestClient(self.api_endpoint, verify=False, credentials_file=self.credential_file)

    def test_connectivity(self, resource="/sensors"):
        """
        Used for debugging connectivity issues
        :param resource: The resource part of the URI
        :return: Status code or JSON object output if OK
        """
        self.response = self.restclient.get(resource)
        if self.response.status_code in Session.OK:
            return self.response.json()
        else:
            return 'Status code: {}'.format(self.response.status_code)

    def query_resource(self, resource="/sensors"):
        """
        Connect to the Tetration system, query the resource specified, and return the results
        :param resource: The resource part of the URI
        :return: The JSON response
        """
        self.response = self.restclient.get(resource)
        if self.response.status_code not in Session.OK:
            return {'Status code': self.response.status_code}

        return self.response.json()

    def resolve_hostname(self, ipaddr):
        """
        references: https://yamakira.github.io/python-network-programming/protocols/dns/index.html
        :param ipaddr: An IP address for resolution
        :return: FQDN 'csr1000v-1.sandbox.wwtatc.local.' or input IP address, if not resolved
        """
        domain_address = reversename.from_address(ipaddr)
        try:
            domain_name = str(resolver.query(domain_address, "PTR")[0])
        except dns.resolver.NXDOMAIN as e:                 # The DNS query name does not exist...
            domain_name = ipaddr
        return domain_name

    def add_host(self, group, host, **kwargs):
        """
        :param group: platform var from Tetration
        :param host: IPaddr or FQDN of the management interface
        :param kwargs: all key, value pairs from Tetration except interfaces
        :return: None
        """
        if self.inventory.get(group):                      # Does the group exist?
            pass
        else:
            self.inventory[group] = dict(hosts=[])         # Create new group

        if self.inventory[group].get(host):                # Does the host exist"
            return                                         # DUPLICATE HOST!
        else:
            self.inventory[group]['hosts'].append(host)    # add new host to group, create hostvars
            self.inventory['_meta']['hostvars'][host] = dict(**kwargs)
        return

    def get_management_ip(self, interfaces, family_type='IPV4', match="vrf", value="Default"):
        """
        :param interfaces: list of interfaces for this host
        :param family_type: Either IPV4 or IPV6
        :param match: key to test for a match
        :param value: value to test
        :return: IP address or None when no valid IP address exists
        """
        try:
            management_ip = interfaces[0].get('ip')        # if no match, return first interface
        except IndexError:
            return None
        for interface in interfaces:
            if interface.get('family_type') == family_type:
                if interface.get(match) == value:
                    management_ip = interface.get('ip')
        if management_ip == Session.LOOPBACK:
            return None
        return management_ip


def parse_config(filename=None, section='tetration'):
    """
    Parse the INI file for the Tetration cluster to query along with the credential file
    :param filename: name of the INI file
    :param section:  section in the INI file
    :return: dictionary of the FQDN/IP address of the cluster and the credential filename
    """
    if not filename:
        filename = __file__                                # python ./inventory/sensors.py retruns ./inventory/sensors.py
        filename = filename.replace('.py', '.ini')         # Look in the same directory as the code
        dirname = os.path.dirname(filename)                # Get the directory name

    ini = dict(credentials=dirname + '/credentials.json',  # Default values
               host='192.0.2.1',
               family_type='IPV4',
               match_key='vrf',
               match_value='Default')
    config = ConfigParser.ConfigParser()
    if config.read(filename):
        for key in ini.keys():
            try:
                value = config.get(section, key)
                ini[key] = value
            except ConfigParser.NoOptionError:
                pass                                       # No key specified
    return ini


def main():
    """
    Read the INI file, create a session with the Tetration cluster, retrieve a list of software sensors,
    for each host, return the managementIP and populate hostvars with metadata from Tetration for the sensor.
    :return:
    """
    ini = parse_config()
    tetration = Session(host=ini.get('host'), credentials=ini.get('credentials'))
    sensors = tetration.query_resource()
    for server in sensors.get('results'):
        management_ip = tetration.get_management_ip(server.get('interfaces'),
                                                    match=ini.get('match_key'),
                                                    value=ini.get('match_value'))
        if management_ip:
            tetration.add_host(server.get('platform'), management_ip, **server)
        else:
            tetration.add_host(Session.NO_MGMT_IP, server.get('host_name'), **server)

    print json.dumps(tetration.inventory)


if __name__ == '__main__':
    ####
    # import pydevd
    # pydevd.settrace('192.168.56.1', stdoutToServer=True, stderrToServer=True)
    ####
    main()
