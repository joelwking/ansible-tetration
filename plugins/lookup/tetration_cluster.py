#!/usr/bin/env python
#
#     GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
#     Copyright (c) 2019 World Wide Technology, LLC.
#     All rights reserved.
#
#     author: joel.king@wwt.com
#     written:  1 October  2019
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

short_description: Query Tetration API for a list of Clusters, which are members of Applications.

description:
  - Uses the Python API Client for Tetration Analytics to return the Clusters associated with an Application
  - to enrich data from the Network Policy Publisher.

requirements:
  - tetpyclient

options:
    app_name:
        description:
          - Non keyword argument which specifies one or more application names
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
          - Either these credentials must be specified above or the credential filename specified.
        required: true

author:
    - Joel W. King (@joelwking)
"""

EXAMPLES = """

vars:
  tet:
      host: "10.253.239.4"

  cfile: '{{ playbook_dir }}/files/kingjoe_atc_tetration.json'
  app_name: 'DAAnE'

tasks:
  - name: get clusters for the specified application name
    debug:
      msg: '{{ item.id }} {{ item.name }} {{ item.description }} {{ item.consistent_uuid }}'
    loop: "{{ query('tetration_cluster', app_name, api_host=tet.host, api_cfile=cfile)  }}"


  when using a credential file, it should be in a form as follows:

  {
  "api_key": "5f79a256e03c48123456",
  "api_secret": "951bdbb1266123456"
  }

"""

RETURN = """
  clusterObjectAttributes:
      description:
        - a list of cluster object attributes, refer to https://<tetration>/documentation/ui/openapi/api_clusters.html

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
        Ansible Plugin:Lookup  Return Clusters for an Application from Tetration API
    """

    NOTFOUND = (404, 403)
    ALL = 'ALL'

    def run(self, app_names, **kwargs):
        """
            Execute the 'tetration_cluster' plugin
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

        display.vvv(u'Calling Tetration {} verify: {} application name: {}'.format(api_host, api_verify, app_names))

        if not api_verify:
            import requests
            requests.packages.urllib3.disable_warnings()

        # Verify we have non-keyword input
        try:
            app_names[0]
        except IndexError:
            raise AnsibleError('one or more application names must be specified')

        # Are credentials in a file or passed as a keyword argument?
        if api_cfile:
            restclient = RestClient(api_host, credentials_file=api_cfile, verify=api_verify)
        else:
            restclient = RestClient(api_host, api_key=api_key, api_secret=api_secret, verify=api_verify)

        return self.clusters(restclient, app_names)

    def clusters(self, restclient, app_names):
        """
            Return a list of clussters for the specified application(s)
        """

        all_clusters = []

        try:
            apps = restclient.get('/applications/')
        except:
            raise AnsibleError('Connection timeout for {}'.format(restclient.server_endpoint))

        for app in apps.json():
            if app.get('name') in app_names:
                display.vvv(u'found application: {} id: {}'.format(app.get('name'), app.get('id')))
                try:
                    clusters = restclient.get('/applications/{}/clusters/'.format(app['id']))
                except:
                    raise AnsibleError('Connection timeout for {}'.format(restclient.server_endpoint))

                all_clusters.extend(clusters.json())

        return all_clusters
