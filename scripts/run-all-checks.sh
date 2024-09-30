# Run the unit tests, the type checker, and the linter.
#
# Print the test coverage report at the end, not immediately after running the tests.
#
# If there are failing tests, type errors, or linter issues, stop after the step that
# discovered the issue.
#
# This script can be run using `make checks`.

set -e

print_header() {
    # Print the given string with a blue background for the entire line.
    echo "\n\\033[1;104m $1 \\033[K\\033[0m"
}

print_header "Unit Tests"
./scripts/run-tests.sh --skip-report

print_header "Type Checks"
./scripts/run-type-checker.sh

print_header "Linter"
./scripts/run-linter.sh

print_header "Test Coverage"
./scripts/run-tests.sh --skip-tests
