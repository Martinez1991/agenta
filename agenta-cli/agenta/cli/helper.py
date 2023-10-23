import sys
import toml
import click
import questionary
from pathlib import Path
from agenta.client import client
from typing import Any, List, MutableMapping
from agenta.client.api_models import AppVariant


def get_api_key():
    agenta_dir = Path.home() / ".agenta"
    credentials_file = agenta_dir / "credentials"

    if credentials_file.is_file():
        with credentials_file.open("r") as f:
            for line in f:
                key, value = line.strip().split("=")
                if key == "api_key":
                    return value
    else:
        api_key = questionary.text("(You can get your API Key here: https://demo.agenta.ai/settings?tab=apiKeys) Please provide your API key:").ask()
        if api_key:
            if not agenta_dir.is_dir():
                agenta_dir.mkdir(parents=True, exist_ok=True)
            with credentials_file.open("w") as f:
                f.write(f"api_key={api_key}")
            return api_key
        else:
            sys.exit(0)


def update_variants_from_backend(
    app_id: str, config: MutableMapping[str, Any], host: str, api_key: str = None
) -> MutableMapping[str, Any]:
    """Reads the list of variants from the backend and updates the config accordingly

    Arguments:
        app_id -- the app id
        config -- the config loaded using toml.load
        api_key -- the api key to use for authentication

    Returns:
        a new config object later to be saved using toml.dump(config, config_file.open('w'))
    """

    try:
        variants: List[AppVariant] = client.list_variants(app_id, host, api_key)
    except Exception as ex:
        raise ex

    config["variants"] = [variant.variant_name for variant in variants]
    config["variant_ids"] = [variant.variant_id for variant in variants]
    return config


def update_config_from_backend(config_file: Path, host: str):
    """Updates the config file with new information from the backend

    Arguments:
        config_file -- the path to the config file
    """
    assert config_file.exists(), "Config file does not exist!"
    config = toml.load(config_file)
    app_id = config["app_id"]
    api_key = config.get("api_key", None)
    if "variants" not in config:
        config["variants"] = []
    if "variant_ids" not in config:
        config["variant_ids"] = []
    config = update_variants_from_backend(app_id, config, host, api_key)
    toml.dump(config, config_file.open("w"))


def display_app_variant(variant: AppVariant):
    """Prints a variant nicely in the terminal"""
    click.echo(
        click.style("App Name: ", bold=True, fg="green")
        + click.style(variant.app_name, fg="green")
    )
    click.echo(
        click.style("Variant Name: ", bold=True, fg="blue")
        + click.style(variant.variant_name, fg="blue")
    )
    click.echo(click.style("Parameters: ", bold=True, fg="cyan"))
    if variant.parameters:
        for param, value in variant.parameters.items():
            click.echo(
                click.style(f"  {param}: ", fg="cyan")
                + click.style(str(value), fg="cyan")
            )
    else:
        click.echo(click.style("  Defaults from code", fg="cyan"))
    if variant.previous_variant_name:
        click.echo(
            click.style("Template Variant Name: ", bold=True, fg="magenta")
            + click.style(variant.previous_variant_name, fg="magenta")
        )
    else:
        click.echo(
            click.style("Template Variant Name: ", bold=True, fg="magenta")
            + click.style("None", fg="magenta")
        )
    click.echo(
        click.style("-" * 50, bold=True, fg="white")
    )  # a line for separating each variant
