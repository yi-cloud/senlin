#!/usr/bin/env python
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Senlin Conductor.
"""
from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr
from oslo_service import service

from senlin.common import consts
from senlin.common import messaging
from senlin.common import profiler
from senlin import objects
from senlin import version


def main():
    logging.register_options(cfg.CONF)
    cfg.CONF(project='senlin', prog='senlin-conductor')
    logging.setup(cfg.CONF, 'senlin-conductor')
    logging.set_defaults()
    gmr.TextGuruMeditation.setup_autorun(version)
    objects.register_all()
    messaging.setup()

    from senlin.conductor import service as conductor

    profiler.setup('senlin-conductor', cfg.CONF.host)
    srv = conductor.ConductorService(cfg.CONF.host, consts.CONDUCTOR_TOPIC)
    launcher = service.launch(cfg.CONF, srv,
                              workers=cfg.CONF.conductor.workers,
                              restart_method='mutate')
    # the following periodic tasks are intended serve as HA checking
    # srv.create_periodic_tasks()
    launcher.wait()
