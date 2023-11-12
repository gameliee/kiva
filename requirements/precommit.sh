#!/bin/bash
if [[ "$OSTYPE" == "darwin"* ]]; then
    pip-compile --quiet --no-strip-extras requirements/mac-requirements.in
else
    pip-compile --quiet --no-strip-extras requirements/requirements.in
fi
