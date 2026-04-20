#!/bin/bash
set -e

# Use absolute paths for port forwarding to avoid python path collisions
KUBECTL="/usr/local/bin/kubectl"
if [ ! -f "$KUBECTL" ]; then
    KUBECTL="kubectl"
fi

echo "🔌 Starting K3s Port Forwards for E2E Tests..."

# We background these port-forwards so they stay active while the test runs
$KUBECTL port-forward svc/eir-gateway 9090:3000 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/forseti 5555:5555 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/fenrir 8200:8200 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/hermodr 8090:8090 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/bifrost 8100:8100 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/vardr 9090:9090 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/huginn 8400:8400 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/muninn 8500:8500 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/ratatoskr 9200:9200 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/mjolnir 8700:8700 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/odin 8800:8800 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/heimdall 8080:8080 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/yggdrasil 8085:8085 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

$KUBECTL port-forward svc/wazuh 55000:55000 -n asgard > /dev/null 2>&1 &
PF_PIDS+=($!)

# Wait a few seconds for tunnels to establish
sleep 3
echo "✅ Tunnels established."

# Clean up function to kill port forwards on exit
cleanup() {
    echo "🧹 Closing port forwards..."
    for pid in "${PF_PIDS[@]}"; do
        kill $pid 2>/dev/null || true
    done
}
trap cleanup EXIT

echo "⚖️ Running Forseti E2E Tests..."
python3 run_e2e.py "$@"
