#!/usr/bin/env bash

set -eo pipefail

.openshift-ci/gcp/command.sh .openshift-ci/crawler/repackage.sh
