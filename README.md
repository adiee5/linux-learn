# Linux-Lingo

This is a webapp which main purpose is to be a quiz about Linux commands.

## Set it up

1. Download the repo on your computer:
```sh
git clone https://github.com/adiee5/linux-lingo
```

2. Create a venv and install dependencies:
```sh
python -m venv .venv
./.venv/Scripts/activate
pip install -r requirements.txt
```

3. Create a `server.ini` configuration file. See [`server.example.ini`](/server.example.ini) for the information on how the configuration is done.

4. Optionally, you can import data from the *[dumps](/dumps/)* folder to your MongoDB DataBase in order to already have some kind of content in your instance.

## Usage
```sh
python theserver.py
```
Make sure you're in the correct venv before running the command.

## Administrating

1. Go to `/admin` page of your instance
2. Log in
3. Now you have an access to the admin panel. The GUI should be self explanatory (if it isn't, feel free to [complain about it](https://github.com/adiee5/linux-lingo/issues/new)).