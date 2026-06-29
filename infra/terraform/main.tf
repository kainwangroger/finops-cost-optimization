terraform {
  required_version = ">= 1.5"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  prefix = "finops-${random_string.suffix.result}"
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "${local.prefix}-logs"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
}

resource "azurerm_container_group" "clickhouse" {
  name                = "${local.prefix}-ch"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  os_type             = "Linux"
  restart_policy      = "Always"
  ip_address_type     = "Public"
  dns_name_label      = local.prefix

  container {
    name   = "clickhouse"
    image  = "clickhouse/clickhouse-server:24.8"
    cpu    = 1.0
    memory = 2.0
    ports {
      port     = 8123
      protocol = "TCP"
    }
    ports {
      port     = 9000
      protocol = "TCP"
    }
  }

  container {
    name   = "postgres"
    image  = "postgres:16-alpine"
    cpu    = 0.5
    memory = 1.0
    ports {
      port     = 5432
      protocol = "TCP"
    }
    environment_variables = {
      POSTGRES_USER     = "finops"
      POSTGRES_PASSWORD = "finops"
      POSTGRES_DB       = "finops"
    }
  }

  container {
    name   = "streamlit"
    image  = "python:3.12-slim"
    cpu    = 0.5
    memory = 1.0
    ports {
      port     = 8501
      protocol = "TCP"
    }
    command = ["bash", "-c", "pip install streamlit pandas -q && streamlit run src/dashboard/app.py --server.port 8501 --server.address 0.0.0.0"]
  }
}

resource "azurerm_monitor_diagnostic_setting" "this" {
  name                       = "${local.prefix}-diag"
  target_resource_id         = azurerm_container_group.clickhouse.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id

  enabled_log {
    category = "ContainerInstanceLog"
  }
  metric {
    category = "AllMetrics"
    enabled  = true
  }
}
