# Release Pipeline Template

This template is designed to automate the creation of weekly releases.
It is based on the TARDIS Collaboration release pipeline, with a number of
simplifications.

Publishes a new release every Sunday at 00:00 UTC using calendar versioning by default.

## Usage

1. Connect your repository on Zenodo, see <https://help.zenodo.org/docs/github/>.
1. Make sure you have a reserved DOI on Zenodo by making a manual
release. Consider adding specific information.
1. Replace the DOI of this repository in these files:
    <https://github.com/tardis-sn/release-pipeline-template/blob/eb7b95ab109ce601221ab745e5c3b670a296a5f3/.github/workflows/release.yml#L65>

    <https://github.com/tardis-sn/release-pipeline-template/blob/eb7b95ab109ce601221ab745e5c3b670a296a5f3/.github/workflows/post-release.yml#L56>

1. Test the pipeline by running it using the workflow dispatch trigger on the
pre-release workflow.

> Note:
    If your main branch is protected, take a look at the full TARDIS 
    release pipeline, which includes automated reviews with tokens.

## Pre-release

The pre-release action clones the current repository, runs the script to 
generate a new ``.zenodo.json`` file, and pushes it to the root of the repository.
This file is used to create a new version of your software on Zenodo with all committers as authors.

### Zenodo job

1. Check out the repository.
2. Store the secret key for the Zenodo API in an environment variable.
3. Run the script to generate a new ``.zenodo.json`` file.
4. Upload the ``.zenodo.json`` as an artifact.

### Push job

Relies on Zenodo step completing.

1. Check out the repository.
2. Download the artifact from the previous step.
3. Checks for ``.zenodo.json`` and uses it if it was generated.
4. Get the current date.
5. Push the updated ``.zenodo.json`` to the main branch.

## Release

Creates a new release on GitHub and Zenodo after the pre-release PR is merged.

1. Check out the repository with 0 fetch depth.
2. Set up Python.
3. Find the next calendar version based on today's date.
4. Create a GitHub release that uses the new version as the tag.
5. Wait for Zenodo to update the new release of TARDIS (2 min sleep).
6. Fetch the new DOI from Zenodo using the Zenodo API, and create a badge.
7. Update the release description with the Zenodo badge.

## Post-release

The post-release action updates the changelog, citation and credits in the main
repository.

### Changelog job

1. Check out the repository with 0 fetch depth.
2. Get the current release tag
3. Generate a changelog with ``git-cliff``
4. Upload a CHANGELOG.md file as an artifact.

### Citation job

1. Check out the repository.
2. Set up Python.
3. Install ``doi2cff``.
4. Convert the latest release DOI to a CITATION.cff file. Try 10 times with a 60 second sleep between attempts.
5. Upload the CITATION.cff file as an artifact.

### Pull Request job

1. Checks out the TARDIS repository.
2. Downloads the artifacts from the previous steps.
3. Copy the ``CHANGELOG.md``, ``CITATION.cff`` files to the repository.
4. Get the current date.
5. Push the changes to the main branch.
