#!/usr/bin/env bash
set -euo pipefail

out="${RUNNER_RESOURCE_SNAPSHOT_PATH:-runner-resource-snapshot.json}"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cpu_count="$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || printf 'null')"
load_1m="null"
if [ -r /proc/loadavg ]; then
  load_1m="$(awk '{print $1}' /proc/loadavg)"
fi

mem_total="null"
mem_available="null"
if [ -r /proc/meminfo ]; then
  mem_total="$(awk '/^MemTotal:/ {print $2 * 1024}' /proc/meminfo)"
  mem_available="$(awk '/^MemAvailable:/ {print $2 * 1024}' /proc/meminfo)"
fi

disk_total="null"
disk_free="null"
if command -v df >/dev/null 2>&1; then
  disk_total="$(df -B1 . | awk 'NR==2 {print $2}')"
  disk_free="$(df -B1 . | awk 'NR==2 {print $4}')"
fi

cat > "$out" <<EOF
{
  "schema": "github-runner-resource-snapshot/v1",
  "observed_at": "$timestamp",
  "ephemeral_runner": true,
  "cpu": {"logical_processors": $cpu_count, "load_1m": $load_1m},
  "memory": {"total_bytes": $mem_total, "available_bytes": $mem_available},
  "filesystem": {"workspace_total_bytes": $disk_total, "workspace_free_bytes": $disk_free}
}
EOF

if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
  {
    echo "### Runner resource snapshot"
    echo
    echo "- observed: `$timestamp`"
    echo "- logical CPUs: `$cpu_count`"
    echo "- 1m load: `$load_1m`"
    echo "- memory total bytes: `$mem_total`"
    echo "- memory available bytes: `$mem_available`"
    echo "- workspace total bytes: `$disk_total`"
    echo "- workspace free bytes: `$disk_free`"
  } >> "$GITHUB_STEP_SUMMARY"
fi

echo "$out"
