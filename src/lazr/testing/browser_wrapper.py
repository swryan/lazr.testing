#!/usr/bin/env python

import os
import sys
import webbrowser

if __name__ == "__main__":
    if len(sys.argv) == 2:
        browser = os.environ.get("LANDSCAPE_BROWSER")
        webbrowser.get(browser).open(sys.argv[1])
