# --- Logs storage, required by the Container Apps environment | Require by Azure, in the portal it is: "Logs" ---
resource "azurerm_log_analytics_workspace" "logs" {
  name                = "logs-crop"
  resource_group_name = azurerm_resource_group.rg.name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# --- The shared "building" both apps live in | In the Azure portal it is: “Container Apps Environment”.
resource "azurerm_container_app_environment" "env" {
  name                       = "ContainerAppsEnv"
  resource_group_name        = azurerm_resource_group.rg.name
  location                   = var.location
  logs_destination           = "log-analytics"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.logs.id
}


# --- Backend container app ---
resource "azurerm_container_app" "backend" {
  name                         = "backend"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single" # Only one version runs. A new deploy replaces the old one

  # --- Storing passwords (ACR password, database URL) ---
  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
  }
  secret {
    name  = "database-url"
    value = local.database_url
  }

  # --- How to log to get in ACR to get the image ---
  registry {
    server               = azurerm_container_registry.acr.login_server
    username             = azurerm_container_registry.acr.admin_username
    password_secret_name = "acr-password"
  }

  # --- Gives the app a public URL ---
  ingress {
    external_enabled = true
    target_port      = 8000
    # --- All visitors go to the newest version ---
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  # --- Shuts down when nobody uses it ---
  template {
    min_replicas = 0
    max_replicas = 1

    # --- Which image to run from ACR ---
    container {
      name  = "backend"
      image = "${azurerm_container_registry.acr.login_server}/backend:${var.image_tag}"
      # --- How much power the app gets ---
      cpu    = 0.25
      memory = "0.5Gi"

      # --- Environment variables: DATABASE_URL for the backend, BACKEND_URL for the frontend ---
      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
    }
  }
}

# --- Frontend (Streamlit) container app | See above comments as they are similar ---
resource "azurerm_container_app" "frontend" {
  name                         = "frontend"
  container_app_environment_id = azurerm_container_app_environment.env.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"

  secret {
    name  = "acr-password"
    value = azurerm_container_registry.acr.admin_password
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
      image  = "${azurerm_container_registry.acr.login_server}/frontend:${var.image_tag}"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "BACKEND_URL"
        value = "https://${azurerm_container_app.backend.ingress[0].fqdn}"
      }
    }
  }
}