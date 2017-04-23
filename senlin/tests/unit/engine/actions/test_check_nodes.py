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

from senlin.common import consts
from senlin.engine.actions import base as ab
from senlin.engine.actions import cluster_action as ca
from senlin.engine import cluster as cm
from senlin.engine import dispatcher
from senlin.objects import action as ao
from senlin.objects import dependency as dobj
from senlin.tests.unit.common import base
from senlin.tests.unit.common import utils


@mock.patch.object(cm.Cluster, 'load')
class ClusterCheckNodesTest(base.SenlinTestCase):

    def setUp(self):
        super(ClusterCheckNodesTest, self).setUp()
        self.ctx = utils.dummy_context()

    @mock.patch.object(ao.Action, 'update')
    @mock.patch.object(ab.Action, 'create')
    @mock.patch.object(dobj.Dependency, 'create')
    @mock.patch.object(dispatcher, 'start_action')
    @mock.patch.object(ca.ClusterAction, '_wait_for_dependents')
    def test__check_nodes(self, mock_wait, mock_start, mock_dep,
                          mock_action, mock_update, mock_load):
        node1 = mock.Mock(id='NODE_1')
        node2 = mock.Mock(id='NODE_2')
        cluster = mock.Mock(id='FAKE_ID', status='old status',
                            status_reason='old reason')
        cluster.nodes = [node1, node2]
        mock_load.return_value = cluster
        mock_action.side_effect = ['NODE_ACTION_1', 'NODE_ACTION_2']

        action = ca.ClusterAction('FAKE_CLUSTER', 'CLUSTER_CHECK', self.ctx)
        action.id = 'CLUSTER_ACTION_ID'

        mock_wait.return_value = (action.RES_OK, 'Everything is Okay')

        # do it
        res_code, res_msg = action._check_nodes()

        # assertions
        self.assertEqual(action.RES_OK, res_code)
        self.assertEqual('Everything is Okay', res_msg)

        mock_load.assert_called_once_with(action.context, 'FAKE_CLUSTER')
        mock_action.assert_has_calls([
            mock.call(action.context, 'NODE_1', 'NODE_CHECK',
                      name='node_check_NODE_1',
                      cause=consts.CAUSE_DERIVED),
            mock.call(action.context, 'NODE_2', 'NODE_CHECK',
                      name='node_check_NODE_2',
                      cause=consts.CAUSE_DERIVED)
        ])
        mock_dep.assert_called_once_with(action.context,
                                         ['NODE_ACTION_1', 'NODE_ACTION_2'],
                                         'CLUSTER_ACTION_ID')
        mock_update.assert_has_calls([
            mock.call(action.context, 'NODE_ACTION_1', {'status': 'READY'}),
            mock.call(action.context, 'NODE_ACTION_2', {'status': 'READY'}),
        ])
        mock_start.assert_called_once_with()
        mock_wait.assert_called_once_with()

    def test__check_nodes_empty(self, mock_load):
        cluster = mock.Mock(id='FAKE_ID', nodes=[], status='old status',
                            status_reason='old reason')
        mock_load.return_value = cluster

        action = ca.ClusterAction(cluster.id, 'CLUSTER_CHECK', self.ctx)

        # do it
        res_code, res_msg = action._check_nodes()

        self.assertEqual(action.RES_OK, res_code)
        self.assertEqual('Nodes status checking completed.', res_msg)

    @mock.patch.object(ao.Action, 'update')
    @mock.patch.object(ab.Action, 'create')
    @mock.patch.object(dobj.Dependency, 'create')
    @mock.patch.object(dispatcher, 'start_action')
    @mock.patch.object(ca.ClusterAction, '_wait_for_dependents')
    def test__check_nodes_failed_waiting(self, mock_wait, mock_start,
                                         mock_dep, mock_action, mock_update,
                                         mock_load):
        node = mock.Mock(id='NODE_1')
        cluster = mock.Mock(id='CLUSTER_ID', status='old status',
                            status_reason='old reason')
        cluster.nodes = [node]
        mock_load.return_value = cluster
        mock_action.return_value = 'NODE_ACTION_ID'

        action = ca.ClusterAction('FAKE_CLUSTER', 'CLUSTER_CHECK', self.ctx)
        action.id = 'CLUSTER_ACTION_ID'

        mock_wait.return_value = (action.RES_TIMEOUT, 'Timeout!')

        res_code, res_msg = action._check_nodes()

        self.assertEqual(action.RES_TIMEOUT, res_code)
        self.assertEqual('Timeout!', res_msg)

        mock_load.assert_called_once_with(self.ctx, 'FAKE_CLUSTER')
        mock_action.assert_called_once_with(
            action.context, 'NODE_1', 'NODE_CHECK',
            name='node_check_NODE_1',
            cause=consts.CAUSE_DERIVED,
        )
        mock_dep.assert_called_once_with(action.context, ['NODE_ACTION_ID'],
                                         'CLUSTER_ACTION_ID')
        mock_update.assert_called_once_with(action.context, 'NODE_ACTION_ID',
                                            {'status': 'READY'})
        mock_start.assert_called_once_with()
        mock_wait.assert_called_once_with()
