#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (c) 2019 World Wide Technology
#     All rights reserved.
#     GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
#     author: joel.king@wwt.com
#     written:  13 August 2019
#     linter: flake8
#         [flake8]
#         max-line-length = 160
#         ignore = E402
#
ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': '@joelwking'
}
DOCUMENTATION = '''
---
module: tetration_application

short_description: Retrieve network policy from the Tetration API

version_added: "2.9"

description:
    -  Queries the Tetration API for applications and details, including absolute and default policies

options:

    application_name:
        description:
            - User specified name of the application. The appropriate application JSON object is returned
            - based on matching the specified name with the application names returned from the API.
        required: true

    version:
        description:
            - A version in the form of ‘v10’ or ‘p10’, defaults to ‘latest’.
        required: false
        default: 'latest'

    api_host:
        description:
          - The hostname or IP address of the Tetration cluster
        required: true

    api_verify:
        description:
          -  By default, if not specified, SSL certification verification is disabled
        required: false
        default: false

    api_secret:
        description:
          - API Secret key from the Tetration Cluster GUI
        required: false

    api_key:
        description:
          - API key from the Tetration Cluster GUI
        required: false

    api_cfile:
        description:
          - The name of a JSON file with the `api_key` and `api_secret` for authentication
          - Either these credentials must be specified above or the credential filename specified.
        required: true


author:
    - Joel W. King (@joelwking)
'''

EXAMPLES = '''

    - name: Tetration Application
      tetration_application:
        application: 'PolicyPubApp'
        version: latest
        api_host: 'tetration.example.net'
        api_cfile: '{{ playbook_dir }}/files/certificates/default/decrypted/api_credentials.json '
        api_verify: False
      register: api

'''
#
#  System Imports
#
pass
#
#  Application Imports
#
try:
    from tetpyclient import RestClient
    HAS_TETPYCLIENT = True
except ImportError:
    pass

#
#  Ansible Imports
#
try:
    from ansible_hacking import AnsibleModule              # Test
    PYCHARM = True
except ImportError:
    from ansible.module_utils.basic import AnsibleModule   # Production

#
# Constants
#
DEBUG = False
NOTFOUND = (404, 403)
OK = (200,)
POLICY_KEYWORDS = ('absolute_policies', 'default_policies')
HIGH = 0.99
ERROR = 0


class ProtocolMap(object):
    """
    Returns the keyword for the Assigned Internet Protocol Numbers given the protocol number as input.
    Refer to: https://en.wikipedia.org/wiki/List_of_IP_protocol_numbers
    """
    UNSPECIFIED = 'unspecified'
    PROTOCOLS = {
                 0: UNSPECIFIED,                           # Default value
                 1: 'icmp',
                 2: 'igmp',
                 6: 'tcp',
                 8: 'egp',
                 9: 'igp',
                 17: 'udp',
                 58: 'icmpv6',
                 88: 'eigrp',
                 89: 'ospfigp',
                 103: 'pim',
                 115: 'l2tp',
                 254: UNSPECIFIED}
    ETHER_TYPE = 'ip'

    def __init__(self):
        """ Build out all values from 0 to 254, creating a new dictionary with 'unspecified'
            as the default value
        """
        self.protocols = dict()
        for i in range(0, 255):
            if ProtocolMap.PROTOCOLS.get(i):
                self.protocols[i] = ProtocolMap.PROTOCOLS[i]
            else:
                self.protocols[i] = ProtocolMap.UNSPECIFIED
        return

    def get_keyword(self, protocol_number):
        """ Return the keyword for the protocol number. Return a string type of the
            input protocol_number if not valid or not found.
        """
        if not isinstance(protocol_number, int):
            try:
                protocol_number = ProtocolMap.UNSPECIFIED
            except (ValueError, TypeError):
                return ProtocolMap.UNSPECIFIED

        if protocol_number >= len(self.protocols) or protocol_number < 0:
            return str(protocol_number)

        return self.protocols.get(protocol_number)


def create_list_of_policies(adm_data):
    """
    Create list of policies from the application dependencey mapping output
    We are decoding a data structure which looks like the following

      "default_policies": [
    {
      "consumer_filter_id": "5c758c18497d4f160dbdb9ff",
      "provider_filter_id": "5c75732a755f022e205d807b",
      "consumer_filter_name": "dev*",
      "provider_filter_name": "Default:FOO:devdmz:EPG-DEV-DMZ1",
      "l4_params": [
        {
          "port": [
            3306,
            3306
          ],
          "proto": 6,
          "confidence": 0.96
        }
      ],
      "action": "ALLOW",
      "priority": 100
    },
    """
    pmap = ProtocolMap()
    filters = []
    #
    # The JSON file can have multiple keywords to specify user defined vs Tetration generated policy.
    #
    policies = []
    for keyword in POLICY_KEYWORDS:
        policies.extend(adm_data.get(keyword, []))

    #
    #  Decode the policies
    #
    for policy in policies:

        for l4 in policy.get('l4_params'):
            fields = dict(consumer_filter_name=policy.get('consumer_filter_name'),
                          provider_filter_name=policy.get('provider_filter_name'),
                          action=policy.get('action'),
                          priority=policy.get('priority'),
                          ether_type=ProtocolMap.ETHER_TYPE,
                          proto=pmap.get_keyword(l4.get('proto')),
                          confidence=l4.get('confidence', HIGH))

            if l4.get('port'):
                ports = {'from': l4.get('port')[0], 'to': l4.get('port')[1]}             # Note, this is a list, but I have never seen a length > 2
            else:
                ports = {'from': ProtocolMap.UNSPECIFIED, 'to': ProtocolMap.UNSPECIFIED}

            fields['ports'] = ports                                                      # Legacy format
                             
            fields['proto-ports'] = dict(protocol=pmap.get_keyword(l4.get('proto')))     # Edits and formatting for Pensando
            if ports['to'] == ports['from']:
                fields['proto-ports']['ports'] = '{}'.format(ports['from'])              # Range not required
            else:
                fields['proto-ports']['ports'] = '{}-{}'.format(ports['from'], ports['to'])

            if fields['proto-ports']['protocol'] == 'icmp':
                fields['proto-ports'].pop('ports')                                       # Can not specify ports for ICMP protocol

            filters.append(fields)

    return filters


