#!/bin/zsh
# Play every test in headless Chrome (run build.sh first). Screenshots go to build/shots/.
cd "${0:A:h}"; mkdir -p ../build/shots
for t in example phone bad_icon hero; do echo "== $t"; node lib/play.js ../build/example tests/$t.json ../build/shots/ex 2>&1 | grep -v "^EVAL" ; done
echo "== three_d"; node lib/play.js ../build/test3d-web tests/three_d.json ../build/shots/t 2>&1 | grep -v "^EVAL"
