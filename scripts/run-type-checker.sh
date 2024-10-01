# Run the type checks.
#
# This script can be run using `c y`.

echo
hatch run type-check:run-type-checks ; EXIT_STATUS=$?
echo
exit $EXIT_STATUS
