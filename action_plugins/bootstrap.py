# (c) 2015, Matt Schreiber <schreibah@gmail.com>,
# 2012, Michael DeHaan <michael.dehaan@gmail.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os

import ansible.constants as C

from ansible import utils
from ansible import errors
from ansible.callbacks import vvvv
from ansible.runner.return_data import ReturnData


class tmp_keep_remote_files(object):
    '''
    Temporarily sets the value of C.DEFAULT_KEEP_REMOTE_FILES.  A hack to
    prevent ansible.runner._execute_module from deleting the remote temporary
    directory before we've had a chance to upload and run the 'passthrough'
    module.
    '''
    def __init__(self, tmp_value):
        self.tmp_value = tmp_value

    def __enter__(self):
        self.stored_value = C.DEFAULT_KEEP_REMOTE_FILES
        return self.tmp_value

    def __exit__(self, type, value, traceback):
        C.DEFAULT_KEEP_REMOTE_FILES = self.stored_value


class ActionModule(object):

    TRANSFERS_FILES = True

    copy_module_key = 'sources'

    def __init__(self, runner):
        self.runner = runner
        # Instantiate the action_plugin for the 'copy' module
        self.copy_handler = utils.plugins.action_loader.get('copy', runner)

    def _copy(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        return self.copy_handler.run(conn, tmp, 'copy', module_args, inject,
                                     complex_args=complex_args, **kwargs)

    def _filter_recursive(self, operation, options):
        mapped_options = {}

        for key, value in options.iteritems():
            if isinstance(value, dict):
                mapped_options[key] = self._filter_recursive(operation, value)
            elif isinstance(value, list):
                mapped_options[key] = filter(operation, value)
            else:
                if operation(value):
                    mapped_options[key] = value
        vvvv("%s" % mapped_options)

        return mapped_options



    def _partition_options(self, options=None, key=copy_module_key):
        if not options:
            return ({}, {})

        extracted = options.get(key, {})
        rest = {k:v for k, v in options.iteritems() if not k == key}

        return extracted, rest

    def _make_sources_map(self, sources_list=None):
        sources_map = {}

        if sources_list:
            try:
                for item in sources_list:
                    if isinstance(item, basestring):
                        item = utils.parse_kv(item)
                    src = item['src']
                    sources_map[src] = item
            except KeyError:
                raise errors.AnsibleError("All sources must define src=path")

        return sources_map


    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):

        # Filter out the omit token
        complex_args = self._filter_recursive(lambda x: x != self.runner.omit_token, complex_args)

        (
        sources_complex_args_list,
        passthru_complex_args_map
        ) = self._partition_options(complex_args)

        sources_complex_args_map = self._make_sources_map(sources_complex_args_list)

        (
        sources_module_args_hash_list,
        passthru_module_args_hash
        ) = self._partition_options(utils.parse_kv(module_args))

        sources_module_args_map = self._make_sources_map(sources_module_args_hash_list)

        sources_options_map = utils.merge_hash(sources_complex_args_map, sources_module_args_map)
        passthru_options_map = utils.merge_hash(passthru_complex_args_map, passthru_module_args_hash)

        passthru_options_keys = passthru_options_map.keys()
        if len(passthru_options_keys) > 1:
            raise errors.AnsibleError("Only one module can be run at a time; saw modules: %s"
                                      % ', '.join(passthru_options_keys))

        # Iterate over 'copy' files
        for src, options in sources_options_map.iteritems():
            # Construct remote filesystem path
            wanted_dest = options.get('dest', None)

            if wanted_dest is None:
                if tmp is None:
                    tmp = self.runner._make_tmp_path(conn)
                options['dest'] = tmp
            # Interpret relative paths as starting with the remote tmp
            # directory
            elif not wanted_dest.startswith('/'):
                if tmp is None:
                    tmp = self.runner._make_tmp_path(conn)
                options['dest'] = os.path.join(tmp, wanted_dest)

            copy_module_args = utils.serialize_args(sources_module_args_map.get(src, {}))
            copy_complex_args = sources_complex_args_map.get(src, None)

            # Copy source to destination.
            #
            # XXX because the 'copy' action_plugin doesn't pass through
            # persist_files or delete_remote_tmp, we need to make a temporary
            # adjustment to C.DEFAULT_KEEP_REMOTE_FILES.  The 'as' clause is
            # necessary in order to affect C.DEFAULT_KEEP_REMOTE_FILES in the
            # scope of ansible.runner.
            res = None
            with tmp_keep_remote_files(True) as C.DEFAULT_KEEP_REMOTE_FILES:
                res = self._copy(conn, tmp, 'copy', copy_module_args, inject,
                                 complex_args=copy_complex_args)

            # Fail here if files weren't copied over correctly
            if res is not None and not res.is_successful():
                return res

        for passthru_name, passthru_options in passthru_options_map.iteritems():
            passthru_complex_args = passthru_complex_args_map.get(passthru_name, None)
            passthru_module_args = utils.serialize_args(passthru_module_args_hash)

            # Handle things like 'command: do_something'
            if not isinstance(passthru_complex_args, dict):
                if isinstance(passthru_complex_args, basestring):
                    passthru_module_args = passthru_complex_args
                passthru_complex_args = None

            # Instantiate the action_plugin for the wanted module
            passthru_handler = utils.plugins.action_loader.get(passthru_name, self.runner)

            if passthru_handler:
                return passthru_handler.run(conn, tmp, passthru_name,
                                            passthru_module_args, inject,
                                            complex_args=passthru_complex_args,
                                            **kwargs)
            else:
                return self.runner._execute_module(conn, tmp, passthru_name,
                                                   passthru_module_args,
                                                   inject=inject,
                                                   complex_args=passthru_complex_args,
                                                   **kwargs)
