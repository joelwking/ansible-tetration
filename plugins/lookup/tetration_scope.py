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
lookup: tetration_scope

version_added: "2.9"

short_description: Query Tetration API for one or more Scopes (or AppScopes)

description:
  - Uses the Python API Client for Tetration Analytics to return one or more Scopes (or AppScopes)
  - to enrich data from the Network Policy Publisher.

requirements:
  - tetpyclient

options:
    app_scope_id:
        description:
          - Non keyword argument which specifies one or more scope ids or the keyword 'all'
        required: true

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
          - Either these credendials must be specified above or the credential filename specified.
        required: true

author:
    - Joel W. King (@joelwking)
"""

EXAMPLES = """
  tasks:
    - name: Query (q) a specific scope id as a literal
      set_fact:
        scope_id_literals: "{{ q('tetration_scope', '5c9a9926497d4f7f0b9dbc07', api_host='10.253.239.4', api_key='5f79a256e', api_secret='951bdbb') }}"

    - name: Specify the scope id as a variable, using `lookup` instead of `query`
      set_fact:
        scope_id_vars: "{{ lookup('tetration_scope', app_scope_id, api_host=tet.host, api_key=tet.api.key, api_secret=tet.api.secret) }}"

    - name: Iterate over all scope ids
      debug:
        msg: '{{ item.name }} {{item.short_name }}'
      loop: "{{ query('tetration_scope', 'all', api_host=tet.host, api_cfile=cfile) }}"

    - name: Specify multiple scopes ids
      set_fact:
        scope_id_two: "{{ query('tetration_scope', '5c9a9926497d4f7f0b9dbc07', '5c50bd60497d4f06cc9dbc1f', api_host=tet.host, api_cfile=cfile)  }}"

  when using a credential file, it should be in a form as follows:

  {
  "api_key": "5f79a256e03c48123456",
  "api_secret": "951bdbb1266123456"
  }

"""

RETURN = """
  scopeObjectAttributes:
      description:
        - a list of scope object attributes, refer to https://<tetration>/documentation/ui/openapi/api_scopes.html#scopes

"""

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.utils.display import Display

try:
    from tetpyclient import RestClient
except ImportError:
    raise AnsibleError('Python API Client for Tetration Analytics required, install using pip install tetpyclient')

display = Display()                                        # Use the Display class for logging


class LookupModule(LookupBase):
    """
        Ansible Plugin:Lookup  Return Application Scopes from Tetration API
    """

    DEFAULT = dict(short_name='CLUSTER', name='CLUSTER', description='Scope Id: Not Found')
    NOTFOUND = (404, 403)
    ALL = 'ALL'

    def run(self, ids, **kwargs):
        """
            Execute the 'tetration_scope' plugin
            NOTE: Ansible sends the non-keyword value as a list.

            The keyword arguments identify the Tetration host, credentials and SSL options
            Either specify the `api_secret` and `api_key` or use the `api_cfile` to specify a credential file

            By default, if not specified, SSL certification verification is disabled
        """

        api_host = 'https://{}'.format(kwargs.get('api_host', '192.0.2.1'))
        api_verify = kwargs.get('api_verify', False)

        # Either specify
        api_secret = kwargs.get('api_secret', '')
        api_key = kwargs.get('api_key', '')

        # Or a JSON formatted credentials_file
        api_cfile = kwargs.get('api_cfile', '')

        display.vvv(u'Calling Tetration {} verify: {} scope_id: {}'.format(api_host, api_verify, ids))

        if not api_verify:
            import requests
            requests.packages.urllib3.disable_warnings()

        # Verify we have non-keyword input
        try:
            ids[0]
        except IndexError:
            raise AnsibleError('the scope id or "all" must be specified')

        # Are credentials in a file or passed as a keyword argument?
        if api_cfile:
            restclient = RestClient(api_host, credentials_file=api_cfile, verify=api_verify)
        else:
            restclient = RestClient(api_host, api_key=api_key, api_secret=api_secret, verify=api_verify)

        # Do we want all scopes or specific ones?
        if ids[0].upper() == LookupModule.ALL:
            return self.all_scopes(restclient)
        else:
            return self.specific_scopes(restclient, ids)

    def all_scopes(self, restclient):
        """
            Return a list of all the scopes known to Tetration
        """
        try:
            response = restclient.get('/app_scopes')
        except:
            raise AnsibleError('Connection timeout for {}'.format(restclient.server_endpoint))

        display.vvv(u'Returning all scopes {}'.format(response))

        return response.json()

    def specific_scopes(self, restclient, ids):
        """
            Return a list of one or more scopes specified in the list 'ids'
        """
        response = []

        for scope_id in ids:
            try:
                rc = restclient.get('/app_scopes/{}'.format(scope_id))
            except:
                raise AnsibleError('Connection timeout for {}'.format(restclient.server_endpoint))

            if rc.status_code in LookupModule.NOTFOUND:
                response.append(LookupModule.DEFAULT)
            else:
                response.append(rc.json())

            display.vvv(u'Scope_Id: {} Status: {} Content: {}'.format(scope_id, rc.status_code, rc.content))

        return response