def debug(msg):
    """
    The debug switch should only be enabled when executing outside Ansible.

    :param msg: a message to ouput for debugging
    :return: None
    """
    if DEBUG:
        print ": {}".format(msg)


def get_applications(restclient, params):
    """
     >>> rc.json()[0]
      {u'enforcement_enabled': True, u'description': u'Hunting Security Demo', u'author': u'Ben Dover', u'created_at': 1498856236,
      u'alternate_query_mode': False, u'primary': True, u'enforced_version': 12, u'latest_adm_version': 10,
      u'app_scope_id': u'5956bb09755f024a96136967', u'id': u'5956bb2c497d4f486384828b', u'name': u'Hunting'}

      return '0' for failures along with a message
      return ip and dictionary of the
    """
    available_applications = []
    rc = restclient.get('/applications/')

    if rc.status_code in OK:
        for application in rc.json():
            available_applications.append(application.get('name'))

            if application.get('name') == params.get('application'):
                return application.get('id'), application

        return ERROR, 'not found, available applications: ' + ','.join(available_applications)
    else:
        return ERROR, 'error getting applications, status_code: {}'.format(rc.status_code)


def get_application_details(restclient, application_id, version):
    """
    ### Get application ID details

        rc = restclient.get('/applications/5c9d827a497d4f0f7efd2cd9/details')
        rc = restclient.get('/applications/5c9d827a497d4f0f7efd2cd9/details?version=latest')
        rc = restclient.get('/applications/5c9d827a497d4f0f7efd2cd9/details?version=v34')

        >>> rc.json().viewkeys()
        dict_keys([u'inventory_filters', u'enforcement_enabled', u'absolute_policies', u'description', u'author',
        u'created_at', u'alternate_query_mode', u'primary', u'enforced_version', u'catch_all_action',
        u'latest_adm_version', u'default_policies', u'vrf', u'version', u'clusters', u'app_scope_id', u'id', u'name'])

    """
    rc = restclient.get('/applications/{}/details?version={}'.format(application_id, version))

    if rc.status_code in OK:
        return rc.status_code, rc.json()
    else:
        return ERROR, 'error getting application details, status_code: {}'.format(rc.status_code)


def main():
    """
    Main Logic
    """
    module = AnsibleModule(
        argument_spec=dict(
            application=dict(required=True, type='str'),
            version=dict(required=False, type='str', default='latest'),
            api_host=dict(required=True),
            api_key=dict(required=False),
            api_secret=dict(required=False),
            api_cfile=dict(required=False),
            api_verify=dict(default=True, required=False, type='bool')),
        supports_check_mode=False
    )

    try:
        HAS_TETPYCLIENT
    except NameError:
        module.fail_json(msg='Python API Client for Tetration Analytics required, install using pip install tetpyclient')

    #
    #  Credentials and identify the Tetration API host
    #
    api_host = 'https://{}'.format(module.params.get('api_host'), '192.0.2.1')
    api_verify = module.params.get('api_verify')

    if not api_verify:
        import requests
        requests.packages.urllib3.disable_warnings()

    if module.params.get('api_cfile'):
        restclient = RestClient(api_host, credentials_file=module.params.get('api_cfile'), verify=api_verify)
    else:
        restclient = RestClient(api_host, api_key=module.params.get('api_key'), api_secret=module.params.get('api_secret'), verify=api_verify)

    #
    # Map the user specified application name to an application ID to query
    #
    application_id, message = get_applications(restclient, module.params)

    if application_id == ERROR:
        module.fail_json(msg=message)

    #
    # Use the API to download what the GUI provides in Applications -> Export -> Clusters and Policies
    #
    status, adm_data = get_application_details(restclient, application_id, module.params.get('version'))

    if status == ERROR:
        module.fail_json(msg=adm_data)

    result = {'ansible_facts': {'adm': {}}}
    result['ansible_facts']['adm']['raw'] = adm_data
    result['ansible_facts']['adm']['policy'] = create_list_of_policies(adm_data)

    #
    # Return to the playbook
    #
    module.exit_json(changed=False, **result)


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
