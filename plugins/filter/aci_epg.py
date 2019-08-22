#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#     Copyright (c) 2019 World Wide Technology
#     All rights reserved.
#     GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
#     author: joel.king@wwt.com
#     written:  22 August 2019
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': '@joelwking'
}
DOCUMENTATION = """
filter: aci_epg

version_added: "2.9"

short_description: Query Tetration Scopes (or AppScopes), Cluster names to the equivalent EGP name for ACI

description:
  - Converts the Tetration application scopeid, clustername, etc. to be converted to an ACI EPG name

requirements:
  - none

options:
    filter_name:
        description:
          - the name of a Tetration application scopeid, clustername, etc. to be converted to an ACI EPG name
        required: true

author:
    - Joel W. King (@joelwking)
"""

EXAMPLES = """

        - hosts: localhost
          gather_facts: no
          connection: local

          vars:
            test_names:
              - "Default"
              - "Default: Tetration"
              - "EPG-ONE"
              - "EPG-TWO"
              - ""                  # return what was input
              - Failure             # return what was input

          tasks:
            - name: Convert Tetration scope id to ACI EPG name
              debug:
                msg: "{{ item | aci_epg }}"
              loop: "{{ test_names }}"

"""

RETURN = """
   returns the converted string or the input value if no conversion applied
"""

from ansible.errors import AnsibleFilterError


class Scope(object):
    """
    Class to translate from Tetration naming conventions to ACI
    """
    def __init__(self):
        """
        """                                          
        self.DEFAULT = "Default"                           # You can map "Default" and "Default: Tetration"
        self.EXTERNAL = "EPG-WWT-EXT"                      # to an EPG called "EPG-WWT-EXT" for now.
        self.KEY = "EPG-"                                  # If it starts with "EPG-", it's an endpoint group.
        return

    def to_aci(self, scope):
        """
            Map Tetration scopes to ACI EPGs
        """
        if self.KEY in scope:
            return '{}{}'.format(self.KEY, scope.split(self.KEY)[1])

        if self.DEFAULT in scope[0:len(self.DEFAULT)]:
            return self.EXTERNAL
        return

def aci_epg(name):
    """
    call the Scope class logic to convert
    """
    return Scope().to_aci(name)


# ---- Ansible filters ----

class FilterModule(object):
    """
    Tetration to ACI EGP filter
    """

    def filters(self):
        return {
            'aci_epg': aci_epg
        }