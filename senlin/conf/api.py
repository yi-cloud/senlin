# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
from oslo_config import cfg

from senlin.common.i18n import _


API_GROUP = cfg.OptGroup('senlin_api')
API_OPTS = [
    cfg.IPOpt('bind_host', default='0.0.0.0',
              help=_('Address to bind the server. Useful when '
                     'selecting a particular network interface.')),
    cfg.PortOpt('bind_port', default=8777,
                help=_('The port on which the server will listen.')),
    cfg.IntOpt('backlog', default=4096,
               help=_("Number of backlog requests "
                      "to configure the socket with.")),
    cfg.StrOpt('cert_file',
               help=_("Location of the SSL certificate file "
                      "to use for SSL mode.")),
    cfg.StrOpt('key_file',
               help=_("Location of the SSL key file to use "
                      "for enabling SSL mode.")),
    cfg.IntOpt('workers', min=0, default=0,
               help=_("Number of workers for Senlin service.")),
    cfg.IntOpt('max_header_line', default=16384,
               help=_('Maximum line size of message headers to be accepted. '
                      'max_header_line may need to be increased when using '
                      'large tokens (typically those generated by the '
                      'Keystone v3 API with big service catalogs).')),
    cfg.IntOpt('tcp_keepidle', default=600,
               help=_('The value for the socket option TCP_KEEPIDLE.  This is '
                      'the time in seconds that the connection must be idle '
                      'before TCP starts sending keepalive probes.')),
    cfg.StrOpt('api_paste_config', default="api-paste.ini",
               deprecated_group='paste_deploy',
               help=_("The API paste config file to use.")),
    cfg.BoolOpt('wsgi_keep_alive', default=True,
                deprecated_group='eventlet_opts',
                help=_("If false, closes the client socket explicitly.")),
    cfg.IntOpt('client_socket_timeout', default=900,
               deprecated_group='eventlet_opts',
               help=_("Timeout for client connections' socket operations. "
                      "If an incoming connection is idle for this number of "
                      "seconds it will be closed. A value of '0' indicates "
                      "waiting forever.")),
    cfg.IntOpt('max_json_body_size', default=1048576,
               deprecated_group='DEFAULT',
               help=_('Maximum raw byte size of JSON request body.')),
]


def register_opts(conf):
    conf.register_group(API_GROUP)
    conf.register_opts(API_OPTS, group=API_GROUP)


def list_opts():
    return {
        API_GROUP: API_OPTS,
    }
