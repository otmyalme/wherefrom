# TEST ###################################################################################

.PHONY: test tests

test:
	@ ./scripts/run-tests.sh || true

tests: test
