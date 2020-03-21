# Copyright 2016-2017 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import, division, print_function, unicode_literals

import json
import os
import sys

from argparse import ArgumentTypeError
from datetime import datetime, timedelta

from c7n import cli, version, commands
from c7n.resolver import ValuesFrom
from c7n.resources import aws
from c7n.schema import ElementSchema, generate
from c7n.utils import yaml_dump

from .common import BaseTest, TextTestIO


class CliTest(BaseTest):
    """ A subclass of BaseTest with some handy functions for CLI related tests. """

    def patch_account_id(self):

        def test_account_id(options):
            options.account_id = self.account_id

        self.patch(aws, "_default_account_id", test_account_id)

    def get_output(self, argv):
        """ Run cli.main with the supplied argv and return the output. """
        out, err = self.run_and_expect_success(argv)
        return out

    def capture_output(self):
        out = TextTestIO()
        err = TextTestIO()
        self.patch(sys, "stdout", out)
        self.patch(sys, "stderr", err)
        return out, err

    def run_and_expect_success(self, argv):
        """ Run cli.main() with supplied argv and expect normal execution. """
        self.patch_account_id()
        self.patch(sys, "argv", argv)
        out, err = self.capture_output()
        try:
            cli.main()
        except SystemExit as e:
            self.fail(
                "Expected sys.exit would not be called. Exit code was ({})".format(
                    e.code
                )
            )
        return out.getvalue(), err.getvalue()

    def run_and_expect_failure(self, argv, exit_code):
        """ Run cli.main() with supplied argv and expect exit_code. """
        self.patch_account_id()
        self.patch(sys, "argv", argv)
        out, err = self.capture_output()
        # clear_resources()
        with self.assertRaises(SystemExit) as cm:
            cli.main()
        self.assertEqual(cm.exception.code, exit_code)
        return out.getvalue(), err.getvalue()

    def run_and_expect_exception(self, argv, exception):
        """ Run cli.main() with supplied argv and expect supplied exception. """
        self.patch_account_id()
        self.patch(sys, "argv", argv)
        # clear_resources()
        try:
            cli.main()
        except exception:
            return
        self.fail("Error: did not raise {}.".format(exception))


class SchemaTest(CliTest):

    def test_schema(self):

        # no options
        self.run_and_expect_success(["custodian", "schema"])

        # summary option
        self.run_and_expect_success(["custodian", "schema", "--summary"])

        # json option
        self.run_and_expect_success(["custodian", "schema", "--json"])

        # with just a cloud
        self.run_and_expect_success(["custodian", "schema", "aws"])

        # with just a resource
        self.run_and_expect_success(["custodian", "schema", "ec2"])

        # with just a mode
        self.run_and_expect_success(["custodian", "schema", "mode"])

        # mode.type
        self.run_and_expect_success(["custodian", "schema", "mode.phd"])

        # resource.actions
        self.run_and_expect_success(["custodian", "schema", "ec2.actions"])

        # resource.filters
        self.run_and_expect_success(["custodian", "schema", "ec2.filters"])

        # specific item
        self.run_and_expect_success(["custodian", "schema", "ec2.filters.tag-count"])

    def test_invalid_options(self):

        # invalid resource
        self.run_and_expect_failure(["custodian", "schema", "fakeresource"], 1)

        # invalid category
        self.run_and_expect_failure(["custodian", "schema", "ec2.arglbargle"], 1)

        # invalid item
        self.run_and_expect_failure(
            ["custodian", "schema", "ec2.filters.nonexistent"], 1
        )

        # invalid number of selectors
        self.run_and_expect_failure(["custodian", "schema", "ec2.filters.and.foo"], 1)

    def test_schema_output(self):

        output = self.get_output(["custodian", "schema"])
        self.assertIn("aws.ec2", output)
        # self.assertIn("azure.vm", output)
        # self.assertIn("gcp.instance", output)

        output = self.get_output(["custodian", "schema", "aws"])
        self.assertIn("aws.ec2", output)
        self.assertNotIn("azure.vm", output)
        self.assertNotIn("gcp.instance", output)

        output = self.get_output(["custodian", "schema", "aws.ec2"])
        self.assertIn("actions:", output)
        self.assertIn("filters:", output)

        output = self.get_output(["custodian", "schema", "ec2"])
        self.assertIn("actions:", output)
        self.assertIn("filters:", output)

        output = self.get_output(["custodian", "schema", "ec2.filters"])
        self.assertNotIn("actions:", output)
        self.assertIn("filters:", output)

        output = self.get_output(["custodian", "schema", "ec2.filters.image"])
        self.assertIn("Help", output)

    def test_schema_expand(self):
        # refs should only ever exist in a dictionary by itself
        test_schema = {
            '$ref': '#/definitions/filters_common/value_from'
        }
        result = ElementSchema.schema(generate()['definitions'], test_schema)
        self.assertEqual(result, ValuesFrom.schema)

    def test_schema_multi_expand(self):
        test_schema = {
            'schema1': {
                '$ref': '#/definitions/filters_common/value_from'
            },
            'schema2': {
                '$ref': '#/definitions/filters_common/value_from'
            }
        }

        expected = yaml_dump({
            'schema1': {
                'type': 'object',
                'additionalProperties': 'False',
                'required': ['url'],
                'properties': {
                    'url': {'type': 'string'},
                    'format': {'enum': ['csv', 'json', 'txt', 'csv2dict']},
                    'expr': {'oneOf': [
                        {'type': 'integer'},
                        {'type': 'string'}]}
                }
            },
            'schema2': {
                'type': 'object',
                'additionalProperties': 'False',
                'required': ['url'],
                'properties': {
                    'url': {'type': 'string'},
                    'format': {'enum': ['csv', 'json', 'txt', 'csv2dict']},
                    'expr': {'oneOf': [
                        {'type': 'integer'},
                        {'type': 'string'}]}
                }
            }
        })

        result = yaml_dump(ElementSchema.schema(generate()['definitions'], test_schema))
        self.assertEqual(result, expected)

    def test_schema_expand_not_found(self):
        test_schema = {
            '$ref': '#/definitions/filters_common/invalid_schema'
        }
        result = ElementSchema.schema(generate()['definitions'], test_schema)
        self.assertEqual(result, None)


