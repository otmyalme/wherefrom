# BUILD ##################################################################################

.PHONY: build

build:
	@ hatch build


# TEST ###################################################################################

.PHONY: test tests

test:
	@ ./scripts/run-tests.sh || true

tests: test


# CLEAN ##################################################################################

.PHONY: clean-all

clean-all: clean-build-artifacts clean-test-files


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
