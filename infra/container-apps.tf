# --- Logs storage, required by the Container Apps environment ---
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "logs-crop"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# --- The shared space the job and the frontend run in ---
resource "azurerm_container_app_environment" "env" {
  name                       = "ContainerAppsEnv"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = var.location
  logs_destination           = "log-analytics"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }
}

# --- Values both containers need to reach Postgres ---
locals {
  pg_host = azurerm_postgresql_flexible_server.pg.fqdn
  pg_db   = azurerm_postgresql_flexible_server_database.db.name
}

# --- Pipeline: Dagster runs once (CSV -> staging -> cleaned -> dbt build), then stops ---
resource "azurerm_container_app_job" "pipeline" {
  name                         = "pipeline-dagster"
  location                     = var.location
  resource_group_name          = azurerm_resource_group.rg.name
  workload_profile_name        = "Consumption"
  container_app_environment_id = azurerm_container_app_environment.env.id
  replica_timeout_in_seconds   = 1800 # stop after 30 minutes at most
  replica_retry_limit          = 0

  # Started by hand: az containerapp job start
  manual_trigger_config {
    parallelism              = 1
    replica_completion_count = 1
  }

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }
  secret {
    name  = "db-admin-password"
    value = var.db_admin_password
  }

  secret {
    name  = "streamlit-reader-password"
    value = var.streamlit_reader_password
  }

  secret {
    name  = "chatbot-reader-password"
    value = var.chatbot_reader_password
  }


  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  template {
    container {
      name   = "pipeline"
      image  = "${azurerm_container_registry.acr.login_server}/backend:${var.backend_image_tag}"
      cpu    = 1.0
      memory = "2Gi"
      command = ["uv", "run", "--no-sync", "dagster", "asset", "materialize",
      "--select", "*", "-m", "backend.orchestration.definitions"]

      env {
        name  = "POSTGRES_HOST"
        value = local.pg_host
      }
      env {
        name  = "POSTGRES_PORT"
        value = "5432"
      }
      env {
        name  = "POSTGRES_DB"
        value = local.pg_db
      }
      env {
        name  = "POSTGRES_USER"
        value = var.db_admin_user
      }
      env {
        name        = "POSTGRES_PASSWORD"
        secret_name = "db-admin-password"
      }
      env {
        name  = "POSTGRES_SSLMODE"
        value = "require"
      }

      env {
        name        = "STREAMLIT_READER_PASSWORD"
        secret_name = "streamlit-reader-password"
      }

      env {
        name        = "CHATBOT_READER_PASSWORD"
        secret_name = "chatbot-reader-password"
      }
    }
  }
}

# --- Frontend: Streamlit reads the warehouse as a read-only user ---
resource "azurerm_container_app" "frontend" {
  name                         = "frontend"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  workload_profile_name        = "Consumption"
  revision_mode                = "Single"

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }
  secret {
    name  = "streamlit-reader-password"
    value = var.streamlit_reader_password
  }
  secret {
    name  = "chatbot-reader-password"
    value = var.chatbot_reader_password
  }

  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  ingress {
    external_enabled = true
    target_port      = 8501
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  template {
    min_replicas = 0
    max_replicas = 1

    container {
      name   = "frontend"
      image  = "${azurerm_container_registry.acr.login_server}/frontend:${var.frontend_image_tag}"
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "POSTGRES_HOST"
        value = local.pg_host
      }
      env {
        name  = "POSTGRES_PORT"
        value = "5432"
      }
      env {
        name  = "POSTGRES_DB"
        value = local.pg_db
      }
      env {
        name  = "POSTGRES_USER"
        value = "streamlit_reader"
      }
      env {
        name        = "POSTGRES_PASSWORD"
        secret_name = "streamlit-reader-password"
      }
      env {
        name  = "POSTGRES_SSLMODE"
        value = "require"
      }
      env {
        name  = "CHATBOT_DB_USER"
        value = "chatbot_reader"
      }
      env {
        name        = "CHATBOT_DB_PASSWORD"
        secret_name = "chatbot-reader-password"
      }
    }
  }
}