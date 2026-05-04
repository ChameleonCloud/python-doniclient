# Contributing 

## Testing

Run the tests using `tox -e py39`


## Publishing new versions

Build the sdist + wheel and upload with `twine`. Packages are published under the `chameleoncloud` user account on PyPi.

```shell
python -m build
twine upload dist/*
```
