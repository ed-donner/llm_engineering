# Part 2C - Alternative to Anaconda or bare pip+venv

This alternative makes use of [Pipenv](https://pipenv.pypa.io/en/latest/).

> *Pipenv is a Python virtualenv management tool that combines pip, virtualenv,
> and Pipfile into a single unified interface. It creates and manages virtual
> environments for your projects automatically, while also maintaining a Pipfile
> for package requirements and a Pipfile.lock for deterministic builds.*

**In summary:**\
It combines venv and pip on one single tool while also providing environment
and dependencies definition and lock control on a file, providing a similar feature to
Anaconda ensuring all collaborators runs exactly the same environment, dependencies and
versions.

This procedure asumes Python is already installed on the system.
In cas it's not refer to your systems instructions:

* [SETUP-PC.md](SETUP-PC.md)
* [SETUP-mac.md](SETUP-mac.md)
* [SETUP-linux.md](SETUP-linux.md)

Once Python is installed and ready follow the next steps:

1. Open a new terminal:

   *It may vary depending on your system.*

2. Install `pipenv` tool:

   ```Python
   python -m pip install pipenv
   ```

3. Check installation:

   ```Shell
   pipenv --version
   ```

4. Navigate to the *project's root directory*

   *It may vary depending on your system.*

5. Create the virtual environment and enter a shell inside.

   ```Shell
   pipenv shell
   ```

6. Install dependencies

   ```Shell
   pipenv install --dev1
   ```

   This may take a while.

> [!NOTE]
>
> On windows, if you see any "compiling" or "building" errors, you'll need to
> install the *Microsoft C++ Build Tools* from:
>
> * <https://visualstudio.microsoft.com/visual-cpp-build-tools/>
>
> And follow this instructions:
> <https://github.com/chroma-core/chroma/issues/189#issuecomment-1454418844>
>
> * Navigate to *"Individual components"*, find and select these two:
>   * `MSVC v143 -VS 2022 C++ x64/x86 build tools (Latest)`
>   * `Windows 11 SDK (10.0.22621.0)`\
>     *It doesn't matter you are on Win10 if the case,
>     choose the higher version available.*
> * And "Install" with the lower right button.
> * You may need to reboot your system.

In future to enter the environment just navigate to the *project's root folder* and run:

```Shell
pipenv shell
```

You'll notice the environment prefix before your prompt, in this case it's the folders
name as `pipenv` sets it automatically:

You'll see `(llm_engineering)` assuming you din't renamed the folder while or after
cloning.

> [!NOTE]
>
> On windows the environment prefix may not show up in some cases.
>
> In that case just copy the profile file at:
>
> `fix-win-env-prefix\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`
>
> To your `<Users-Root-Folder>\Documents\WindowsPowerShell\` folder.
> (*Or update it with its contents if already exists.*)
