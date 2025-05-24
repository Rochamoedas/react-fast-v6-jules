# src/config.py
# This file holds various settings for the application.

# API URLs
OIL_PRICE_API_URL = "YOUR_OIL_PRICE_API_URL_HERE"  # Placeholder for Oil Price API URL
EXCHANGE_RATE_API_URL = "YOUR_EXCHANGE_RATE_API_URL_HERE"  # Placeholder for Exchange Rate API URL
PRODUCTION_DATA_API_URL = "YOUR_PRODUCTION_DATA_API_URL_HERE"  # Placeholder for Production Data API URL
ODATA_PRODUCTION_DATA_API_URL = "YOUR_ODATA_PRODUCTION_DATA_API_URL_HERE"  # Placeholder for OData Production Data API URL

# API Keys & Credentials
OIL_PRICE_API_KEY = "YOUR_OIL_PRICE_API_KEY_HERE"  # Placeholder for Oil Price API Key
PRODUCTION_API_KEY = "YOUR_PRODUCTION_API_KEY_HERE"  # Placeholder for Production API Key
# Note: Depending on the exchange rate API, an API key might be needed.
# EXCHANGE_RATE_API_KEY = "YOUR_EXCHANGE_RATE_API_KEY_HERE"

# OData API Credentials (Basic Auth)
# For production, these should be loaded from environment variables or a secure vault.
ODATA_API_USERNAME = "YOUR_ODATA_API_USERNAME_HERE"  # Placeholder for OData API Username
ODATA_API_PASSWORD = "YOUR_ODATA_API_PASSWORD_HERE"  # Placeholder for OData API Password

# Database Path
DATABASE_PATH = "data/local_database.duckdb"  # Path for the DuckDB database file

# Chunk Sizes
DEFAULT_CHUNK_SIZE = 10000  # Default chunk size for processing large datasets

# Basic Column Schema Definitions
# These schemas define the expected structure for various data entities.
# Types are represented as strings, which will be mapped to actual database types.

WELL_SCHEMA = {
    "well_code": "VARCHAR",  # Unique identifier for the well
    "well_name": "VARCHAR",  # Name of the well
    "field_name": "VARCHAR",  # Name of the field the well belongs to
    "operator_name": "VARCHAR",  # Name of the operator
    "latitude": "DOUBLE",  # Latitude of the well
    "longitude": "DOUBLE",  # Longitude of the well
    "spud_date": "DATE",  # Date the well was spudded
    "completion_date": "DATE",  # Date the well was completed
    "status": "VARCHAR"  # Current status of the well (e.g., Active, Inactive)
}

PRODUCTION_SCHEMA = {
    "well_code": "VARCHAR",  # Foreign key linking to the WELL_SCHEMA
    "production_date": "DATE",  # Date of production
    "oil_volume_bbl": "DOUBLE",  # Volume of oil produced in barrels
    "gas_volume_mcf": "DOUBLE",  # Volume of gas produced in thousand cubic feet
    "water_volume_bbl": "DOUBLE",  # Volume of water produced in barrels
    "bhp": "DOUBLE"  # Bottom Hole Pressure
}

FIELD_SCHEMA = {
    "field_name": "VARCHAR",  # Unique identifier for the field
    "reservoir_formation": "VARCHAR",  # Geological formation of the reservoir
    "discovery_date": "DATE",  # Date the field was discovered
    "country": "VARCHAR"  # Country where the field is located
}

OIL_PRICE_SCHEMA = {
    "price_date": "DATE",  # Date of the oil price
    "price_usd_bbl": "DOUBLE"  # Price of oil in USD per barrel
}

EXCHANGE_RATE_SCHEMA = {
    "rate_date": "DATE",  # Date of the exchange rate
    "from_currency": "VARCHAR",  # Currency converting from (e.g., USD)
    "to_currency": "VARCHAR",  # Currency converting to (e.g., local currency)
    "rate": "DOUBLE"  # Exchange rate
}

# It's good practice to load sensitive information like API keys from environment variables
# or a secure vault in a production environment. For example:
# import os
# OIL_PRICE_API_KEY = os.getenv("OIL_PRICE_API_KEY", "YOUR_DEFAULT_KEY_IF_ANY")
# DATABASE_PATH = os.getenv("DATABASE_PATH", "data/local_database.duckdb")

# Further configurations can be added here as the application grows.
# For instance, logging configurations, external service credentials, etc.
