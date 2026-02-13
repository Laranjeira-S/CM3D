# CM3D
Database for Nerve Guide Conduit experiments
cm3d
## Prerequisites

* [Miniconda](https://docs.conda.io/en/latest/miniconda.html)

## Installation

### Overview:

```shell
cd CM3D
conda env create -f environment.yml
conda activate cm3d
pytest
mkdir workdir
cd workdir
cm3d-cli init
cm3d-cli add-user USERNAME PASSWORD
cm3d-cli web
```

1. The `environment.yml` file lists the Python package dependencies. From a terminal in repository folder run: `conda env create -f environment.yml` to create a virtual environment called `cm3d` with the correct packages.
   * Windows: Use Anaconda Prompt in Start Menu
3. Type `conda activate cm3d` to activate the environment.
4. Run `pytest` and check all tests pass.
5. Run `cm3d-cli` to see help for the cm3d command-line tool.

## Usage

### Setting up the working directory

You only need to do this the first time you install cm3d.

1. Create a new, empty, directory that will be the working directory for cm3d. This is _not_ the same as the repository folder, the working directory is where you will store your spreadsheet and files you download from the database.
2. Open a terminal in the directory you created. On Windows you can use the Anaconda Prompt that is installed with Miniconda.
3. Run `cm3d-cli init` to create the necessary files and folders need to run the program.

### Add users

1. Open a terminal in the working directory you created.
2. Run `cm3d-cli user USERNAME PASSWORD`, replacing USERNAME and PASSWORD with suitable values.
3. The program will generate and display the credential.
4. Alternatively you can add the credential to the `users.json` file (remember to put a comma between users).
5. Add additional users as required (you can add users at any time following the same procedure)

### Running the web server

1. Open a terminal in the working directory.
2. Run `cm3d-cli web` to start the webserver.
3. Navigate to the website using the link given in the terminal and enter your credentials when prompted.

## cm3d-cli

`cm3d-cli <command>` is the command-line interface for cm3d. Available commands:

* `init` sets up a work directory for the cm3d, holding database, template files, and directories for downloads/uploads
* `add-user` creates a new user
* `web` starts the NGC DB webserver. Adding `--debug` runs the development version
* `create-db` creates a new database to store studies
* `export-db` downloads the full database as a CSV file and saves it in your working directory
* `query-db` prints records from database applying the given filter
* `backup-db` creates and saves a backup file
* `add-study` loads a Excel file into the database
* `mock-study` creates a fake Excel file following the correct ttemplate structure, for testing.

Use `cm3d-cli <command> --help` for more information on parameters for each command.

