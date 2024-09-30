# Run the linter.
#
# This script can be run using `make lint`.

echo
hatch run lint:run-linter ; EXIT_STATUS=$?
echo
exit $EXIT_STATUS
