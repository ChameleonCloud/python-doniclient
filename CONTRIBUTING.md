# Contributing 

## Testing

Run the tests using `tox -e py`


## Publishing new versions

Releases are published to PyPI by the [publish workflow](.github/workflows/publish.yml), using PyPI trusted publishing. The version comes from the git tag (via pbr), so there is no version to edit before releasing.

To release, create a GitHub release with a new tag named `vX.Y.Z`, and set its target to the branch you are releasing from. Publishing the release runs the tests, builds the package and uploads it to PyPI.

Use tags like `v1.1.0rc1` for pre-releases. GitHub's pre-release checkbox doesn't change the version uploaded to PyPI.
