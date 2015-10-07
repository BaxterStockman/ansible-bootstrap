ansible-bootstrap
=================

An Ansible module for bootstrapping files onto remote systems.  If you have a
role or module that requires, e.g., a Python module to exist on the remote
system, but you don't want to install the library permanently, you can use this
module to upload it to the remote system for the duration of the play.

(A word of caution: if you upload the file to anywhere but the play's remote
temporary directory, it won't be cleaned up automatically)

Example Playbook
----------------

`bootstrap` works in two stages:

- First, it uploads any files given as a list specified under the `sources`
  key.  Each item in the list is passed through to the `copy` module, so any
  valid `copy` option will work here, too.
- After all `sources` items have been process, `bootstrap` attempts to load the
  named module's `action_plugin`.  If that is not available, it executes the
  module directly.

`bootstrap` assumes that anything other than the `sources` list represents a
task specification -- so, in the sample playbook below, `bootstrap` would
attempt to find and run the `action_plugin` or module for `super_sweet_module`.
It is an error to specify more than one such module.

```yaml
- hosts: servers
  roles:
    # Use this if you haven't copied the module into your ANSIBLE_LIBRARY
    - role: bootstrap
  tasks:
    - name: bootstrap python libraries onto managed host
      bootstrap:
        sources:
          - src: /path/to/one/library.py
          - src: /path/to/another/library.py
          - src=/path/to/something/else/entirely.py dest=/an/absolute/path
        super_sweet_module:
          key1: value1
          key2: value2
          key3: value3
```

License
-------

GPLv3

Author Information
------------------

[BaxterStockman](https://github.com/BaxterStockman)
