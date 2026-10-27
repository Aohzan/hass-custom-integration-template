# Home Assistant custom integration template

Template of a [Home Assistant](https://www.home-assistant.io/) custom integration distributed with [HACS](https://hacs.xyz/), with the development environment, tests and GitHub automation shared by the [Aohzan](https://github.com/Aohzan) integrations.

Minimum Home Assistant version: **2026.10.0**, Python **3.14**.

## Content

| Area | What |
|---|---|
| Integration | `custom_components/integration_blueprint`: config flow (user, reauthentication, reconfiguration), options flow reloading the entry, `DataUpdateCoordinator` subclass, `entry.runtime_data`, entities with translated names and icons, translated exceptions, diagnostics |
| Example device | A local HTTP API (`api.py`): in a real integration, this client lives in a library published on PyPI |
| Development | [uv](https://docs.astral.sh/uv/) with Home Assistant in the dev dependency group, [ruff](https://docs.astral.sh/ruff/), [prek](https://github.com/j178/prek) git hooks, VS Code launch and tasks |
| Tests | [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component): config flow, setup, entity snapshots, diagnostics, API client |
| CI | Reusable workflows of [Aohzan/.github](https://github.com/Aohzan/.github): ruff, translations, pytest, Home Assistant constraints, hassfest, HACS, then semantic-release on the default branch |
| Dependencies | Dependabot for uv and GitHub Actions, non-major updates merged automatically once the checks pass |

## Create an integration

1. "Use this template" on GitHub, clone the new repository.
2. Rename the integration, then lock the environment:

   ```sh
   python3 scripts/rename.py my_domain "My Integration" Owner/repository
   uv lock
   ```

3. Set up the environment: dependencies, git hooks and `config/`:

   ```sh
   scripts/setup
   ```

4. Replace the example: `api.py` by the library of your device (add it to `dependencies` in `pyproject.toml`, then `uv lock` and `python3 scripts/sync_requirements.py` to pin it in `manifest.json`), the entities, the translations and the tests.
5. Fill `hacs.json`, `manifest.json` (`codeowners`, `integration_type`, `iot_class`, `loggers`) and add the brand images.
6. Configure the GitHub repository (see below).

## Develop

| Command | Purpose |
|---|---|
| `scripts/setup` | `uv sync`, git hooks, Home Assistant configuration in `config/` |
| `scripts/develop` | Start Home Assistant on <http://localhost:8123> with the integration of the repository |
| `scripts/lint` | Format, lint and check the translations |
| `uv run pytest` | Tests, `--snapshot-update` to update the snapshots, `--cov` for the coverage |
| `python3 scripts/sync_requirements.py` | Pin the manifest requirements to `uv.lock`, `--check` to check them against the oldest supported Home Assistant |
| `python3 scripts/check_translations.py` | Check the translations, `--fix` copies `strings.json` to `translations/en.json` |

In VS Code, **F5** ("Home Assistant") starts Home Assistant under the debugger, breakpoints work in the integration. No container is needed: Home Assistant runs from `.venv` and finds the integration through `PYTHONPATH` (`custom_components` is a namespace package).

- The first start installs the requirements of `default_config` in `.venv`. `uv sync` removes them, the next start reinstalls them from the uv cache.
- The debugger doesn't follow subprocesses (`"subProcess": false`): Home Assistant installs packages with `python -m uv`, and debugging these processes breaks the installs.

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/): semantic-release computes the version from them (`fix` → patch, `feat` → minor, `!` or `BREAKING CHANGE` → major), writes `CHANGELOG.md`, the manifest version and the GitHub release with `release.zip`.
- `strings.json` is the source of the translations, in plain text: `translations/en.json` is a copy, the other languages have the same keys.
- Entities use `has_entity_name` with a `translation_key` or a device class, icons are in `icons.json`. Unique IDs never change; migrate them in `async_migrate_entry` when they must.
- No update listener: `OptionsFlowWithReload` reloads the entry. Home Assistant rejects an update listener together with the reloading methods of config flows from 2026.12.
- The shared abort reasons (`reauth_successful`, `reconfigure_successful`, `already_in_progress`, `single_instance_allowed`, OAuth ones) are translated by Home Assistant: don't add them to `strings.json`.
- Requirements: pin a library with `==` from `uv.lock`, except a library that Home Assistant core already pins: hassfest requires `>=` for it.
- Brand images go in `custom_components/<domain>/brand/` (`icon.png`, `icon@2x.png`, `logo.png`, `logo@2x.png`, `dark_*` variants): no pull request to home-assistant/brands is needed.
- `categories` in `manifest.json` will be added once hassfest supports it (Home Assistant 2026.11).

Follow the [developer blog](https://contributors.home-assistant.io/blog) for the deprecations of Home Assistant.

## GitHub repository settings

- **Allow auto-merge** and **Automatically delete head branches**.
- A ruleset on the default branch requiring the checks `ci / Lint`, `ci / Tests`, `ci / Home Assistant constraints`, `validate / Hassfest` and `validate / HACS`, with the repository admin role as bypass actor. Without required checks, Dependabot updates would be merged before the CI.
- `RELEASE_TOKEN`: a fine-grained personal access token (contents and pull requests read/write) stored as an Actions **and** a Dependabot secret. It lets the release push through the ruleset, and the merge of a Dependabot update trigger the release. Without it the workflows use `GITHUB_TOKEN`.
