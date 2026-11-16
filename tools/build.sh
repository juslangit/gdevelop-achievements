#!/bin/zsh
# Build the extension and the example, check every instruction with GDevelop's own library,
# normalize the example to the editor's format and export a playable web build to build/example.
set -e
cd "${0:A:h}"
python3 build_extension.py
python3 build_example.py
node lib/build_html5.js "../example/Achievements Example.json" ../build/example --normalize
