import os
import sys
import time
import signal
import tempfile
import subprocess
import xml.parsers.expat

from mocker import MockerTestCase

from zope.testing.testrunner.runner import TestResult as ZopeTestResult


class JsTestDriverError(Exception):

    def __init__(self, message):
        message = "\n".join(filter(None, [line.strip() for line in message]))
        super(JsTestDriverError, self).__init__(message)


class JsTestDriverFailure(Exception):

    def __init__(self, message):
        message = "\n".join(filter(None, [line.strip() for line in message]))
        super(JsTestDriverFailure, self).__init__(message)


class JsTestDriverResult(object):

    failureException = JsTestDriverFailure

    def __init__(self, classname, name, browser, duration):
        self.classname = classname
        self.name = name
        self.browser = browser
        self.duration = duration
        self.message = []

    def countTestCases(self):
        return 1

    def shortDescription(self):
        return None

    def id(self):
        return "%s.%s:%s" % (self.classname, self.name, self.browser)

    def __str__(self):
        return "%s:%s (%s)" % (self.name, self.browser, self.classname)

    def __repr__(self):
        return "<%s testMethod=%s, browser=%s>" % (self.classname,
                                                   self.name, self.browser)

class GlobalJsTestDriverResult(object):

    failureException = JsTestDriverFailure

    def __init__(self, name, test_id):
        self.name = name
        self.test_id = test_id
        self.message = []

    def countTestCases(self):
        return 1

    def shortDescription(self):
        return None

    def id(self):
        return self.test_id

    def __str__(self):
        return self.name


class JsTestDriverResultParser(object):
    """Parse the XML output from I{JsTestDriver} and report to a L{TestResult}.

    Python's L{unittest} module uses the L{TestResult} class to report
    success/error/failure, calling the appropriate methods.

    A L{JsTestDriverResult} object is instantiated for each matched
    test case, in order to properly report the underlying test name
    and test class.
    """

    def __init__(self, expat, result):
        self.expat = expat
        self.result = result
        self.test_result = None

        # attach expat parser methods
        for name, value in type(self).__dict__.items():
            if isinstance(value, property):
                continue
            try:
                setattr(expat, name, getattr(self, name))
            except AttributeError:
                pass

    def StartElementHandler(self, tag, attributes):
        if tag == "testsuite":
            pass
        elif tag == "testcase":
            classname = attributes["classname"]
            name, browser = attributes["name"].split(":", 1)
            duration = attributes["time"]
            self.test_result = JsTestDriverResult(classname, name,
                                                  browser, duration)
            self.result.startTest(self.test_result)
        elif tag == "error":
            self.test_result.error_message = attributes["message"]
        elif tag == "failure":
            self.test_result.failure_type = attributes["type"]
        else:
            raise ValueError("Unexpected tag: %s" % tag)

    def EndElementHandler(self, tag):
        if tag == "testsuite":
            pass
        elif tag == "testcase":
            if isinstance(self.result, ZopeTestResult):
                self.result.options.output.test_success(
                    self.test_result, float(self.test_result.duration))
            else:
                self.result.addSuccess(self.test_result)
            self.result.stopTest(self.test_result)
        elif tag == "error":
            try:
                raise JsTestDriverError(self.test_result.message)
            except:
                self.result.addError(self.test_result, sys.exc_info())
        elif tag == "failure":
            try:
                raise JsTestDriverFailure(self.test_result.message)
            except:
                self.result.addFailure(self.test_result, sys.exc_info())
        else:
            raise ValueError("Unexpected tag: %s" % tag)

    def CharacterDataHandler(self, data):
        if self.test_result is not None:
            self.test_result.message.append(data)


