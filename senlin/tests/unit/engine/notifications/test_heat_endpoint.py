# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock

from senlin.common import context
from senlin.engine.notifications import heat_endpoint
from senlin import objects
from senlin.tests.unit.common import base


@mock.patch('oslo_messaging.NotificationFilter')
class TestHeatNotificationEndpoint(base.SenlinTestCase):
    @mock.patch('senlin.rpc.client.EngineClient')
    def test_init(self, mock_rpc, mock_filter):
        x_filter = mock_filter.return_value
        event_map = {
            'orchestration.stack.delete.end': 'DELETE',
        }
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )

        mock_filter.assert_called_once_with(
            publisher_id='^orchestration.*',
            event_type='^orchestration\.stack\..*',
            context={'project_id': '^PROJECT$'})
        mock_rpc.assert_called_once_with()
        self.assertEqual(x_filter, endpoint.filter_rule)
        self.assertEqual(mock_rpc.return_value, endpoint.rpc)
        for e in event_map:
            self.assertIn(e, endpoint.STACK_FAILURE_EVENTS)
            self.assertEqual(event_map[e], endpoint.STACK_FAILURE_EVENTS[e])
        self.assertEqual('PROJECT', endpoint.project_id)
        self.assertEqual('CLUSTER_ID', endpoint.cluster_id)

    @mock.patch.object(context.RequestContext, 'from_dict')
    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info(self, mock_rpc, mock_context, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {
            'tags': {
                'cluster_id=CLUSTER_ID',
                'cluster_node_id=FAKE_NODE',
                'cluster_node_index=123',
            },
            'stack_identity': 'PHYSICAL_ID',
            'user_identity': 'USER',
            'state': 'DELETE_COMPLETE',
        }
        metadata = {'timestamp': 'TIMESTAMP'}
        call_ctx = mock.Mock()
        mock_context.return_value = call_ctx

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        x_rpc.call.assert_called_once_with(call_ctx, 'node_recover', mock.ANY)
        req = x_rpc.call.call_args[0][2]
        self.assertIsInstance(req, objects.NodeRecoverRequest)
        self.assertEqual('FAKE_NODE', req.identity)
        expected_params = {
            'event': 'DELETE',
            'state': 'DELETE_COMPLETE',
            'stack_id': 'PHYSICAL_ID',
            'timestamp': 'TIMESTAMP',
            'publisher': 'PUBLISHER',
            'operation': 'REBUILD',
        }
        self.assertEqual(expected_params, req.params)

    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_event_type_not_interested(self, mock_rpc, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {'tags': {'cluster_id': 'CLUSTER_ID'}}
        metadata = {'timestamp': 'TIMESTAMP'}

        res = endpoint.info(ctx, 'PUBLISHER',
                            'orchestration.stack.create.start',
                            payload, metadata)

        self.assertIsNone(res)
        self.assertEqual(0, x_rpc.node_recover.call_count)

    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_no_tag(self, mock_rpc, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {'tags': None}
        metadata = {'timestamp': 'TIMESTAMP'}

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        self.assertEqual(0, x_rpc.node_recover.call_count)

    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_empty_tag(self, mock_rpc, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {'tags': []}
        metadata = {'timestamp': 'TIMESTAMP'}

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        self.assertEqual(0, x_rpc.node_recover.call_count)

    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_no_cluster_in_tag(self, mock_rpc, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {'tags': ['foo', 'bar']}
        metadata = {'timestamp': 'TIMESTAMP'}

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        self.assertEqual(0, x_rpc.node_recover.call_count)

    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_no_node_in_tag(self, mock_rpc, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {'tags': ['cluster_id=C1ID']}
        metadata = {'timestamp': 'TIMESTAMP'}

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        self.assertEqual(0, x_rpc.node_recover.call_count)

    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_cluster_id_not_match(self, mock_rpc, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {
            'tags': ['cluster_id=FOOBAR', 'cluster_node_id=N2'],
            'user_identity': 'USER',
        }
        metadata = {'timestamp': 'TIMESTAMP'}

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        self.assertEqual(0, x_rpc.node_recover.call_count)

    @mock.patch.object(context.RequestContext, 'from_dict')
    @mock.patch('senlin.rpc.client.EngineClient')
    def test_info_default_values(self, mock_rpc, mock_context, mock_filter):
        x_rpc = mock_rpc.return_value
        recover_action = {'operation': 'REBUILD'}
        endpoint = heat_endpoint.HeatNotificationEndpoint(
            'PROJECT', 'CLUSTER_ID', recover_action
        )
        ctx = mock.Mock()
        payload = {
            'tags': [
                'cluster_id=CLUSTER_ID',
                'cluster_node_id=NODE_ID'
            ],
            'user_identity': 'USER',
        }
        metadata = {'timestamp': 'TIMESTAMP'}
        call_ctx = mock.Mock()
        mock_context.return_value = call_ctx

        res = endpoint.info(ctx, 'PUBLISHER', 'orchestration.stack.delete.end',
                            payload, metadata)

        self.assertIsNone(res)
        x_rpc.call.assert_called_once_with(call_ctx, 'node_recover', mock.ANY)
        req = x_rpc.call.call_args[0][2]
        self.assertIsInstance(req, objects.NodeRecoverRequest)
        self.assertEqual('NODE_ID', req.identity)
        expected_params = {
            'event': 'DELETE',
            'state': 'Unknown',
            'stack_id': 'Unknown',
            'timestamp': 'TIMESTAMP',
            'publisher': 'PUBLISHER',
            'operation': 'REBUILD',
        }
        self.assertEqual(expected_params, req.params)
