# venvconfig
__venvconfig__ is a small Python package to aid managing virtual environments for development.

## Prerequisites
Python 3.4+

This package uses the built in library __venv__ to help manage virtual environments, which was introduced in Python 3.4.  It also makes extensive use of __pathlib__, also introduced in Python 3.4.

## Background
I found that when experimenting with various Python libraries available through pip, I didn't want to install these into my main Python installation.  Of course this meant using virtual environments, but this lead to another problem.  At least on Windows, it's cumbersome managing virtual environments, especially remembering to activate them before you want to test one of your scripts.  So, after a couple iterations, I came up with this package to help me streamline the process.

## Usage
There are a couple ways you can use this package.  The simplest is a fully automated method, and varying levels of finer control over the startup process of your script.

### Fully-automatic
For the fully automated method, first create a file named __venv.cfg__ in the same directory as your script file.  The format of this file is similar to the INI file format, here is an example of one:
```
[venv]
path=.venv
name=TestVenv

[pip]
pyqt5 = 5.9
```
This config file specifies that the virtual environment should be stored in the `.venv` sub-directory, be named `TestVenV`, and should have PyQt5 (version 5.9) installed in it using pip.

Next, in your script file, as close to the top as possible, just use:
`from venvconfig import autoconfig`
And the rest will be taken care of automatically.  If the package detects that the specified virtual environment is not active, it will attempt to create and/or activate it as necessary.  If the listed pip dependencies are not found, it will also install those into the virtual environment using pip.

### Semi-automatic
The semi-automated method involves possibly creating one or more `.cfg` files, loading them with the `Config` class, and then fine tuning the startup process using the `Launcher` class.  For more details, check out the docstrings in those classes.

## History
__0.1 (2017/07/09)__ - Initial release
