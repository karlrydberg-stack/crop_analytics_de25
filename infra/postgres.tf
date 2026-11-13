# --- Azure Database for PostgreSQL: stores the raw and clean crop data ---
resource "azurerm_postgresql_flexible_server" "pg" {
  name                          = "crop-analytics-psql-no"
  resource_group_name           = azurerm_resource_group.rg.name
  location                      = var.postgres_location
  version                       = "17"
  administrator_login           = var.db_admin_user
  administrator_password        = var.db_admin_password
  sku_name                      = "B_Standard_B1ms"
  storage_mb                    = 32768 
  public_network_access_enabled = true

  lifecycle {
    ignore_changes = [zone] # Azure picks a zone itself - Nothing to do with compliance regions
  }
}

resource "azurerm_postgresql_flexible_server_database" "db" {
  name      = "crop_db"
  server_id = azurerm_postgresql_flexible_server.pg.id
  charset   = "UTF8" # To include Swedish letters: å, ä, ö stored correctly
  collation = "en_US.utf8"
}

# --- Let other Azure services (backend) connect ---
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_azure" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.pg.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}


# --- The connection string the backend will use ---
locals {
  database_url = "postgresql+psycopg://${var.db_admin_user}:${urlencode(var.db_admin_password)}@${azurerm_postgresql_flexible_server.pg.fqdn}:5432/${azurerm_postgresql_flexible_server_database.db.name}?sslmode=require"
}

