# src/routers/dependencies.py
from src.infrastructure.adapters.duckdb_adapter import DuckDBAdapter
from src.domain.interfaces.external_api import IExternalAPI
# We will import the *instances* from main.py inside the functions
# This avoids top-level import cycle issues but means main.py must be importable
# and have these instances defined when these functions are called.

def get_db_adapter() -> DuckDBAdapter:
    from src.main import db_adapter # db_adapter is instantiated in main.py
    return db_adapter

def get_api_adapter() -> IExternalAPI:
    from src.main import api_adapter # api_adapter is instantiated in main.py
    return api_adapter
