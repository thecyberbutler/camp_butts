#!/usr/bin/env bash
# Read-only target inspection. Do not print environment variables, logs or credentials.
set -euo pipefail
printf '%s\n' '== Host metadata =='
uname -s
uname -m
awk '/^(ID|VERSION_ID)=/' /etc/os-release
id -u
printf '%s\n' '== Noninteractive administrative access =='
sudo -n true
printf '%s\n' '== Disk and memory capacity =='
df -Pk /
awk '/^(MemTotal|MemAvailable):/' /proc/meminfo
printf '%s\n' '== Deployment path and identity conflicts =='
if sudo -n test -e /opt/camp-butts-test; then
  printf '%s\n' 'STOP: /opt/camp-butts-test already exists; review before any write.'
  exit 1
fi
if getent passwd 10001 >/dev/null; then
  printf '%s\n' 'UID 10001 is already assigned; review its intended use.'
fi
if getent group 10001 >/dev/null; then
  printf '%s\n' 'GID 10001 is already assigned; review its intended use.'
fi
printf '%s\n' '== Existing listeners on intended public ports =='
sudo -n ss -ltn '( sport = :80 or sport = :443 )'
printf '%s\n' '== Docker availability =='
if command -v docker >/dev/null; then
  sudo -n docker version --format '{{.Client.Version}} {{.Server.Version}}'
  sudo -n docker compose version
  printf '%s\n' '== Existing campground test resources =='
  sudo -n docker ps -a --filter label=com.docker.compose.project=camp-butts-test --format '{{.Names}} {{.Status}}'
  sudo -n docker volume ls --filter label=com.docker.compose.project=camp-butts-test --format '{{.Name}}'
  printf '%s\n' '== Existing Docker network subnets =='
  while IFS= read -r network; do
    sudo -n docker network inspect --format '{{range .IPAM.Config}}{{println .Subnet}}{{end}}' "$network"
  done < <(sudo -n docker network ls -q)
else
  printf '%s\n' 'Docker is not installed; a reviewed OS-specific installation transcript is required.'
fi
printf '%s\n' 'Read-only preflight complete. No deployment changes were made.'
