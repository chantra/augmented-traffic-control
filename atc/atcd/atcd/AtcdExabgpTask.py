#
#  Copyright (c) 2014, Facebook, Inc.
#  All rights reserved.
#
#  This source code is licensed under the BSD-style license found in the
#  LICENSE file in the root directory of this source tree. An additional grant
#  of patent rights can be found in the PATENTS file in the same directory.
#
#
import tempfile
import time
import os

from atcd.AtcdThriftHandlerTask import AtcdThriftHandlerTask
from sparts.sparts import option
from sparts.tasks.periodic import PeriodicTask


class AtcdExabgpTask(PeriodicTask):
    INTERVAL = 30.0
    OPT_PREFIX = 'exabgp'

    exabgp_expiry = option(
        default=60,
        metavar='EXABGP_EXPIRY',
        type=int,
        help='Time before exabgp announcement expire [%(default)s]',
        name='expiry',
    )

    exabgp_file = option(
        default='/var/lib/exabgp/commands/atcd',
        metavar='EXABGP_FILE',
        help='path to the file to write exabgp routes to [%(default)s]',
        name='path'
    )

    exabgp_adv_ip = option(
        default='',
        help='List of IPs that need to be constantly advertised through BGP',
        name='ip',
    )

    def initTask(self):
        super(AtcdExabgpTask, self).initTask()
        self.required_task = AtcdThriftHandlerTask.factory()

    def execute(self):
        self.logger.info('Executing AtcdExabgpTask')

        AtcdMainTask = self.service.requireTask(
            self.required_task
        )
        ips = AtcdMainTask.getShapedIps()
        expiry = int(time.time()) + self.exabgp_expiry
        try:
            tmpfile = tempfile.NamedTemporaryFile(delete=False)
            self.logger.info('Writing exabgp routes to %s' % tmpfile.name)
            tmpfile.write('%d\n' % expiry)
            for ip in [self.exabgp_adv_ip] + ips:
                # FIXME: this assumes ipv4
                tmpfile.write('route %s/32 next-hop self\n' % ip)
            tmpfile.close()
            self.logger.info(
                'Moving %s to %s' % (tmpfile.name, self.exabgp_file)
            )
            os.chmod(tmpfile.name, 0644)
            os.rename(tmpfile.name, self.exabgp_file)
        except Exception:
            # log failure to update exabgp but don't do anything about it.
            self.logger.exception('Updating exabgp file')
