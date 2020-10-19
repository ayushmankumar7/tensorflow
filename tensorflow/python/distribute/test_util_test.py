# Copyright 2020 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for test utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl.testing import parameterized

from tensorflow.python.distribute import combinations
from tensorflow.python.distribute import strategy_combinations
from tensorflow.python.distribute import test_util
from tensorflow.python.eager import context
from tensorflow.python.eager import def_function
from tensorflow.python.eager import test
from tensorflow.python.framework import config
from tensorflow.python.framework import dtypes
from tensorflow.python.ops import array_ops


@combinations.generate(
    combinations.combine(
        strategy=[
            strategy_combinations.multi_worker_mirrored_2x1_cpu,
            strategy_combinations.multi_worker_mirrored_2x1_gpu,
            strategy_combinations.multi_worker_mirrored_2x2_gpu,
        ] + strategy_combinations.strategies_minus_tpu,
        mode=['eager', 'graph']))
class GatherTest(test.TestCase, parameterized.TestCase):

  def testOne(self, strategy):

    @def_function.function
    def f():
      return array_ops.ones((), dtypes.float32)

    results = test_util.gather(strategy, strategy.run(f))
    self.assertAllEqual(
        self.evaluate(results), [1.] * strategy.num_replicas_in_sync)

  def testNest(self, strategy):

    @def_function.function
    def f():
      return {
          'foo':
              array_ops.ones((), dtypes.float32),
          'bar': [
              array_ops.zeros((), dtypes.float32),
              array_ops.ones((), dtypes.float32),
          ]
      }

    results = test_util.gather(strategy, strategy.run(f))
    self.assertAllEqual(
        self.evaluate(results['foo']), [1.] * strategy.num_replicas_in_sync)
    self.assertAllEqual(
        self.evaluate(results['bar'][0]), [0.] * strategy.num_replicas_in_sync)
    self.assertAllEqual(
        self.evaluate(results['bar'][1]), [1.] * strategy.num_replicas_in_sync)


class LogicalDevicesTest(test.TestCase):

  def testLogicalCPUs(self):
    context._reset_context()
    test_util.set_logical_devices_to_at_least('CPU', 3)
    cpu_device = config.list_physical_devices('CPU')[0]
    self.assertLen(config.get_logical_device_configuration(cpu_device), 3)


if __name__ == '__main__':
  test_util.main()
