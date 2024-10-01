# Run the unit tests, the type checker, and the linter.
#
# Print the test coverage report at the end, not immediately after running the tests.
#
# If there are failing tests, type errors, or linter issues, stop after the step that
# discovered the issue.
#
# The script accepts the following arguments:
#     --skip-tests              Do not run the tests
#     --skip-type-checks        Do not run the type checks
#     --skip-linter             Do not run the linter
#     --skip-coverage-report    Do not print the coverage report to the terminal
#     --verbose-tests           Run the tests with verbose output
#     --fix-linter-issues       Automatically fix linter issues
#
# This script can be run using `c`. See that script’s documentation for an explanation
# as to how to specify the optional arguments.

set -e

RUN_TESTS=true
EXTRA_TEST_ARGUMENTS=
RUN_TYPE_CHECKER=true
RUN_LINTER=true
EXTRA_LINTER_ARGUMENTS=
PRINT_COVERAGE_REPORT=true

# Process the arguments
while [ "$1" ]; do
    case "$1" in
        --skip-tests) RUN_TESTS=false;;
        --skip-type-checker) RUN_TYPE_CHECKER=false;;
        --skip-linter) RUN_LINTER=false;;
        --skip-coverage-report) PRINT_COVERAGE_REPORT=false;;
        --verbose-tests) EXTRA_TEST_ARGUMENTS="$EXTRA_TEST_ARGUMENTS --verbose";;
        --fix-linter-issues) EXTRA_LINTER_ARGUMENTS="$EXTRA_LINTER_ARGUMENTS --fix";;
        *) echo "Unknown argument: $1"; exit -1;;
    esac
    shift
done


print_header() {
    # Print the given string with a blue background for the entire line.
    echo "\n\\033[1;104m $1 \\033[K\\033[0m"
}


if ( $RUN_TESTS ); then
    print_header "Unit Tests"
    ./scripts/run-tests.sh --skip-report $EXTRA_TEST_ARGUMENTS
fi

if ( $RUN_TYPE_CHECKER ); then
    print_header "Type Checks"
    ./scripts/run-type-checker.sh
fi

if ( $RUN_LINTER ); then
    print_header "Linter"
    ./scripts/run-linter.sh $EXTRA_LINTER_ARGUMENTS
fi

if ( $PRINT_COVERAGE_REPORT ); then
    print_header "Test Coverage"
    ./scripts/run-tests.sh --skip-tests
fi
