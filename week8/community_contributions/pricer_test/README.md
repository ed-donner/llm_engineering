# Run Continuous Integration (CI) Tests on Modal

Note!
The HF secret in Modal is named "huggingface-secret". Pls rename if your secret has another name.

## Test modal deployment
You can test pricer.ci in Modal:
(`modal deploy -m pricer.ci`)
In python CLI:
(`import modal`)
(`Pricer = modal.Cls.lookup("pricer-ci-testing", "Pricer")`)
(`pricer = Pricer()`)
(`reply = pricer.price.remote("Quadcast HyperX condenser mic, connects via usb-c to your computer for crystal clear audio")`)
(`print(reply)`)

## Unit testing
Unit test strategy created like in 
[This example repo](https://github.com/modal-labs/ci-on-modal)

## Usage

All commands below are run from the root of the repository (this directory).

### Run tests remotely on Modal

```bash
modal run pricer.ci
```

On the first execution, the [container image](https://modal.com/docs/guide/custom-container)
for your application will be built.

This image will be cached on Modal and only rebuilt if one of its dependencies,
like the `requirements.txt` file, changes.

### Debug tests running remotely

To debug the tests, you can open a shell
in the exact same environment that the tests are run in:

```bash
modal shell pricer.ci
```

_Note_: On the Modal worker, the `pytest` command is run from the home directory, `/root`,
which contains the `tests` folder, but the `modal shell` command will
drop you at the top of the filesystem, `/`.