class ReportTest(CliTest):

    def test_report(self):
        policy_name = "ec2-running-instances"
        valid_policies = {
            "policies": [
                {
                    "name": policy_name,
                    "resource": "ec2",
                    "query": [{"instance-state-name": "running"}],
                }
            ]
        }
        yaml_file = self.write_policy_file(valid_policies)

        output = self.get_output(
            ["custodian", "report", "-s", self.output_dir, yaml_file]
        )
        self.assertIn("InstanceId", output)
        self.assertIn("i-014296505597bf519", output)

        # ASCII formatted test
        output = self.get_output(
            [
                "custodian",
                "report",
                "--format",
                "grid",
                "-s",
                self.output_dir,
                yaml_file,
            ]
        )
        self.assertIn("InstanceId", output)
        self.assertIn("i-014296505597bf519", output)

        # json format
        output = self.get_output(
            ["custodian", "report", "--format", "json", "-s", self.output_dir, yaml_file]
        )
        self.assertTrue("i-014296505597bf519", json.loads(output)[0]['InstanceId'])

        # empty file
        temp_dir = self.get_temp_dir()
        empty_policies = {"policies": []}
        yaml_file = self.write_policy_file(empty_policies)
        self.run_and_expect_failure(
            ["custodian", "report", "-s", temp_dir, yaml_file], 1
        )

        # more than 1 policy
        policies = {
            "policies": [
                {"name": "foo", "resource": "s3"}, {"name": "bar", "resource": "ec2"}
            ]
        }
        yaml_file = self.write_policy_file(policies)
        self.run_and_expect_failure(
            ["custodian", "report", "-s", temp_dir, yaml_file], 1
        )

    def test_warning_on_empty_policy_filter(self):
        # This test is to examine the warning output supplied when -p is used and
        # the resulting policy set is empty.  It is not specific to the `report`
        # subcommand - it is also used by `run` and a few other subcommands.

        policy_name = "test-policy"
        valid_policies = {
            "policies": [
                {
                    "name": policy_name,
                    "resource": "s3",
                    "filters": [{"tag:custodian_tagging": "not-null"}],
                }
            ]
        }
        yaml_file = self.write_policy_file(valid_policies)
        temp_dir = self.get_temp_dir()

        bad_policy_name = policy_name + "-nonexistent"
        log_output = self.capture_logging("custodian.commands")
        self.run_and_expect_failure(
            ["custodian", "report", "-s", temp_dir, "-p", bad_policy_name, yaml_file], 1
        )
        self.assertIn(policy_name, log_output.getvalue())

        bad_resource_name = "foo"
        self.run_and_expect_failure(
            ["custodian", "report", "-s", temp_dir, "-t", bad_resource_name, yaml_file],
            1,
        )


class LogsTest(CliTest):

    def test_logs(self):
        temp_dir = self.get_temp_dir()

        # Test 1 - empty file
        empty_policies = {"policies": []}
        yaml_file = self.write_policy_file(empty_policies)
        self.run_and_expect_failure(["custodian", "logs", "-s", temp_dir, yaml_file], 1)

        # Test 2 - more than one policy
        policies = {
            "policies": [
                {"name": "foo", "resource": "s3"}, {"name": "bar", "resource": "ec2"}
            ]
        }
        yaml_file = self.write_policy_file(policies)
        self.run_and_expect_failure(["custodian", "logs", "-s", temp_dir, yaml_file], 1)

        # Test 3 - successful test
        p_data = {
            "name": "test-policy",
            "resource": "rds",
            "filters": [
                {"key": "GroupName", "type": "security-group", "value": "default"}
            ],
            "actions": [{"days": 10, "type": "retention"}],
        }
        yaml_file = self.write_policy_file({"policies": [p_data]})
        output_dir = os.path.join(os.path.dirname(__file__), "data", "logs")
        self.run_and_expect_success(["custodian", "logs", "-s", output_dir, yaml_file])


class TabCompletionTest(CliTest):
    """ Tests for argcomplete tab completion. """

    def test_schema_completer(self):
        self.assertIn("aws.rds", cli.schema_completer("rd"))
        self.assertIn("aws.s3.", cli.schema_completer("s3"))
        self.assertListEqual([], cli.schema_completer("invalidResource."))
        self.assertIn("aws.rds.actions", cli.schema_completer("rds."))
        self.assertIn("aws.s3.filters.", cli.schema_completer("s3.filters"))
        self.assertIn("aws.s3.filters.event", cli.schema_completer("s3.filters.eve"))
        self.assertListEqual([], cli.schema_completer("rds.actions.foo.bar"))

    def test_schema_completer_wrapper(self):

        class MockArgs(object):
            summary = False

        args = MockArgs()
        self.assertIn("aws.rds", cli._schema_tab_completer("rd", args))

        args.summary = True
        self.assertListEqual([], cli._schema_tab_completer("rd", args))

