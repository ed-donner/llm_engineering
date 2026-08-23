# Run Continuous Integration (CI) Tests on Modal

## Unit testing
Unit test strategy created like in 
[This example repo](https://github.com/modal-labs/ci-on-modal)

## Usage

All commands below are run from the root of the repository (this directory).
_Note_: I removed modal-decorators from pricer.ci-module to be able to run unit tests.

### Run tests remotely on Modal

```bash
modal run pricer.ci::pytest
```

On the first execution, the [container image](https://modal.com/docs/guide/custom-container)
for your application will be built.

This image will be cached on Modal and only rebuilt if one of its dependencies,
like the `requirements.txt` file, changes.

### Debug tests running remotely

To debug the tests, you can open a shell
in the exact same environment that the tests are run in:

```bash
modal shell pricer.ci::pytest
```

_Note_: On the Modal worker, the `pytest` command is run from the home directory, `/root`,
which contains the `tests` folder, but the `modal shell` command will
drop you at the top of the filesystem, `/`.

To run test:
```bash
cd root
pytest
```