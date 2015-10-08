ansible-bootstrap
=================

An Ansible module for bootstrapping files onto remote systems.  If you have a
role or module that requires, e.g., a Python module to exist on the remote
system, but you don't want to install the library permanently, you can use this
module to upload it to the remote system for the duration of the play.

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

Caveats
-------

This module is designed for single-task dependency bootstrapping: all of the
listed sources are uploaded to the managed node on *each play*.  In addition,
the `copy` module isn't meant to handle large numbers of file uploads (_see_
`ansible-doc copy`), so if your task has a lot of dependencies or if you'll be
using the same dependencies for more than one task, you should probably install
them using one of Ansible's package management modules, or with `synchronize`.

A further word of caution: if you upload the file to anywhere but the play's
remote temporary directory, it won't be cleaned up automatically


Bugs/Misfeatures
----------------

Probably a bunch :).

One known issue is that the return value of `bootstrap` tasks as captured by
`register` contains funky-looking output for Jinja2 filters that evaluate to
`omit`.  This is apparently an unavoidable consequence of how Ansible deals
with `omit` -- it creates a long, unique token that gets substituted for each
instance of `omit`, then laters calls `iteritems` on the task's arguments,
deleting any key-value pairs whose value is that token.  Because Ansible
assumes that the module's arguments are a one-level dictionary, it doesn't
removed `omit` tokens from bootstrap's nested arguments.  Furthermore, the code
responsible for doing this removal gets called only once per task.  In the
`bootstrap` `action_module`, a little recursion (plus cut 'n paste from
`ansible.runner` :), solves the issue of removing `omit` tokens from nested
arguments, but the strange-looking tokens still show up in the module's output.

License
-------

GPLv3

Author Information
------------------

[BaxterStockman](https://github.com/BaxterStockman)
