#!/usr/bin/env python3

import sys
import argparse
import json
import logging
import os
import yaml

logging.basicConfig(format='[%(asctime)s] %(message)s')
logger = logging.getLogger('validate-release-jobs')
logger.setLevel(logging.INFO)

release_definition_path = 'core-services/release-controller/_releases'
job_definitions_paths = ['ci-operator/jobs/openshift/release', 'ci-operator/jobs/openshift/multiarch', 'ci-operator/jobs/openshift/hypershift', 'ci-operator/jobs/openshift/microshift']


def raise_on_duplicates(ordered_pairs):
    d = {}
    for k, v in ordered_pairs:
        if k in d:
            raise ValueError(f'Duplicate key: {k} for value: {v}')
        d[k] = v
    return d


def read_release_definitions(path):
    definitions = {}
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                if entry.name.endswith('.json'):
                    with open(entry, 'r', encoding='utf-8') as release:
                        definitions.update({entry.name: json.load(release, object_pairs_hook=raise_on_duplicates)})
    return definitions


def read_job_definitions(path):
    definitions = {}
    with os.scandir(path) as entries:
        for entry in entries:
            if entry.is_file():
                if entry.name.endswith('.yaml'):
                    with open(entry, 'r', encoding='utf-8') as release:
                        definitions.update({entry.name: yaml.load(release, Loader=yaml.SafeLoader)})
    return definitions


def get_job_data(release_definitions):
    data = []
    for release_name in release_definitions:
        release = release_definitions[release_name]
        for job_type in 'verify', 'periodic':
            if job_type in release:
                for release_verification_name in release[job_type]:
                    data.append((release_name, release_verification_name, release[job_type][release_verification_name]['prowJob']['name']))
    return data


def validate_jobs(data, definitions):
    missing = []
    for source, verification, name in data:
        logger.debug('Searching for job: %s', name)
        found = False
        for definition in definitions:
            for key in definition:
                jobs = definition[key]
                if 'periodics' in jobs:
                    logger.debug('\tChecking: %s', key)
                    for job in jobs['periodics']:
                        if job['name'] == name:
                            logger.debug('\t\tFound')
                            found = True
                            break
            if found:
                break
        if not found:
            missing.append((source, verification, name))
    return missing


def main(git_repo_path):
    releases = read_release_definitions(os.path.join(git_repo_path, release_definition_path))
    job_data = get_job_data(releases)
    job_definitions = []
    for job_definitions_path in job_definitions_paths:
        job_definition = read_job_definitions(os.path.join(git_repo_path, job_definitions_path))
        job_definitions.append(job_definition)
    missing_jobs = validate_jobs(job_data, job_definitions)

    for source, verification, name in missing_jobs:
        logger.error('Unable to locate job definition for: %s:%s:%s', source, verification, name)

    sys.exit(len(missing_jobs))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Validate that the release verification/periodic jobs exist.')
    parser.add_argument('-r', '--release-repo-path', help='Path to the openshift/release git repo.', required=True)
    parser.add_argument('-v', '--verbose', help='Enable verbose output.', action='store_true')

    opts = parser.parse_args()

    if opts.verbose:
        logger.setLevel(logging.DEBUG)

    if not os.path.exists(opts.release_repo_path):
        logger.error('Release repository path does not exist: %s', opts.release_repo_path)
        sys.exit(-1)
    elif not os.path.exists(os.path.join(opts.release_repo_path, 'hack', 'validate-release-jobs.py')):
        logger.error('Invalid release repository specified: %s', opts.release_repo_path)
        sys.exit(-1)

    main(opts.release_repo_path)
