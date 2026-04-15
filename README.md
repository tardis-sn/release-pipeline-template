# TARDIS Collaboration Release Pipeline Template

This template is designed to automate the creation of weekly releases.

Publishes a new release every Sunday at 00:00 UTC using calendar versioning by default.

## Pre-release

The pre-release action clones the ``tardis-sn/tardis_zenodo`` repository, runs the notebook to 
generate a new ``.zenodo.json`` file, and pushes it to the root of the tardis repository. 
This file is used to create a new version of TARDIS on Zenodo with all committers as authors.
A pull request is created and automatically merged if all required checks pass.

### Zenodo job

1. Checkout the ``tardis-sn/tardis_zenodo`` repository.
2. Wait for the Zenodo webhook to be available (3 min sleep).
3. Set up the Python environment stored in ``tardis-sn/tardis_zenodo``.
4. Store the secret key for the Zenodo API in an environment variable.
5. Run the notebook to generate a new ``.zenodo.json`` file. Re-run if there are 
errors and ignore any errors.
6. Upload the ``.zenodo.json`` as an artifact.

### pip tests job

Runs the TARDIS test suite using pip to install TARDIS.

### Pull Request job

Relies on Zenodo and pip test steps completing.

1. Checks out the TARDIS repository.
2. Downloads the artifacts from the previous steps.
3. Checks for ``.zenodo.json`` and uses it if it was generated.
4. Get the current date.
5. Create a bot pull request on the tardis-bot fork using a branch named ``pre-release-<date>`` with the new ``.zenodo.json`` file.
6. Wait for the PR to be created (1 min sleep).
7. Automatically approve the PR using tokens from the infrastructure and core coordinator members.
8. Enable auto-merge.

## Release

Creates a new release on GitHub after the pre-release PR is merged. 

1. Check out the TARDIS repository with 0 fetch depth.
2. Set up Python.
3. Install ``setuptools_scm`` and ``git-cliff``.
4. Get the current TARDIS version using ``setuptools_scm`` via a helper script.
5. Get the next TARDIS version using ``setuptools_scm``.
6. Create a GitHub release that uses the new version as the tag.
7. Wait for Zenodo to update the new release of TARDIS (2 min sleep).
8. Fetch the new DOI from Zenodo using the Zenodo API, and create a badge.
9. Generate the changelog using ``git-cliff``.
10. Update the release description with the changelog and the Zenodo badge. 
Include the environment lock files in the release assets.

## Post-release

The post-release action updates the changelog, citation and credits in the main
repository.

### Changelog job

1. Check out the TARDIS repository with 0 fetch depth.
2. Get the current release tag
3. Generate a changelog with ``git-cliff``
4. Upload a CHANGELOG.md file as an artifact.

### Citation job

1. Check out the TARDIS repository.
2. Wait for the Zenodo webhook to be available (3 min sleep).
3. Set up Python.
4. Install ``doi2cff``.
5. Convert the latest TARDIS release DOI to a CITATION.cff file. Try 10 times with a 60 second sleep between attempts.
6. Upload the CITATION.cff file as an artifact.

### Credits job

1. Check out the TARDIS repository.
2. Wait for the Zenodo webhook to be available (3 min sleep).
3. Set up Python.
4. Install ``requests``.
5. Run a helper script to update ``README.rst`` and ``docs/resources/credits.rst``.
6. Upload README.rst and credits.rst as artifacts.
7. Dispatch the updates to the TARDIS website.

### Pull Request job

1. Checks out the TARDIS repository.
2. Downloads the artifacts from the previous steps.
3. Copy the ``CHANGELOG.md``, ``CITATION.cff``, ``README.rst`` and ``credits.rst`` files to the repository.
4. Get the current date.
5. Create a pull request.
6. Wait for the PR to be created (30 second sleep).
7. Automatically approve the PR using tokens from the infrastructure and core coordinator members.
8. Enable auto-merge.
