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

from ansible.module_utils.basic import *
from ansible import utils
from ansible import errors
from ansible.runner.return_data import ReturnData

class ActionModule(object):

    TRANSFERS_FILES = True

    def __init__(self, runner):
        self.runner = runner

    def run(self, conn, tmp, module_name, module_args, inject, complex_args=None, **kwargs):
        ''' handler for nginx_config operations '''

        # extract passthrough arguments from module_args

        # construct remote filesystem path

        # if path doesn't start with /, assume that it is relative to the
        # remote temporary directory

        # get path to local utils library
        utils_src = os.path.join(self.runner.basedir, 'library', 'utils')

        # ensure temporary directory exists on target
        #if "tmp" not in tmp:
        if tmp is None:
            tmp= self.runner._make_tmp_path(conn)

        # upload library files to temporary directory using the 'copy' module
        copy_module_args = utils.merge_module_args('', dict(
            src=utils_src,
            dest=tmp,
            original_basename=os.path.basename(utils_src),
            follow=True,
        ))

        res = None
        if self.runner.noop_on_check(inject):
            return ReturnData(conn=conn, comm_ok=True, result=dict(skipped=True))
        else:
            # Instantiate the action_plugin for the 'copy' module
            copy_handler = utils.plugins.action_loader.get('copy', self.runner)

            # FIXME handle complex_args -- some of that stuff should probably
            # be passed through to 'copy' (or maybe not?)
            res = copy_handler.run(conn, tmp, 'copy', copy_module_args,
                                   inject=inject)

            # Fail here if libs weren't copied over correctly
            if res is not None and not res.is_successful():
                return res


        return self.runner._execute_module(conn, tmp, 'nginx_config',
                                           module_args, inject=inject,
                                           complex_args=complex_args)
