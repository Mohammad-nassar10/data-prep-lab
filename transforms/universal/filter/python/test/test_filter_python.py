# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################
import os

from filter_test_support import AbstractPythonFilterTransformTest


class TestPythonFilterTransform(AbstractPythonFilterTransformTest):
    def _get_test_file_directory(self) -> str:
        dir = os.path.abspath(os.path.dirname(__file__))
        return dir