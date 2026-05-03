output "instance_id" {
  description = "Linode instance ID."
  value       = linode_instance.blackwell.id
}

output "label" {
  description = "Instance label."
  value       = linode_instance.blackwell.label
}

output "public_ip" {
  description = "Public IPv4 address."
  value       = local.blackwell_public_ip
}

output "private_ip" {
  description = "Private IPv4 address (if allocated)."
  value       = try(linode_instance.blackwell.private_ip_address, null)
}

output "ssh_command" {
  description = "Convenience SSH command."
  value       = "ssh root@${local.blackwell_public_ip != "" ? local.blackwell_public_ip : "<ip-not-yet-allocated>"}"
}

output "root_pass" {
  description = "Generated root password (use SSH key auth in practice)."
  value       = random_password.root.result
  sensitive   = true
}

output "ansible_inventory_path" {
  description = "Path to the rendered Ansible inventory, if any."
  value       = var.render_ansible_inventory ? "${path.module}/inventory.ini" : null
}
