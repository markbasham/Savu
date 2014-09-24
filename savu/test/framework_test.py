# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: framework_test
   :platform: Unix
   :synopsis: unittest test class for plugin utils

.. moduleauthor:: Mark Basham <scientificsoftware@diamond.ac.uk>

"""

import unittest
import tempfile

from savu.core import process
from savu.plugins import utils as pu
from savu.test import test_utils as tu

base_class_name = "savu.plugins.plugin"


class FrameworkTest(unittest.TestCase):

    def setUp(self):
        self.plugin_list = [base_class_name]

    def test_pipeline(self):
        temp_dir = tempfile.gettempdir()
        first_plugin = pu.load_plugin(None, self.plugin_list[0])
        if self.plugin_list[0] == base_class_name:
            return
        input_data = tu.get_appropriate_input_data(first_plugin)[0]
        process.run_plugin_chain(input_data, self.plugin_list, temp_dir)


class SimpleReconstructionTest(FrameworkTest):

    def setUp(self):
        self.plugin_list = ["savu.plugins.timeseries_field_corrections",
                            "savu.plugins.simple_recon"]


class SimpleReconWithRawMedianFilteringTest(FrameworkTest):

    def setUp(self):
        self.plugin_list = ["savu.plugins.median_filter",
                            "savu.plugins.timeseries_field_corrections",
                            "savu.plugins.simple_recon"]


class SimpleReconWithProjectionMedianFilteringTest(FrameworkTest):

    def setUp(self):
        self.plugin_list = ["savu.plugins.timeseries_field_corrections",
                            "savu.plugins.median_filter",
                            "savu.plugins.simple_recon"]


class SimpleReconWithVolumeMedianFilteringTest(FrameworkTest):

    def setUp(self):
        self.plugin_list = ["savu.plugins.timeseries_field_corrections",
                            "savu.plugins.simple_recon",
                            "savu.plugins.median_filter"]


class SimpleReconWithMedianFilteringTest(FrameworkTest):

    def setUp(self):
        self.plugin_list = ["savu.plugins.median_filter",
                            "savu.plugins.timeseries_field_corrections",
                            "savu.plugins.median_filter",
                            "savu.plugins.simple_recon",
                            "savu.plugins.median_filter"]

if __name__ == "__main__":
    unittest.main()