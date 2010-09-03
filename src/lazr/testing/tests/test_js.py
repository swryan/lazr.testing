import os
import re
import unittest
import doctest
import socket
import operator
import sys
from cStringIO import StringIO

from os.path import dirname

from mocker import MockerTestCase

from zope.testing import testrunner

from lazr.testing.jstestdriver import (
    JsTestDriverTestCase, JsTestDriverLayer)


class JsTestDriverSelfTest(JsTestDriverTestCase):

    config_filename = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                   "js", "tests.conf"))


class JsTestDriverErrorTests(MockerTestCase):

    def setUp(self):
        super(JsTestDriverErrorTests, self).setUp()
        env_keys = [
            "JSTESTDRIVER_SERVER",
            "JSTESTDRIVER_PORT",
            "JSTESTDRIVER_CAPTURE_TIMEOUT",
            "JSTESTDRIVER_BROWSER"]

        def cleanup_non_existing_key(some_key):
            try:
                del os.environ[some_key]
            except KeyError:
                pass

        for key in env_keys:
            if key in os.environ:
                self.addCleanup(
                    operator.setitem, os.environ, key, os.environ[key])
            else:
                self.addCleanup(cleanup_non_existing_key, key)

    def test_binding(self):
        """
        If a specific port is requested, and a server is already started in the
        requested port, then the layer setup fails.
        """
        s = socket.socket()
        try:
            s.bind((socket.gethostbyname(""), 4225))
        except socket.error:
            s.close()
            s = None
            raise

        if "JSTESTDRIVER_SERVER" in os.environ:
            del os.environ["JSTESTDRIVER_SERVER"]
        os.environ["JSTESTDRIVER_PORT"] = "4225"
        try:
            try:
                JsTestDriverLayer.setUp()
            except ValueError, e:
                msg = str(e)
                self.assertIn(
                    "Failed to execute JsTestDriver server on port 4225", msg)
                self.assertIn(
                    "java.lang.RuntimeException: java.net.BindException: "
                    "Address already in use", msg)
            else:
                self.fail("ValueError not raised")
        finally:
            JsTestDriverLayer.tearDown()
            s.close()

    def test_connection_error(self):
        """
        An appropriate message is printed when the JsTestDriver client cannot
        connect to a server.
        """
        runner = getattr(testrunner, "run_internal", testrunner.run)
        root_directory = os.path.abspath(
            dirname(dirname(dirname(dirname(__file__)))))
        defaults = [
            "--path", root_directory,
            "-m", "lazr.testing.tests.test_js",
            "-t", "JsTestDriverSelfTest"]
        arguments = [
            "--no-progress"]
        os.environ["JSTESTDRIVER_SERVER"] = "http://localhost:4226"
        os.environ["JSTESTDRIVER_SELFTEST"] = "1"
        # Patch stdout to prevent spurious output
        test_stdout = StringIO()
        old_stdout = sys.stdout
        sys.stdout = test_stdout
        try:
            try:
                runner(defaults, arguments)
            except ValueError, e:
                msg = str(e)
                self.assertIn("Failed to execute JsTestDriver tests for", msg)
                self.assertIn(
                    "lazr/testing/tests/js/tests.conf "
                    "(http://localhost:4226)", msg)
                self.assertIn(
                    "java.lang.RuntimeException: java.net.ConnectException: "
                    "Connection refused", msg)
            else:
                self.fail("ValueError not raised")
        finally:
            sys.stdout = old_stdout

    def test_timeout(self):
        """
        If we fail to capture a browser within the specified timeout, an
        appropriate message is shown. In order to test that, let's set the
        browser to be empty so that the JsTestDriver server doesn't capture a
        browser automatically, and set the timeout to a very short time so we
        don't wait for too long.
        """
        os.environ["JSTESTDRIVER_CAPTURE_TIMEOUT"] = "1"
        os.environ["JSTESTDRIVER_BROWSER"] = ""
        if "JSTESTDRIVER_SERVER" in os.environ:
            del os.environ["JSTESTDRIVER_SERVER"]
        os.environ["JSTESTDRIVER_PORT"] = "4225"

        try:
            try:
                JsTestDriverLayer.setUp()
            except ValueError, e:
                msg = str(e)
                self.assertIn("Failed to capture a browser in 1 seconds", msg)
            else:
                self.fail("ValueError not raised")
        finally:
            JsTestDriverLayer.tearDown()


def test_suite():
    suite = unittest.TestSuite()

    if os.environ.get("JSTESTDRIVER_SELFTEST"):
        suite.addTests(unittest.makeSuite(JsTestDriverSelfTest))
    else:
        suite.addTests(unittest.makeSuite(JsTestDriverErrorTests))

        def setUp(test):
            test.globs["this_directory"] = os.path.abspath(dirname(__file__))
            test.globs["root_directory"] = dirname(
                dirname(dirname(test.globs["this_directory"])))

        from zope.testing import renormalizing
        checker = renormalizing.RENormalizing([
            (re.compile(r"\d+[.]\d\d\d seconds"), "N.NNN seconds"),
            (re.compile(r"\d+[.]\d\d\d s"), "N.NNN s"),
            (re.compile(r"\d+[.]\d\d\d{"), "N.NNN{"),
            (re.compile(r":\w+[\d\.]+ "), ":BrowserN.N.N.N "),
            (re.compile(r":\w+_\d+_\w+ "), ":BrowserN.N.N.N "),

            # omit traceback entries for jstestdriver.py or doctest.py from
            # output:
            (re.compile(r'^ +File "[^\n]*/lazr/testing/jstestdriver.py"'
                        r", [^\n]+\n[^\n]+\n",
                        re.MULTILINE),
             r"...\n"),
            ])
        suite.addTests(doctest.DocFileSuite(
            "jstestdriver.txt",
            setUp=setUp,
            checker=checker,
            optionflags=(doctest.ELLIPSIS |
                         doctest.NORMALIZE_WHITESPACE |
                         doctest.REPORT_NDIFF)))
    return suite
