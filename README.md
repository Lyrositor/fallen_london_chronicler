Fallen London Chronicler
========================

*A tool for recording and exporting Fallen London content.*

The **Fallen London Chronicler** is a software tool for recording local sessions of Fallen London for archival and documentation purposes, notably including contributing to the wiki.

**License:** [Creative Commons 0](https://creativecommons.org/share-your-work/public-domain/cc0/)

![Screenshot](https://user-images.githubusercontent.com/1495312/107299258-394e0900-6a77-11eb-92f1-d66ddc6e6e6c.png)

## Usage

The Fallen London Chronicler works by passively monitoring a local, ongoing Fallen London session. It does so through two components:

- **A local server** process which renders a web view of what has been recorded so far and listens for Fallen London events from the userscript
- **A browser userscript** which listens for Fallen London events (e.g. entering a new area, choosing a storylet branch...) and relays them to the server process

The tool **does not** require your Fallen London credentials, not does it log any personal information (username, email, password...). It only records game data.

### Setup

#### Windows

A pre-packaged binary is available for Windows to make it easier to set up. Just follow the below instructions:

1. Download the Windows build of the [latest release](https://github.com/Lyrositor/fallen_london_chronicler/releases).
2. Extract it somewhere on your computer.
3. *(Optional)* Configure your setup, as detailed in the Configuration section below.
4. Run the `fallen_london_chronicler.exe` program.
5. Your browser should open to `http://localhost:7777` by default; if it doesn't, go there now.
6. Follow the setup instructions on the home page there.
7. You're good to go!

#### Other Operating Systems

While only Windows is officially supported, the Fallen London Chronicler should run fine on other operating systems. The steps to get it running are a bit more complicated, however:

1. Download and install [Python 3.8](https://www.python.org/) (or higher).
2. Download the source of the [latest release](https://github.com/Lyrositor/fallen_london_chronicler/releases).
3. Extract it somewhere on your computer.
4. Set up the virtual environment for the Fallen London Chronicler:
   - Windows: in a PowerShell console, enter:
```
(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -
poetry install
# Follow the instructions Poetry outputs to activate your virtual environment
```
    
   - macOS/Linux/etc.: in a terminal, enter:
```shell
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
poetry install
# Follow the instructions Poetry outputs to activate your virtual environment
```
5. *(Optional)* Configure your setup, as detailed in the Configuration section below.
6. Run the following command from the root of the repository:
```shell
PYTHONPATH=.:${PYTHONPATH} python fallen_london_chronicler/__main__.py
```
7. Your browser should open to `http://localhost:7777` by default; if it doesn't, go there now.
8. Follow the setup instructions on the home page there.
9. You're good to go!

### Configuration

Fallen London Chronicler comes with a `config.default.env` which can be used to set various configuration settings. Rename it to `config.env` and edit the values within to adjust various settings (the file is commented to let you know what each value does).

#### Setting up HTML Export

In order to export your recording to a static collection of HTML files, configure the variables in your config under the `HTML Export` section.

#### Setting Up Google Docs Export

In order to export your recording to a Google Docs document, configure the variables in your config under the `Google Docs Export` section.

You'll need to acquire a `credentials.json` file to authenticate with the Google Docs API. This is currently still a rather involved process:

1. Go to the [Google Docs API documentation](https://developers.google.com/docs/api/quickstart/python).
2. Click on the "Enable the Google Docs API" button and follow the listed steps. Download the client configuration file at the end, then click on the "API Console link".
3. Click on "Enable APIs and Services" at the top, search for "Google Drive" and enable it.
4. Copy the file you downloaded to the root of your Fallen London Chronicler installation.
5. You're good to go! When you export to Google Docs for the first time, you'll be prompted to authorize the application; you won't need to do this every time.

Future versions of this project will hopefully simplify this process.

### Known Bugs and Missing Features

The following are known issues with the current version of the Chronicler:

- Outcomes which lead to other outcomes (e.g. when setting out to Zee from Wolfstack Docks) are not currently supported
- Quality changes which don't actually change the quality level (either because the quantity is already 0, in case of a decrease, or the quality cap, in case of an increase) aren't recorded properly
- Opportunity cards are not supported - the storylets themselves are recorded, but they are not linked back to the area
- Quality requirements are not listed in Google Docs output
- Designated currency costs are not displayed currently (very few storylets actually use these types of quality requirements)

## Development

If you wish to further develop Fallen London Chronicler, you'll need to set up a local development environment, as detailed below. If you'd like to contribute back your changes, make a fork of this repository and submit a merge request.

### Setup

You'll need to follow the instructions in the setup for other operating systems to install the app in development mode. You'll also probably want an IDE like [PyCharm](https://www.jetbrains.com/pycharm/) to make it easier to develop.

It is recommended to run the app in debug mode (configurable in the `config.env` file) to enable auto-reload.
