# Common tasks. On Windows use `python run_tests.py ...` directly (see README).
PYTHON ?= python

.PHONY: install dev list smoke regression e2e integration all selftest lint typecheck traceability clean

install:
	$(PYTHON) -m pip install -r requirements.txt

dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

list:
	$(PYTHON) run_tests.py --list

smoke:
	$(PYTHON) run_tests.py --smoke

regression:
	$(PYTHON) run_tests.py --regression

e2e:
	$(PYTHON) run_tests.py --e2e

integration:
	$(PYTHON) run_tests.py --integration

all:
	$(PYTHON) run_tests.py

selftest:
	$(PYTHON) run_tests.py --selftest

lint:
	ruff check . && ruff format --check .

typecheck:
	mypy .

traceability:
	$(PYTHON) run_tests.py --traceability

clean:
	rm -rf reports .cache .mypy_cache .ruff_cache
	find . -name __pycache__ -type d -exec rm -rf {} +
