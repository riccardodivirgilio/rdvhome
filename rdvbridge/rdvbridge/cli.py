import os
import subprocess
import base64
from pathlib import Path

import click

PI_USER = "pi"
PI_HOST = "rdvhome.local"
PI = f"{PI_USER}@{PI_HOST}"
HA_USER = "pi"
HA_DIR = f"/home/{HA_USER}/.homeassistant"
TMP = "/tmp/rdvbridge-deploy"

HERE = Path(__file__).parent.parent  # rdvbridge/
HA_CONFIG = HERE / "ha_config"

SYSTEMD_SERVICE = """\
[Unit]
Description=Home Assistant
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
ExecStart=/home/{user}/.ha-venv/bin/hass -c {ha_dir}
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
"""


def ssh(cmd, capture=False):
    full = ["ssh", PI, cmd]
    if capture:
        return subprocess.check_output(full, text=True).strip()
    subprocess.run(full, check=True)


def b64(text):
    return base64.b64encode(text.encode()).decode()


@click.group()
def main():
    """rdvbridge — Home Assistant setup and deploy tool."""
    pass


@main.command()
def setup():
    """Full Pi setup: venv, HA install, systemd service."""

    click.echo("==> Creating virtualenv...")
    ssh("python3 -m venv /home/pi/.ha-venv")

    click.echo("==> Syncing project dependencies...")
    subprocess.run([
        "rsync", "-av", str(HERE / "pyproject.toml"), f"{PI}:/home/pi/.ha-setup/"
    ], check=True)

    click.echo("==> Installing dependencies (this takes a few minutes)...")
    ssh(
        "/home/pi/.ha-venv/bin/pip install /home/pi/.ha-setup/ "
        "--extra-index-url https://www.piwheels.org/simple "
        "--quiet"
    )

    click.echo("==> Writing systemd service...")
    service = SYSTEMD_SERVICE.format(user=HA_USER, ha_dir=HA_DIR)
    encoded = b64(service)
    ssh(f"echo {encoded} | base64 --decode | sudo tee /etc/systemd/system/home-assistant@homeassistant.service > /dev/null")
    ssh("sudo systemctl daemon-reload")
    ssh("sudo systemctl enable home-assistant@homeassistant")

    click.echo("==> Deploying config...")
    _deploy()

    click.echo("==> Starting Home Assistant...")
    ssh("sudo systemctl start home-assistant@homeassistant")

    click.echo("\nDone. HA will be at http://rdvhome.local:8123 in ~60 seconds.")


@main.command()
def deploy():
    """Push ha_config + custom_components to Pi and restart HA."""
    _deploy()
    ssh("sudo systemctl restart home-assistant@homeassistant")
    click.echo("Deployed and restarted.")


def _deploy():
    ssh(f"mkdir -p {TMP}")
    subprocess.run([
        "rsync", "-av", "--delete",
        "--exclude-from", str(HERE / ".deployignore"),
        str(HA_CONFIG) + "/",
        f"{PI}:{TMP}/"
    ], check=True)
    subprocess.run([
        "rsync", "-av",
        str(HERE / ".deployignore"),
        f"{PI}:{TMP}/.deployignore"
    ], check=True)
    ssh(f"rsync -a --delete --exclude-from={TMP}/.deployignore {TMP}/ {HA_DIR}/")


@main.command()
def restart():
    """Restart Home Assistant on the Pi."""
    ssh("sudo systemctl restart home-assistant@homeassistant")
    click.echo("Restarted.")


@main.command()
def logs():
    """Tail Home Assistant logs on the Pi."""
    os.execlp("ssh", "ssh", PI, "sudo journalctl -u home-assistant@homeassistant -f")


@main.command()
def status():
    """Show Home Assistant service status on the Pi."""
    ssh("sudo systemctl status home-assistant@homeassistant --no-pager")


@main.command()
def local():
    """Run Home Assistant locally against ha_config."""
    os.chdir(HERE)
    os.execlp("uv", "uv", "run", "hass", "-c", str(HA_CONFIG))
