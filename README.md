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
  - [Run with Docker](#run-with-docker)

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

Additionally the settings set via _settings_default.py_ or _settings_local.py_ can be overwritten by the command line:

* -b, --base-dir - The directory where the downloaded data is stored. An additional directory called _raw_data_ will be created in the selected directory.    
  ```shell
  python -m vwkommi request -b /home/user/vwdata
  ```
* -w, --worker-count - The number of workers to be used to make requests (default: 30)    
  ```shell
  python -m vwkommi request -w 20
  ```
* -u, --username - The username of your account on the VW website    
  ```shell
  python -m vwkommi request -u example
  ```
* -p, --password - The password of you account on the VW website    
  ```shell
  python -m vwkommi request -p example
  ```
* -P, --prefix-list - The prefixes for commission numbers which are tried (default [185,900,877,902]).    
  ```shell
  python -m vwkommi request -P [123,444]
  ```    
  The default value is for ID.3, ID.4 and ID.5 vehicles. 
* -s, --skip-fin-details - Set to _True_ to request additional VIN details. It may be very slow (default: True).    
  ```shell
  python -m vwkommi request -s True
  ```
* -c, --commission-number-range - Sets the ranges to be requested. The value is a list containing lists with four elements. The inner lists elements consist of the character part of the commission number. The next two elements are the actual range. The last element contains the number of characters of the number part.    
  ```shell
  python -m vwkommi request -c '[[\"AF\",0,5000,4],[\"AH\",123,123,4]]'
  ```

## Run with Docker

Instead of installing local environment you can build a docker image and run vwkommi with docker. To build the docker image execute:
```shell
docker build -t vwkommi .
```

To run the image create a settings_local.py (here under /srv/vwkommi/settings_local.py) and execute the following command:
```shell
docker run --rm -v /srv/vwkommi/raw_data/:/work/vwkommi/raw_data -v /srv/vwkommi/settings_local.py:/work/vwkommi/settings_local.py vwkommi:latest request
```

You will find then the .json files in the directory /srv/vwkommi/raw_data/.
