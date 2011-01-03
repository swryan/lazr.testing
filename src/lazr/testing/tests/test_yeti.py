import doctest
import operator
import os
import re
import socket
import sys
import unittest
import warnings

from cStringIO import StringIO

from os.path import dirname

from mocker import ANY, ARGS, KWARGS, MockerTestCase

from zope.testing import testrunner

from lazr.testing.yeti import YetiLayer


class YetiLayerErrorTests(MockerTestCase):

    def setUp(self):
        super(YetiLayerErrorTests, self).setUp()
        env_keys = [
            "YETI",
            "YETI_SERVER",
            "YETI_PORT",
            "YETI_CAPTURE_TIMEOUT",
            "YETI_BROWSER"]

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

        if "YETI_SERVER" in os.environ:
            del os.environ["YETI_SERVER"]
        os.environ["YETI_PORT"] = "4225"
        try:
            try:
                YetiLayer.setUp()
            except ValueError, e:
                msg = str(e)
                self.assertIn(
                    "Failed to execute Yeti server on port 4225", msg)
                self.assertIn(
                    "Address already in use", msg)
            else:
                self.fail("ValueError not raised")
        finally:
            YetiLayer.tearDown()
            s.close()

    def mock_popen(self):
        """Replace subprocess.Popen and make it return a mock process.

        The mock process is returned.
        """
        mock_Popen = self.mocker.replace("subprocess.Popen")
        self.mock_proc = self.mocker.mock()
        mock_Popen(ARGS, KWARGS)
        self.mocker.result(self.mock_proc)
        return self.mock_proc

    def mock_builtin_open(self):
        """Replace built-in open and make it return a mock file.

        The mock file is returned.
        """
        mock_open = self.mocker.replace("__builtin__.open")
        mock_open(ANY)
        self.mock_file = self.mocker.mock()
        self.mocker.result(self.mock_file)
        return self.mock_file

    def test_wait_for_server_startup(self):
        """
        Even if we don't wait for the browser to be captured, we wait
        for the server to start up.
        """
        mock_proc = self.mock_popen()
        mock_file = self.mock_builtin_open()

        with self.mocker.order():
            mock_time = self.mocker.replace("time.time")
            # The first time is to initialize the start time.
            mock_time()
            start_time = 0
            self.mocker.result(start_time)

            # The second time is to check if the timeout is exceeded in
            # the while loop.
            mock_time()
            self.mocker.result(start_time)
            # Go one iteration of the while loop, reporting the server
            # has started.
            mock_proc.poll()
            self.mocker.result(None)
            mock_file.readline()
            self.mocker.result("to run and report the results")

            # The opened file is closed.
            mock_file.close()
            self.mocker.result(None)

            # Last check to make sure the server is running ok.
            mock_proc.poll()
            self.mocker.result(None)

        self.mocker.replay()

        os.environ["YETI_BROWSER"] = ""
        if "YETI_SERVER" in os.environ:
            del os.environ["YETI_SERVER"]
        os.environ["YETI_PORT"] = "4225"

        YetiLayer.setUp()
        self.assertEqual(
            "http://localhost:4225", os.environ["YETI_SERVER"])

    def test_server_fail(self):
        """
        If we a poll of the process returns a non-None value while we
        are waiting, we report that server couldn't be started.
        """
        mock_proc = self.mock_popen()
        mock_file = self.mock_builtin_open()

        with self.mocker.order():
            mock_time = self.mocker.replace("time.time")
            # The first time is to initialize the start time.
            mock_time()
            start_time = 0
            self.mocker.result(start_time)

            # The second time is to check if the timeout is exceeded in
            # the while loop.
            mock_time()
            self.mocker.result(start_time)
            # Go one iteration of the while loop, reporting the server
            # is starting up.
            mock_proc.poll()
            self.mocker.result(None)
            mock_file.readline()
            self.mocker.result("not yeti?")

            # Go another iteration of the while loop, reporting the
            # server failed to start up.
            mock_time()
            self.mocker.result(start_time)
            mock_proc.poll()
            self.mocker.result(1)

            # The opened file is closed.
            mock_file.close()
            self.mocker.result(None)

        self.mocker.replay()

        if "YETI_SERVER" in os.environ:
            del os.environ["YETI_SERVER"]
        os.environ["YETI_PORT"] = "4225"

        try:
            YetiLayer.setUp()
        except ValueError, e:
            msg = str(e)
            self.assertIn(
                "Failed to execute Yeti server on port 4225", msg)
        else:
            self.fail("ValueError not raised")

    def test_server_timeout(self):
        """
        If we don't see that the server is started before the timeout, a
        ValueError is raised, even if the process is still running.
        """
        timeout = 1
        os.environ["YETI_CAPTURE_TIMEOUT"] = "%s" % timeout
        os.environ["YETI_BROWSER"] = ""
        if "YETI_SERVER" in os.environ:
            del os.environ["YETI_SERVER"]
        os.environ["YETI_PORT"] = "4225"

        mock_proc = self.mock_popen()
        mock_file = self.mock_builtin_open()

        with self.mocker.order():
            mock_time = self.mocker.replace("time.time")
            # The first time is to initialize the start time.
            mock_time()
            start_time = 0
            self.mocker.result(start_time)

            # The second time is to check if the timeout is exceeded in
            # the while loop.
            mock_time()
            self.mocker.result(start_time)
            # Go one iteration of the while loop, reporting the server
            # is starting up.
            mock_proc.poll()
            self.mocker.result(None)
            mock_file.readline()
            self.mocker.result("not yeti?")

            # Trigger a timeout.
            mock_time()
            self.mocker.result(start_time + timeout + 1)

            # The opened file is closed.
            mock_file.close()
            self.mocker.result(None)

            # Last check whether the server is still running.
            mock_proc.poll()
            self.mocker.result(None)

            # Since the server is running, it gets terminated.
            mock_proc.terminate()
            self.mocker.result(None)
            mock_proc.wait()
            self.mocker.result(None)

        self.mocker.replay()

        try:
            YetiLayer.setUp()
        except ValueError, e:
            msg = str(e)
            self.assertIn(
                "Failed to execute Yeti server in 1 seconds"
                " on port 4225", msg)
        else:
            self.fail("ValueError not raised")

    def tearDown(self):
        super(YetiLayerErrorTests, self).tearDown()
        self.mocker.restore()


def test_suite():
    suite = unittest.TestSuite()

    if not "YETI" in os.environ:
        warnings.warn("Environment variable 'YETI' not set. "
                      "Skipping 'YETI' tests.")
        return suite

    suite.addTests(unittest.makeSuite(YetiLayerErrorTests))
    return suite
