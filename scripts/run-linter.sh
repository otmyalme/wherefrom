# Run the linter.
#
# The script accepts the following arguments:
#     --fix    Automatically fix linter issues, if possible
#
# This script can be run using `c l`, or `c f` to run it with `--fix`.

EXTRA_ARGUMENTS=

# Process the arguments
while [ "$1" ]; do
    case "$1" in
        --fix) EXTRA_ARGUMENTS="$EXTRA_ARGUMENTS --fix";;
        *) echo "Unknown argument: $1"; exit -1;;
    esac
    shift
done


echo
hatch run lint:run-linter $EXTRA_ARGUMENTS ; EXIT_STATUS=$?
echo
exit $EXIT_STATUS
