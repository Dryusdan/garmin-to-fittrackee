# garmin-to-fittrackee

A simple script to synchronize garmin to fittrackee. Inspired by https://github.com/jat255/strava-to-fittrackee

![Dynamic JSON Badge](https://shields.dryusdan.net/badge/dynamic/json?url=https%3A%2F%2Fgit.dryusdan.fr%2FDryusdan%2Fgarmin-to-fittrackee%2Fraw%2Fbranch%2Fmain%2Fcoverage.json&query=%24.totals.percent_covered_display&suffix=%25&style=flat&label=Coverage&color=light-green)

## How to install it

This script is a CLI to interact download activity with GPX on Garmin and push it into Fittrackee.

This program use `garminconnect` package to interact with Garmin and `Typer` to provide a CLI. Also, it use sqlite3 to keep whitch Garmin activity match Fittrackee workout with the aim of modifying Fittrackee sessions if new features appear.

This program is developed around Fittrackee v0.7.29 and work with it. It work on Python 3.12, 3.11 and 3.10 (minimal version required) but actively developped on Python 3.11. It's only run on Linux. Other OS isn't tested.

### To install it

With pipy, use git.dryusdan.fr repository.
```bash
pip install --upgrade --index-url https://git.dryusdan.fr/api/packages/Dryusdan/pypi/simple/ --extra-index-url https://pypi.python.org/simple garmin-to-fittrackee
```

With source code

```bash
pip3 install poetry
git clone https://git.dryusdan.fr/Dryusdan/garmin-to-fittrackee.git
cd garmin-to-fittrackee
poetry install
```

## How to use it

### Setting you're fittrackee instance Oauth2 application

You need to setting an application in your Fittrackee instance.

Go to you're fittrackee account, then go to "apps", then "Add an application".


In the "Add a new OAuth2 application" section; chose your `Application name`.

To `application URL` and `Redirect URL` set this URL `https://localhost` (usefull for configuration, later in this README)/

In Scope, check `profile:read`, `workouts:read`, `workouts:write`.

After submit your application, an application ID and secret is displayed. These informatiuon is usefull for setting the CLI, note theses.
And that all for Fittrackee.


The first time, you need to run 3 commands :

```bash
garmin2fittrackee setup config-tool #
```
This command set the configuration, default log level ("INFO"), default path to database.
Use `--help` to view which parameters you can change

The seconds command login to Garmin. The client ask you're Garmin's credential :

```bash
garmin2fittrackee setup garmin
```
You can save this credentials with `--store`. You can set this parameters in cli argument. See `--help`.

The third command is used to setup fittrackee connection.
```bash
garmin2fittrackee setup fittrackee
```

The command ask your application ID, application secret, the domain of you're domain Fittrackee instance (without `https://`).

Then the CLI will guide you through authorising the application to Fittrackee.
