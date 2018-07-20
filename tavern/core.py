import logging
import os
import io
from collections import OrderedDict
from typing import List, Dict
from datetime import datetime

import yaml

from contextlib2 import ExitStack
from box import Box

from tavern.response.rest import RestResponse
from .util.general import load_global_config
from .util import exceptions
from .util.dict_util import format_keys
from .util.delay import delay
from .util.loader import IncludeLoader
from .printer import log_pass, log_fail

from .plugins import get_extra_sessions, get_request_type, get_verifiers, get_expected

from .schemas.files import verify_tests


logger = logging.getLogger(__name__)


def run_test(in_file, test_spec, global_cfg) -> dict:
    """Run a single tavern test

    Note that each tavern test can consist of multiple requests (log in,
    create, update, delete, etc).

    The global configuration is copied and used as an initial configuration for
    this test. Any values which are saved from any tests are saved into this
    test block and can be used for formatting in later stages in the test.

    Args:
        in_file (str): filename containing this test
        test_spec (dict): The specification for this test
        global_cfg (dict): Any global configuration for this test

    Raises:
        TavernException: If any of the tests failed
    """

    # pylint: disable=too-many-locals

    # Initialise test config for this test with the global configuration before
    # starting
    test_block_config = dict(global_cfg)

    if "variables" not in test_block_config:
        test_block_config["variables"] = {}

    tavern_box = Box({
        "env_vars": dict(os.environ),
    })

    test_block_config["variables"]["tavern"] = tavern_box
    tests: OrderedDict = {
        'all_passed': True,
        'tests': list(),
        'passed': list(),
        'failed': list(),
        'timing': {
            'total': 0,
            'min': 0,
            'average': 0,
            'max': 0
        }
    }

    if not test_spec:
        logger.warning("Empty test block in %s", in_file)
        return tests

    if test_spec.get("includes"):
        for included in test_spec["includes"]:
            if "variables" in included:
                formatted_include = format_keys(included["variables"], {"tavern": tavern_box})
                test_block_config["variables"].update(formatted_include)

    test_block_name = test_spec["test_name"]

    logger.info("Running test : %s", test_block_name)
    with ExitStack() as stack:
        sessions = get_extra_sessions(test_spec)

        for name, session in sessions.items():
            logger.debug("Entering context for %s", name)
            stack.enter_context(session)

        # Run tests in a path in order
        times = list()
        for stage in test_spec["stages"]:
            start_time = datetime.now()
            fail = False
            name = stage["name"]
            test_info = {'name': name, 'passed': False, 'expected': None, 'actual': None, 'errors': None, 'time_ms': 0}

            try:
                r = get_request_type(stage, test_block_config, sessions)
            except exceptions.MissingFormatError:
                log_fail(stage, None, None)
                fail = True

            tavern_box.update(request_vars=r.request_vars)

            try:
                expected = get_expected(stage, test_block_config, sessions)
                test_info['expected'] = expected
            except exceptions.TavernException:
                log_fail(stage, None, None)
                fail = True

            delay(stage, "before")

            logger.info("Running stage : %s", name)

            try:
                response = r.run()
            except exceptions.TavernException:
                log_fail(stage, None, expected)
                fail = True

            response_body = None if response.text is str() else response.text
            test_info['actual'] = {'requests': {'status_code': response.status_code, 'body': response_body}}

            verifiers: List[RestResponse] = get_verifiers(stage, test_block_config, sessions, expected)
            test_info['errors'] = verifiers[0].errors if len(verifiers) > 0 else []

            for v in verifiers:
                try:
                    saved = v.verify(response)
                except exceptions.TavernException:
                    log_fail(stage, v, expected)
                    fail = True
                else:
                    test_block_config["variables"].update(saved)
                    log_pass(stage, verifiers)

            test_info['passed'] = (fail is False)
            tests['all_passed'] = (test_info['passed'] is tests['all_passed'])

            test_info['time_ms'] = (datetime.now() - start_time).microseconds / 1000
            times.append(test_info['time_ms'])

            tests['tests'].append(test_info)
            if test_info['passed'] is True:
                tests['passed'].append(test_info)
            else:
                tests['failed'].append(test_info)

            tavern_box.pop("request_vars")
            delay(stage, "after")

    tests['timing'].update({
        'total': round(sum(times), 2),
        'min': min(times),
        'average': round(sum(times) / len(times), 2),
        'max': max(times)
    })

    return tests

def run(in_file: str, tavern_global_cfg=[]) -> dict:
    """Run all tests contained in a file

    For each test this makes sure it matches the expected schema, then runs it.
    There currently isn't something like pytest's `-x` flag which exits on first
    failure.

    Todo:
        the tavern_global_cfg argument should ideally be called
        'global_cfg_paths', but it would break the API so we just rename it below

    Note:
        This function DOES NOT read from the pytest config file. This is NOT a
        pytest-reliant part of the code! If you specify global config in
        pytest.ini this will not be used here!

    Args:
        in_file (str): file to run tests on
        tavern_global_cfg (List[str]): file containing Global config for all tests

    Returns:
        bool: Whether ALL tests passed or not
    """

    info = {
        'all_passed': False,
        'tests': list(),
        'passed': list(),
        'failed': list(),
        'timing': list()
    }

    global_cfg_paths = tavern_global_cfg
    global_cfg = load_global_config(global_cfg_paths)

    with io.open(in_file, "r", encoding="utf-8") as infile:
        # Multiple documents per file => multiple test paths per file
        for test_spec in yaml.load_all(infile, Loader=IncludeLoader):
            if not test_spec:
                logger.warning("Empty document in input file '%s'", in_file)
                continue

            try:
                verify_tests(test_spec)
            except exceptions.BadSchemaError:
                info['all_passed'] = False
                continue

            try:
                info = run_test(in_file, test_spec, global_cfg)
            except exceptions.TestFailError:
                continue
    return info
