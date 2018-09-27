create_user
=========

Creates user accounts on a server for training on Python, Tetration and Ansible.

Requirements
------------

None

Role Variables
--------------

    class_size: 0                       # Number of student account to create
    comment: CSE training               # Comment for the account  
    base_name: student                  # Base name, student1, student2, etc.
    state: present                      # Add the user by default
    shell: /bin/bash                    # Default shell for the student account
                                        # Decoder ring for mapping present to 'no', absent to 'yes'
    remove:
      present: no
      absent: yes

Dependencies
------------

None

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    #
    #  Create student user accounts
    #
    - include_role:
        name: create_user
      vars:
          class_size: "{{ students }}"
      when: students > 0
      tags: create_user


License
-------

GNU General Public License v3.0

Author Information
------------------

joel.king@wwt.com @joelwking
