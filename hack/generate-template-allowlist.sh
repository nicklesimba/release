#!/bin/bash

# This script generates the template allowlist

set -o errexit
set -o nounset
set -o pipefail

CONTAINER_ENGINE=${CONTAINER_ENGINE:-docker}
SKIP_PULL=${SKIP_PULL:-false}

if [[ -n ${BLOCKER:-} ]]; then
    ARGS="--block-new-jobs=$BLOCKER"
fi

${SKIP_PULL} || ${CONTAINER_ENGINE} pull registry.ci.openshift.org/ci/template-deprecator:latest
${CONTAINER_ENGINE} run --rm -v "$PWD:/release:z" registry.ci.openshift.org/ci/template-deprecator:latest \
    ${ARGS:-} \
    --prow-jobs-dir /release/ci-operator/jobs \
    --prow-config-path /release/core-services/prow/02_config/_config.yaml \
    --plugin-config /release/core-services/prow/02_config/_plugins.yaml \
    --allowlist-path /release/core-services/template-deprecation/_allowlist.yaml
