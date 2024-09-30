# Run the unit tests.
#
# If all tests passed, create the HTML coverage report, then print the coverage report
# to the terminal, but make insufficient test coverage more obvious.
#
# If there were test failures, create the HTML coverage report, but do not print the
# coverage report to the terminal (that would be annoying since it would force the
# developer to scroll up to see the test failures).
#
# This script can be run using `make test`.

echo
hatch run test:run-tests ; TEST_EXIT_STATUS=$?
echo
hatch run test:generate-html-coverage-report --fail-under 0
echo
if [[ $TEST_EXIT_STATUS -ne 0 ]]; then
    exit $TEST_EXIT_STATUS
fi
hatch run test:print-coverage-report --fail-under 0
echo
hatch run test:print-coverage-report > /dev/null ; COVERAGE_REPORT_EXIT_STATUS=$?
if [[ $COVERAGE_REPORT_EXIT_STATUS -eq 2 ]]; then
    COVERAGE_PERCENTAGE="$(hatch run test:print-coverage-percentage)"
    echo "\033[31;1mInsufficient test coverage: $COVERAGE_PERCENTAGE%\033[0m"
    echo
fi
exit $COVERAGE_REPORT_EXIT_STATUS
