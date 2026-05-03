#!/usr/bin/env bash
#
# bootstrap_host.sh - end-to-end provision + configure for the Akamai GPU VM.
#
# Wraps two steps:
#   1. terraform apply against infra/terraform/akamai/, which creates the
#      Linode and emits inventory.ini next to it.
#   2. ansible-playbook against infra/ansible/playbook.yml using the rendered
#      inventory.
#
# Idempotent: re-running this against an existing VM only rolls forward
# changes (terraform plan -> apply, ansible converge).

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tf_dir="${repo_root}/infra/terraform/akamai"
ansible_dir="${repo_root}/infra/ansible"

if [[ -z "${LINODE_TOKEN:-}" ]]; then
    echo "ERROR: LINODE_TOKEN must be set in the environment." >&2
    exit 2
fi

echo "==> terraform init"
(cd "${tf_dir}" && terraform init -input=false -upgrade)

echo "==> terraform apply"
(cd "${tf_dir}" && terraform apply -input=false -auto-approve)

inventory="${tf_dir}/inventory.ini"
if [[ ! -f "${inventory}" ]]; then
    echo "ERROR: terraform did not produce ${inventory}" >&2
    exit 3
fi

echo "==> waiting 30s for the new instance to boot"
sleep 30

echo "==> ansible-playbook"
(cd "${ansible_dir}" && ansible-playbook -i "${inventory}" playbook.yml)

echo "==> done"
public_ip=$(cd "${tf_dir}" && terraform output -raw public_ip)
echo "App health: http://${public_ip}:8000/health"
echo "App UI:     http://${public_ip}:8000/"
