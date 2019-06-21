#!/usr/bin/env python
#
#     GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
#     Copyright (c) 2019 World Wide Technology, Inc.
#     All rights reserved.
#
#     author: joel.king@wwt.com
#     written:  20 June  2019
#     linter: flake8
#         [flake8]
#         max-line-length = 160
#         ignore = E402
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.0',
    'status': ['preview'],
    'supported_by': '@joelwking'
}

DOCUMENTATION = """

"""

EXAMPLES = """
  tasks:
    - set_fact:
        scope_id_literals: "{{ query('tetration_scope', '5c9a9926497d4f7f0b9dbc07', api_host='10.253.239.4', api_key='5f79a256e', api_secret='951bdbb') }}"

    - set_fact:
        scope_id_vars: "{{ query('tetration_scope', app_scope_id, api_host=tet.host, api_key=tet.api.key, api_secret=tet.api.secret) }}"

    - set_fact:
        scope_id_all: "{{ query('tetration_scope', 'all', api_host=tet.host, api_cfile=cfile)  }}"

"""

RETURN = """

"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

from tetpyclient import RestClient

display = Display()                                        # Use the Display class for logging


class LookupModule(LookupBase):
#class LookupModule(object):
    """
        Ansible Plugin:Lookup  Return Application Scopes from Tetration API
    """

    DEFAULT = dict(short_name='CLUSTER', name='CLUSTER', description='Scope Id: Not Found')
    NOTFOUND = (404, 403)
    ALL = 'ALL'

    def run(self, ids,  **kwargs):
        """
            Execute the 'tetration_scope' plugin
            Ansible sends the non-keyword value as a list. 

            The keyword arguments identify the Tetration host, credentials and SSL options
        """

        api_host = 'https://{}'.format(kwargs.get('api_host', '192.0.2.1')) # Hostname or IP of Tetration Cluster
        api_verify = kwargs.get('api_verify', False)                        # SSL certification verification 
                                                                            # Either specify
        api_secret = kwargs.get('api_secret', '')                           #   API Secret 
        api_key = kwargs.get('api_key', '')                                 #   API Key
                                                                            # Or (recommended) credentials_file
        api_cfile = kwargs.get('api_cfile', '')                             #   API Credential filename

        display.vv(u'Calling Tetration {} verify: {} scope_id: {}'.format(api_host, api_verify, ids))

        if not api_verify:
            import requests
            requests.packages.urllib3.disable_warnings()

        if api_cfile:
            restclient = RestClient(api_host, credentials_file=api_cfile, verify=api_verify)
        else:
            restclient = RestClient(api_host, api_key=api_key, api_secret=api_secret, verify=api_verify)

        try:
            ids[0]
        except IndexError:
            raise AnsibleError('the scope id or "all" must be specified')

        # Return all scopes
        if ids[0].upper() == LookupModule.ALL: 
            try:
                response = restclient.get('/app_scopes')
            except:
                raise AnsibleError('Connection timeout for {}'.format(api_host))

            display.vvvv(u'Returning all scopes {}'.format(response))
            return response.json()
                                           
        # Return one or more scopes
        response = []

        for scope_id in ids:
            try:
                rc = restclient.get('/app_scopes/{}'.format(scope_id))
            except:
                raise AnsibleError('Connection timeout for {}'.format(api_host))

            if rc.status_code in LookupModule.NOTFOUND:
                response.append(LookupModule.DEFAULT)
                display.vvvv(u'Response: {}'.format(rc.status_code, rc.content))
            else:
                response.append(rc.json())

        display.vvvv(u'Response{}'.format(response))
        return response
