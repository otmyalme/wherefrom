# wherefrom

On macOS, files may have metadata that provides information about their source. For an image file downloaded from the Internet, that metadata generally consists of the URL of the webpage the file was saved from and the URL of the file itself.

These URLs are stored as an extended file attribute, `com.apple.metadata:kMDItemWhereFroms`, and are shown in Finder using the key “Where from”.

*wherefrom* is a Python command-line application that recursively descends into one or more directories, reads the “where from” value of all regular files it finds, and prints the gathered values as a JSON object.

The application is functional, but not quite finished. The JSON output, in particular, has been added in a rush so that the project is in a state where it can reasonably be mentioned on an résumé.

And *wherefrom* is, perhaps, more of an exercise than a useful tool in any case. The actual task is rather trivial, but the project aims for full test coverage, thorough documentation, and exhaustive error handling that includes clear explanations for every low-level error that could possibly occur, just to see how much effort that takes. (A lot more than expected, it turns out.)

Currently, the application has about 1000 lines of code and 800 lines of comments, with about 60% of the code being tests and 20% error handling.
