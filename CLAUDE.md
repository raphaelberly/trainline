# CLAUDE.md

Personal alert script: it watches Trainline results pages (thetrainline.com, French UI) for specific trains and sends a Pushover notification when a ticket becomes sellable.

## Layout

- `main_search.py`: the whole script, executed top to bottom (no `main()`, no CLI arguments).
- `lib/push.py`: thin Pushover wrapper. `lib/logger.py`: stdout logging setup.
- `conf/search.yaml`: the searches to watch (tracked).
- `conf/secrets.yaml`: credentials (gitignored).

## Running locally

Python env is a pyenv virtualenv named `trainline3.12.7`. Run from the repo root, since config paths are relative:

```bash
pip install -r requirements.txt
python main_search.py
```

Chrome must be installed. `webdriver_manager` downloads chromedriver unless `chromedriver` is set in the secrets.

`conf/secrets.yaml` format:

```yaml
push:
  user_key: ...
  api_token: ...
chromedriver: /usr/bin/chromedriver  # optional
```

There are no tests, linter or CI.

## Search config

`conf/search.yaml` is a list of searches:

- `url`: a Trainline results URL copied from the browser, with `lang=fr`. Route, date and passengers are encoded in it.
- `key`: label used in logs.
- `trains`: for each train to watch:
  - `time`: departure time `'HH:MM'`, asserted to appear in the text of the targeted result.
  - `target_result`: 1-indexed position among the non-flexible results on the page.
  - `only_second_class`: if true, no notification when only first class is available.

## Detection logic

The checks rely on Trainline's DOM and French wording, and break when Trainline changes its markup:

- Results rows: `//*[@aria-labelledby="urn:trainline:flex:nonflexi"]/div`
- Unsellable train: `data-test-unsellable="true"`
- Second class available: the row's accessible name contains `un billet de 2nde classe`
- Cookie banner: button with text `Continuer sans accepter`

Waits are fixed `time.sleep` calls. Any exception sends a "Broken trainline alerting" Pushover message, then is re-raised.

## Deployment (Raspberry Pi)

- Access: `ssh pi@journal.rberly.ovh -p 1337`. Repo at `/home/pi/trainline`, updated with `git pull`.
- The Pi copy has its own local edits to `conf/search.yaml` and an untracked `test.py`: check `git status` there before pulling.
- Python env: pyenv virtualenv `trainline3.11.6` (Python 3.11 on the Pi, 3.12 locally).
- Uses the system Chromium with `chromedriver: /usr/bin/chromedriver` in the secrets.
- Cron entry, under the `# TRAINLINE` block of the user crontab:
  ```
  */5 9-23 * * * cd /home/pi/trainline && /home/pi/.pyenv/versions/trainline3.11.6/bin/python /home/pi/trainline/main_search.py >> /home/pi/trainline/log/main_search.log 2>&1
  ```
- The crontab also runs other projects (accountin, journal, bricksbot, strava). Only touch the `TRAINLINE` block.

## Status

- In its current form, the bot gets blocked quickly by DataDome: after a few runs, Trainline serves a captcha (`geo.captcha-delivery.com` iframe) instead of the results, and the script fails, typically with an `ElementClickInterceptedException` on the cookie banner.
- Because of this, the cron on the Pi has been commented out since April 2025.
- In October 2026, a local run from a Mac got blocked on the first run: `/api/journey-search/` returns 403 with `x-datadome` headers and the page shows "Une erreur est survenue". In that case no result rows exist, and the script exits with no log and no alert.
