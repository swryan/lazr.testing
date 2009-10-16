# Simple makefile for lazr.testing.
#
#
PYTHON_VERSION=
PYTHON=python${PYTHON_VERSION}
WD:=$(shell pwd)
PY=$(WD)/bin/py

# Default target
build: $(PY)

eggs:
	mkdir eggs

download-cache:
	@echo "Missing ./download-cache."
	@exit 1

# The download-cache dependency comes *before* eggs so that developers get the
# warning before the eggs directory is made.  The target for the eggs directory
# is only there for deployment convenience.
bin/buildout: download-cache eggs
	$(SHHH) PYTHONPATH= $(PYTHON) bootstrap.py \
                --ez_setup-source=ez_setup.py \
		--download-base=download-cache/dist --eggs=eggs

$(PY): bin/buildout buildout.cfg setup.py
	PYTHONPATH= ./bin/buildout -c buildout.cfg


clean:
	rm -fr bin

.PHONY: build clean
