import os
import time
import fnmatch
import signal
import tempfile
import subprocess

from unittest import TestCase
from subunit import ProtocolTestCase


def startYeti():
    yeti = os.environ["YETI"]
    port = os.environ.get("YETI_PORT", "4422")

    capture_timeout = int(os.environ.get(
        "YETI_CAPTURE_TIMEOUT", "30"))

    cmd = yeti.split() + ["--port", port, "--server"]

    browser = os.environ.get("YETI_BROWSER", "default")

    if browser:
        cmd.extend(["--browsers", browser])

    # Redirect stderr through a temporary file, so that it doesn't
    # block and we don't get an IOError on readline(), apparently
    # caused by an unhandled SIGINT (Google for it. :)
    fd, name = tempfile.mkstemp()
    stderr = open(name)
    server_started = False
    rc = None

    try:
        proc = subprocess.Popen(cmd,
                                shell=False,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=fd,
                                close_fds=True)

        # Give the server process a few seconds to start, and
        # capture the browser if needed.
        output = []
        start = time.time()
        while time.time() - start < capture_timeout:
            rc = proc.poll()
            if rc is not None:
                break
            line = stderr.readline()
            if not line:
                continue
            output.append(line)
            if line.startswith("Running tests locally with:"):
                server_started = True
                break
            if line.startswith("to run and report the results"):
                server_started = True
                break
    finally:
        stderr.close()

    if rc is None:
        rc = proc.poll()
    if rc is not None:
        raise ValueError(
            "Failed to execute Yeti server on port %s:"
            "\nError: (%s) %s" %
            (port, rc, "\n".join(output)))
    if not server_started:
        terminateProcess(proc)
        raise ValueError(
            "Failed to execute Yeti server in %d seconds on port %s:"
            "\nError: (%s) %s" %
            (capture_timeout, port, rc, "\n".join(output)))
    else:
        os.environ["YETI_SERVER"] = (
            "http://localhost:%s" % port)
    return proc


def terminateProcess(proc):
    try:
        proc.terminate()
    except AttributeError:
        os.kill(proc.pid, signal.SIGTERM)
    proc.wait()


class YetiLayer(object):
    """Manages startup/shutdown of a I{Yeti} server.
    """

    @classmethod
    def setUp(cls):
        cls.proc = None
        if os.environ.get("YETI_SERVER") is None:
            cls.proc = startYeti()

    @classmethod
    def tearDown(cls):
        if cls.proc is not None:
            # If the process was created by us, then that means the
            # environment variable has been set by ourselves too, so
            # we must unset it.
            del os.environ["YETI_SERVER"]
            terminateProcess(cls.proc)


class YetiTestCase(TestCase):
    """Controls a I{Yeti} client for a specific configuration.

    Test output from I{Yeti} is captured and then parsed and
    reported to unittest through clever subunit usage.

    We require a L{tests_directory} class variable to be set by
    subclasses, and that's the only configuration needed.
    """
    layer = YetiLayer

    def _runTest(self, result):
        yeti = os.environ["YETI"]
        port = os.environ.get("YETI_PORT", "4422")
        cmd = yeti.split() + ["--formatter=subunit",
                              "--solo=1",
                              "--port=%s" % port]
        for base, dirs, files in os.walk(self.tests_directory):
            for filename in fnmatch.filter(files, "test_*.html"):
                cmd.append(os.path.join(base, filename))
        proc = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        suite = ProtocolTestCase(proc.stdout)
        suite.run(result)
        proc.wait()

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        self.setUp()
        try:
            self._runTest(result)
        finally:
            self.tearDown()

    def runTest(self):
        self.run()
