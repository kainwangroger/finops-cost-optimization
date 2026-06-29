output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "clickhouse_fqdn" {
  value = "${azurerm_container_group.clickhouse.fqdn}:8123"
}

output "clickhouse_ip" {
  value = azurerm_container_group.clickhouse.ip_address
}

output "log_analytics_workspace" {
  value = azurerm_log_analytics_workspace.this.name
}
