SCRIPTS = "scripts"


# BUILD ##################################################################################

.PHONY: build

build:
	@ hatch build


# TEST ###################################################################################

.PHONY: test tests

test tests:
	@ ./$(SCRIPTS)/run-tests.sh || true


# TYPE-CHECK #############################################################################

.PHONY: type types

type types:
	@ ./$(SCRIPTS)/run-type-checker.sh || true


# LINT ###################################################################################

.PHONY: lint

lint:
	@ ./$(SCRIPTS)/run-linter.sh || true


# CLEAN ##################################################################################

.PHONY: clean-all

clean-all: clean-build-artifacts clean-test-files clean-type-checking-cache \
           clean-linter-cache


# BUILD

.PHONY: clean-build-artifacts

clean-build-artifacts:
	@ rm -rf artifacts


# TESTS

.PHONY: clean-test-files clean-test-cache clean-coverage-data clean-html-coverage-report

clean-test-files: clean-test-cache clean-coverage-data clean-html-coverage-report

clean-test-cache:
	@ rm -rf .pytest_cache

clean-coverage-data:
	@ hatch run test:erase-coverage-data

clean-html-coverage-report:
	@ rm -rf coverage


# TYPE CHECKS

.PHONY: clean-type-checking-cache

clean-type-checking-cache:
	@ rm -rf .mypy_cache


# LINTER

.PHONY: clean-linter-cache

 clean-linter-cache:
	@ rm -rf .ruff_cache
