# Run the unit tests.
#
# If all tests passed, create the HTML coverage report, then print the coverage report
# to the terminal, but make insufficient test coverage more obvious.
#
# If there were test failures, create the HTML coverage report, but do not print the
# coverage report to the terminal (that would be annoying since it would force the
# developer to scroll up to see the test failures).
#
# The script accepts the following arguments:
#     --skip-tests     Do not run the tests
#     --skip-report    Do not print the coverage report to the terminal
#     --verbose        Run the tests with verbose output
#
# This script can be run using `c tr`, or `c vr` to run it with `--verbose`.
# `c t` only runs the tests, and `c r` only prints the coverage report.

RUN_TESTS=true
PRINT_COVERAGE_REPORT=true
EXTRA_TEST_ARGUMENTS=

# Process the arguments
while [ "$1" ]; do
    case "$1" in
        --skip-tests) RUN_TESTS=false;;
        --skip-report) PRINT_COVERAGE_REPORT=false;;
        --verbose) EXTRA_TEST_ARGUMENTS="$EXTRA_TEST_ARGUMENTS -vv";;
        *) echo "Unknown argument: $1"; exit -1;;
    esac
    shift
done

echo

# Run the tests
if ( $RUN_TESTS ); then
    hatch run test:run-tests $EXTRA_TEST_ARGUMENTS ; TEST_EXIT_STATUS=$?
    echo
    hatch run test:generate-html-coverage-report --fail-under 0
    echo
    if [ $TEST_EXIT_STATUS -ne 0 ]; then
        exit $TEST_EXIT_STATUS
    fi
fi

# Print the coverage report
if ( $PRINT_COVERAGE_REPORT ); then
    hatch run test:print-coverage-report --fail-under 0
    echo
    hatch run test:print-coverage-report > /dev/null; COVERAGE_REPORT_EXIT_STATUS=$?
    if [ $COVERAGE_REPORT_EXIT_STATUS -eq 2 ]; then
        COVERAGE_PERCENTAGE="$(hatch run test:print-coverage-percentage)"
        echo "\033[31;1mInsufficient test coverage: $COVERAGE_PERCENTAGE%\033[0m"
        echo
    fi
    exit $COVERAGE_REPORT_EXIT_STATUS
fi
