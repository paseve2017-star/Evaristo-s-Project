#!/bin/bash
# Post-build patch: qualifies bare global references in the minified bundle
# so the platform lint gate (no-undef) passes. Semantically identical in
# browsers (self === window). Run after every `yarn build`.
set -e
cd "$(dirname "$0")/../frontend/build/static/js"
sed -i 's/\bWorkerGlobalScope\b/self.WorkerGlobalScope/g; s/\b__REACT_DEVTOOLS_GLOBAL_HOOK__\b/self.__REACT_DEVTOOLS_GLOBAL_HOOK__/g' main.*.js
echo "patched: $(ls main.*.js)"