def startJsTestDriver():
    jstestdriver = os.environ["JSTESTDRIVER"]
    port = os.environ.get("JSTESTDRIVER_PORT", "4224")

    capture_timeout = int(os.environ.get(
        "JSTESTDRIVER_CAPTURE_TIMEOUT", "30"))
    browser = os.environ.get(
        "BROWSER",
        os.path.join(os.path.dirname(__file__), "browser_wrapper.py"))

    cmd = jstestdriver.split() + ["--port", port]
    wait_for_browser = False
    if browser:
        wait_for_browser = True
        cmd.extend(["--browser", browser])

    # Redirect stderr through a temporary file, so that it doesn't
    # block and we don't get an IOError on readline(), apparently
    # caused by an unhandled SIGINT (Google for it. :)
    fd, name = tempfile.mkstemp()
    stderr = open(name)
    captured = False
    rc = None

    try:
        proc = subprocess.Popen(cmd,
                                shell=False,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=fd,
                                close_fds=True)

        if wait_for_browser:
            # Give the server process a few seconds to capture the browser.
            output = []
            start = time.time()
            while time.time() - start < capture_timeout:
                rc = proc.poll()
                if rc is not None:
                    break
                line = stderr.readline()
                if not line:
                    # time.sleep(0.1)
                    continue
                output.append(line)
                # A browser was captured, no reason to wait any longer.
                if line.startswith("INFO: Browser Captured:"):
                    captured = True
                    break
    finally:
        stderr.close()

    if rc is None:
        rc = proc.poll()
    if rc is not None:
        raise ValueError(
            "Failed to execute JsTestDriver server on port %s:"
            "\nError: (%s) %s" %
            (port, rc, "\n".join(output)))
    elif not captured and wait_for_browser:
        # Kill the process ourselves, since it failed to capture a
        # browser within the time we specified but did not exit by
        # itself.
        terminateProcess(proc)
        raise ValueError(
            "Failed to capture a browser in %d seconds:"
            "\nError: %s" %
            (capture_timeout, "\n".join(output)))
    else:
        os.environ["JSTESTDRIVER_SERVER"] = (
            "http://localhost:%s" % port)
    return proc


def terminateProcess(proc):
    try:
        proc.terminate()
    except AttributeError:
        os.kill(proc.pid, signal.SIGTERM)
    proc.wait()


class JsTestDriverLayer(object):
    """Manages startup/shutdown of a I{JsTestDriver} server.
    """

    @classmethod
    def setUp(cls):
        cls.proc = None
        if os.environ.get("JSTESTDRIVER_SERVER") is None:
            cls.proc = startJsTestDriver()

    @classmethod
    def tearDown(cls):
        if cls.proc is not None:
            # If the process was created by us, then that means the
            # environment variable has been set by ourselves too, so
            # we must unset it.
            del os.environ["JSTESTDRIVER_SERVER"]
            terminateProcess(cls.proc)


class JsTestDriverTestCase(MockerTestCase):
    """Controls a I{JsTestDriver} client for a specific configuration.

    Test output from I{JsTestDriver} is captured and then parsed and
    reported to unittest through clever usage of the TestResult class.

    Optionally, if tests are being run with zope.testrunner, we also
    report the time that I{JsTestDriver} took for each test.

    We require the L{config_filename} class variable to be set by
    subclasses, and that's the only configuration needed.
    """
    layer = JsTestDriverLayer

    def setUp(self):
        super(JsTestDriverTestCase, self).setUp()
        self.output_dir = self.makeDir()

    def _runTest(self, result):
        jstestdriver = os.environ["JSTESTDRIVER"]
        server = os.environ["JSTESTDRIVER_SERVER"]
        cmd = jstestdriver.split() + ["--config",
                                      self.config_filename,
                                      "--testOutput",
                                      self.output_dir,
                                      "--server",
                                      server,
                                      "--tests",
                                      "all"]
        proc = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0:
            raise ValueError(
                "Failed to execute JsTestDriver tests for:\n"
                "%s (%s)\nError: %s" %
                (self.config_filename, server, stderr))
        if stderr:
            test_result = GlobalJsTestDriverResult(str(self), self.id())
            result.startTest(test_result)
            result.addFailure(
                test_result, (RuntimeError, RuntimeError(stderr), None))

    def _reportResults(self, result):
        """Parse generated test results and report them to L{unittest}.
        """
        for fname in os.listdir(self.output_dir):
            output = open(os.path.join(self.output_dir, fname), "r")
            try:
                body = output.read()
            finally:
                output.close()

            expat = xml.parsers.expat.ParserCreate()
            parser = JsTestDriverResultParser(expat, result)
            expat.Parse(body, 1)

    def run(self, result=None):
        if result is None:
            result = self.defaultTestResult()
        self.setUp()

        try:
            self._runTest(result)
            self._reportResults(result)
        finally:
            self.tearDown()

    def runTest(self):
        self.run()

