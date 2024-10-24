"""
Test the `wherefrom.run` module.
"""

from textwrap import dedent
from wherefrom.run import run


def test_run(environment, capfd):
    """Does the `run()` function run the application?"""
    arguments = [
        f"{environment}/simple/one-item.html",
        f"{environment}/errors/no-such-file.html",
    ]
    run(arguments)
    output = capfd.readouterr()
    assert output.out == dedent(f"""
        {{
          "{environment}/simple/one-item.html": [
            "http://nowhere.test/index.html"
          ]
        }}
    """).lstrip()
    assert output.err == (
        f"Could not collect the contents of “{environment}/errors/no-such-file.html”: "
        "The directory doesn’t exist\n"
    )
