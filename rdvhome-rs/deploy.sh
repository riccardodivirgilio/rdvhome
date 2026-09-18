#!/usr/bin/env bash
#
# Build the raspberry binary on the mac and push it there.
#
# No cross toolchain to install: Docker on Apple Silicon is linux/arm64, and the
# pi is aarch64 too (Debian 13, 6.12 rpi-v8), so the Dockerfile compose already
# uses *is* the build for the pi — static musl binary, frontend inside, real
# pins (rppal) compiled in. `-o type=local` just takes the binary out of the
# scratch image instead of running it.
#
#   ./deploy.sh              build, copy the binary and the unit, start nothing
#   ./deploy.sh --switch     also stop the python service and start this one (the real lights)
#   ./deploy.sh --rollback   stop this one, start the python service again
#
# Both apps read the same ~/.rdvhome, accessory.state included, so **nobody has to
# pair again**, in either direction. The rust app rewrites that file once to add
# `pincode` / `setup_id` (hap-python forgets its setup code at every start, we do
# not); everything hap-python reads — mac, keys, paired_clients, client_properties,
# accessories_hash — stays byte for byte the same, and hap-python ignores the two
# extra keys, so a rollback finds the pairing it left. Verified on the pi by
# diffing the file the rust app wrote against the one the python app wrote.
#
# Every run still copies the file aside first, here and on the pi. To put one back:
#   scp ~/.rdvhome-backups/<stamp>/accessory.state pi@rdvhome.local:.rdvhome/

set -euo pipefail

HOST=${RDV_HOST:-pi@rdvhome.local}
REMOTE=${RDV_REMOTE:-/home/pi/rdvhome-rs}
DATA=${RDV_REMOTE_DATA:-/home/pi/.rdvhome}
UNIT=rdvhome-rs.service
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

unit() {
    cat <<EOF
[Unit]
Description=Light 1 (rust)
After=network.target

[Service]
ExecStart=$REMOTE/rdvhome run
WorkingDirectory=$REMOTE
Environment=RDV_DATA_DIR=$DATA
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF
}

case "${1:-}" in
--rollback)
    echo "==> back to the python app"
    ssh "$HOST" "sudo systemctl disable --now $UNIT; sudo systemctl enable --now lights.service; systemctl is-active lights.service"
    exit 0
    ;;
--switch | "") ;;
*)
    echo "usage: $(basename "$0") [--switch | --rollback]" >&2
    exit 2
    ;;
esac

echo "==> build (linux/arm64)"
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
docker buildx build --platform linux/arm64 \
    --build-context frontend="$HERE/../rdvhome/frontend/dist" \
    -o "type=local,dest=$out" "$HERE"
file "$out/rdvhome" | grep -q aarch64 || { echo "not an aarch64 binary" >&2; exit 1; }

# The HomeKit pairing lives in $DATA/accessory.state and re-pairing ~25 accessories
# is a day of work: keep a copy on the pi and one here before anything happens.
stamp=$(date +%Y%m%d-%H%M%S)
backups=${RDV_BACKUPS:-$HOME/.rdvhome-backups}
echo "==> backup of the pairing -> $backups/$stamp"
mkdir -p "$backups/$stamp"
ssh "$HOST" "cp -a $DATA $DATA.backup-$stamp"
scp -q "$HOST:$DATA/accessory.state" "$backups/$stamp/accessory.state"

echo "==> copy to $HOST:$REMOTE"
ssh "$HOST" "mkdir -p $REMOTE"
# aside and renamed: overwriting the file of a running process is ETXTBSY
scp -q "$out/rdvhome" "$HOST:$REMOTE/rdvhome.new"
unit | ssh "$HOST" "cat > /tmp/$UNIT"
ssh "$HOST" "mv $REMOTE/rdvhome.new $REMOTE/rdvhome && sudo cp /tmp/$UNIT /etc/systemd/system/$UNIT && sudo systemctl daemon-reload && $REMOTE/rdvhome --help > /dev/null"

if [ "${1:-}" != "--switch" ]; then
    echo "==> done, nothing started. The python app is still the one running."
    echo "    ssh $HOST '$REMOTE/rdvhome pair'      # reads the same pairing
    ./deploy.sh --switch                     # hand the house over"
    exit 0
fi

echo "==> switching: python off, rust on"
# one at a time: they share the pins, port 8500, 51826 and the mdns name
# restart, not `enable --now`: on a re-deploy the unit is already up and would keep the old binary
ssh "$HOST" "sudo systemctl disable --now lights.service; sudo systemctl enable $UNIT; sudo systemctl restart $UNIT; sleep 3; systemctl is-active $UNIT"

# The one failure that looks healthy: no /dev/gpiomem, so it falls back to the
# file pins and the house stops answering the switches while the service is green.
# scoped to this invocation, not the last N lines: booting prints one line per pin
if ! ssh "$HOST" "journalctl -u $UNIT _SYSTEMD_INVOCATION_ID=\$(systemctl show -p InvocationID --value $UNIT) --no-pager | grep -q 'using the raspberry pins'"; then
    echo "!!! the pins are simulated, rolling back to the python app" >&2
    ssh "$HOST" "sudo systemctl disable --now $UNIT; sudo systemctl enable --now lights.service"
    exit 1
fi

# from the pi: this mac cannot reach port 8500 on that network
ssh "$HOST" "curl -fsS --max-time 10 http://127.0.0.1:8500/switch >/dev/null" && echo "==> answering on :8500, real pins"
