# VW Kommi

VW Kommi is a simple tool to read out commission numbers of VW ID vehicles.

## Outline

- [VW Kommi](#vw-kommi)
  - [Outline](#outline)
  - [Install Requirements](#install-requirements)
    - [Linux](#linux)
    - [Windows](#windows)
  - [Create virtual environment (optional)](#create-virtual-environment-optional)
  - [Install VW Kommi](#install-vw-kommi)
  - [Settings](#settings)
  - [Usage](#usage)

## Install Requirements

The following requirements are needed to run VW Kommi:

* Python 3.8 (or newer)
* pip
* virtualenv (optional)

### Linux

The following steps are based on Ubuntu 18.04. Other distributions may work in a similar way.

First install the needed packages.

```
sudo apt install python3.8 python3.8-venv
```

Then install *virtualenv*.

```
python3.8 -m pip install virtualenv
```

The command will install the *virtualenv* binary to *~/.local/bin*. So add your local *bin*
directories to your *PATH* system environment variable. Therefore open *~/.bashrc* and add the
following line to the end if it is not already there:

```sh
PATH=$PATH:~/.local/bin:~/.local/sbin
```

### Windows

Download Python 3 from the [Python Download Website](https://www.python.org/downloads/windows/).
Following the setup you should bbe able to also install *pip*. Be sure to add the *Python-Path* and
*Scripts* to your Path to make the commands available.

After installing Python install *virtualenv*.

```
pip install virtualenv
```

## Create virtual environment (optional)

Using *virtualenv* is not needed but keeps the system installation of Python clean. So I recommend
using it!

Create a virtual environment and *cd* to it.

```
python -m venv vwkommi
cd vwkommi
```

__Attention:__ Depending on the system *python3.8* needs to be used as command.

Activate the virtual environment.

```
. bin/activate
```

__Attention Windows users:__ The above command is different using windows:

```
Scripts\activate
```

If the above command worked you can see that the environment is active by _(vwkommi)_ in front
of the command line.

## Install VW Kommi

Clone the project. If you are using *virtualenv* change to its directory and activate it first (see
section [Create virtual environment](#create-virtual-environment-optional))!

```
git clone https://github.com/SushiTee/vwkommi.git
```

The last thing to do is installing the package. Therefor go into the checked out project directory
and install the package using _pip_.

```
cd vwkommi
pip install -e .
```

The parameter *-e* stands for *editable*. This means all local changes to the project or updates
will be applied without needing to reinstall the package.

## Settings

In the subdirectory _vwkommi_ a _settings_local.py.example_ can be found. It is to set
local settings for your installation. copy the file like so:

```shell
cp settings_local.py.example settings_local.py
```

All settings made there override the default settings set in _settings_default.py_.

**Make sure you enter your user data within the _settings_local.py_.**

The range of the commission numbers to be requested can be set as well.

## Usage

As VW Kommi is a python module it is run using the _-m_ parameter of the _python_ command:

```shell
python -m vwkommi <subcommand>
```

The following subcommands are available:

* request - Requests data from VW and stores them into the _raw_data_ directory

Within the _settings_local.py_ you can set the range commission numbers to be requested.

**request sub command**

The _request_ sub command supports two additional options:

* -f, --find-prefix - Find the prefix and year of a commission number    
  ```shell
  python -m vwkommi request -f AL1234
  ```
* -a, --add-to-profile - Tries to add a car with a given commission to your profile    
  ```shell
  python -m vwkommi request -a AL1234
  ```
