# src/infrastructure/adapters/duckdb_adapter.py
import duckdb
import logging # Added
from typing import List, Optional, TypeVar, Generic, Any, Dict, Type, Union
from pydantic import BaseModel
from pydantic.fields import ModelField
from datetime import date

from src.domain.entities import Well, Field, Production, OilPrice, ExchangeRate
from src.domain.interfaces.repository import (
    IWellRepository, IFieldRepository, 
    IProductionRepository, IOilPriceRepository, IExchangeRateRepository
) 
from src.config import DATABASE_PATH
from src.core.exceptions import DatabaseError # Added

logger = logging.getLogger(__name__) # Added

T = TypeVar('T', bound=BaseModel)

PYDANTIC_TO_DUCKDB_TYPES: Dict[Type, str] = {
    str: "VARCHAR",
    int: "INTEGER",
    float: "DOUBLE",
    date: "DATE",
    bool: "BOOLEAN",
}

PRIMARY_KEY_COLUMNS: Dict[str, Union[str, List[str]]] = {
    "Well": "well_code",
    "Field": "field_code",
    "Production": ["well_code", "reference_date"], 
    "OilPrice": ["field_code", "reference_date"],   
    "ExchangeRate": "reference_date" 
}

class DuckDBGenericRepository(Generic[T]):
    def __init__(self, connection: duckdb.DuckDBPyConnection, table_name: str, model: Type[T]):
        self.connection = connection
        self.table_name = table_name
        self.model = model
        self.fields = model.__fields__
        self.pk_info = PRIMARY_KEY_COLUMNS.get(model.__name__)
        logger.debug(f"Initialized DuckDBGenericRepository for table '{table_name}', model '{model.__name__}'.")


    def _build_where_clause(self, conditions: Dict[str, Any]) -> tuple[str, list]:
        if not conditions:
            return "", []
        clauses = [f"{key} = ?" for key in conditions.keys()]
        values = list(conditions.values())
        return "WHERE " + " AND ".join(clauses), values

    def add(self, entity: T) -> T:
        columns = list(self.fields.keys())
        values_placeholders = ["?"] * len(columns)
        insert_values = [getattr(entity, field_name) for field_name in columns]

        for i, val in enumerate(insert_values):
            if isinstance(val, BaseModel):
                logger.error(f"Field '{columns[i]}' is a nested Pydantic model. Repository expects flat entities.")
                raise DatabaseError(message=f"Cannot insert nested model for field {columns[i]}.")

        cols_sql = ", ".join(columns)
        placeholders_sql = ", ".join(values_placeholders)
        sql = f"INSERT INTO {self.table_name} ({cols_sql}) VALUES ({placeholders_sql})"
        
        logger.debug(f"Executing SQL: {sql} with values: {insert_values}")
        try:
            self.connection.execute(sql, insert_values)
            logger.info(f"Entity added to {self.table_name}: {entity}")
        except duckdb.Error as e:
            logger.error(f"Error adding entity to {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message=f"Error adding entity to {self.table_name}", detail=str(e)) from e
        return entity

    def get(self, entity_id: Any) -> Optional[T]:
        if not isinstance(self.pk_info, str):
            msg = f"Entity {self.model.__name__} has a composite PK. Use get_by_composite_key."
            logger.error(msg)
            raise TypeError(msg)
        id_column_name = self.pk_info
        
        sql = f"SELECT * FROM {self.table_name} WHERE {id_column_name} = ?"
        logger.debug(f"Executing SQL: {sql} with ID: {entity_id}")
        try:
            result = self.connection.execute(sql, [entity_id]).fetchone()
        except duckdb.Error as e:
            logger.error(f"Error fetching entity by {id_column_name} from {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message=f"Error fetching entity by {id_column_name}", detail=str(e)) from e
            
        if result:
            column_names = [desc[0] for desc in self.connection.description]
            row_dict = dict(zip(column_names, result))
            logger.debug(f"Found entity in {self.table_name}: {row_dict}")
            return self.model(**row_dict)
        logger.debug(f"No entity found in {self.table_name} with {id_column_name}={entity_id}")
        return None
        
    def get_by_composite_key(self, key_values: Dict[str, Any]) -> Optional[T]:
        if not isinstance(self.pk_info, list) or not all(k in self.pk_info for k in key_values.keys()):
            msg = f"Provided keys do not match composite PK definition for {self.model.__name__}."
            logger.error(msg + f" PK_INFO: {self.pk_info}, KEYS: {key_values.keys()}")
            raise ValueError(msg)

        where_clause, values = self._build_where_clause(key_values)
        sql = f"SELECT * FROM {self.table_name} {where_clause}"
        logger.debug(f"Executing SQL: {sql} with values: {values}")
        try:
            result = self.connection.execute(sql, values).fetchone()
        except duckdb.Error as e:
            logger.error(f"Error fetching entity by composite key from {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message="Error fetching entity by composite key", detail=str(e)) from e

        if result:
            column_names = [desc[0] for desc in self.connection.description]
            row_dict = dict(zip(column_names, result))
            logger.debug(f"Found entity in {self.table_name} by composite key: {row_dict}")
            return self.model(**row_dict)
        logger.debug(f"No entity found in {self.table_name} with composite key: {key_values}")
        return None

    def list(self, filters: Optional[Dict[str, Any]] = None) -> List[T]:
        where_clause, values = self._build_where_clause(filters) if filters else ("", [])
        sql = f"SELECT * FROM {self.table_name} {where_clause}"
        logger.debug(f"Executing SQL: {sql} with filters: {values}")
        try:
            results = self.connection.execute(sql, values).fetchall()
        except duckdb.Error as e:
            logger.error(f"Error listing entities from {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message=f"Error listing entities from {self.table_name}", detail=str(e)) from e

        column_names = [desc[0] for desc in self.connection.description or []]
        entities = [self.model(**dict(zip(column_names, row))) for row in results]
        logger.debug(f"Listed {len(entities)} entities from {self.table_name} with filters: {filters}")
        return entities

    def update(self, entity: T, entity_id: Any) -> T:
        if not isinstance(self.pk_info, str):
            msg = f"Entity {self.model.__name__} has a composite PK. Use update_by_composite_key."
            logger.error(msg)
            raise TypeError(msg)
        id_column_name = self.pk_info

        set_clauses = [f"{field_name} = ?" for field_name in self.fields.keys() if field_name != id_column_name]
        update_values = [getattr(entity, field_name) for field_name in self.fields.keys() if field_name != id_column_name]
        update_values.append(entity_id) 
        
        set_sql = ", ".join(set_clauses)
        sql = f"UPDATE {self.table_name} SET {set_sql} WHERE {id_column_name} = ?"
        logger.debug(f"Executing SQL: {sql} with values: {update_values}")
        try:
            self.connection.execute(sql, update_values)
            logger.info(f"Entity updated in {self.table_name} with ID {entity_id}: {entity}")
        except duckdb.Error as e:
            logger.error(f"Error updating entity in {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message=f"Error updating entity in {self.table_name}", detail=str(e)) from e
        return entity

    def update_by_composite_key(self, entity: T, key_values: Dict[str, Any]) -> T:
        if not isinstance(self.pk_info, list) or not all(k in self.pk_info for k in key_values.keys()):
             msg = f"Provided keys do not match composite PK definition for {self.model.__name__}."
             logger.error(msg)
             raise ValueError(msg)

        set_clauses = [f"{field_name} = ?" for field_name in self.fields.keys() if field_name not in self.pk_info]
        update_values = [getattr(entity, field_name) for field_name in self.fields.keys() if field_name not in self.pk_info]

        where_clause, where_values = self._build_where_clause(key_values)
        update_values.extend(where_values)
        
        set_sql = ", ".join(set_clauses)
        sql = f"UPDATE {self.table_name} SET {set_sql} {where_clause}"
        logger.debug(f"Executing SQL: {sql} with values: {update_values}")
        try:
            self.connection.execute(sql, update_values)
            logger.info(f"Entity updated by composite key in {self.table_name} with keys {key_values}: {entity}")
        except duckdb.Error as e:
            logger.error(f"Error updating entity by composite key in {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message="Error updating entity by composite key", detail=str(e)) from e
        return entity

    def delete(self, entity_id: Any) -> None:
        if not isinstance(self.pk_info, str):
            msg = f"Entity {self.model.__name__} has a composite PK. Use delete_by_composite_key."
            logger.error(msg)
            raise TypeError(msg)
        id_column_name = self.pk_info
        
        sql = f"DELETE FROM {self.table_name} WHERE {id_column_name} = ?"
        logger.debug(f"Executing SQL: {sql} with ID: {entity_id}")
        try:
            self.connection.execute(sql, [entity_id])
            logger.info(f"Entity deleted from {self.table_name} with ID {entity_id}.")
        except duckdb.Error as e:
            logger.error(f"Error deleting entity by {id_column_name} from {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message=f"Error deleting entity by {id_column_name}", detail=str(e)) from e
            
    def delete_by_composite_key(self, key_values: Dict[str, Any]) -> None:
        if not isinstance(self.pk_info, list) or not all(k in self.pk_info for k in key_values.keys()):
            msg = f"Provided keys do not match composite PK definition for {self.model.__name__}."
            logger.error(msg)
            raise ValueError(msg)

        where_clause, values = self._build_where_clause(key_values)
        sql = f"DELETE FROM {self.table_name} {where_clause}"
        logger.debug(f"Executing SQL: {sql} with values: {values}")
        try:
            self.connection.execute(sql, values)
            logger.info(f"Entity deleted from {self.table_name} with composite key {key_values}.")
        except duckdb.Error as e:
            logger.error(f"Error deleting entity by composite key from {self.table_name}: {e}", exc_info=True)
            raise DatabaseError(message="Error deleting entity by composite key", detail=str(e)) from e

# --- Concrete Repositories --- (Structure unchanged, only super() calls to generic methods)
class WellDuckDBRepository(DuckDBGenericRepository[Well], IWellRepository):
    def __init__(self, connection: duckdb.DuckDBPyConnection, table_name: str = "wells"):
        super().__init__(connection, table_name, Well)

    def get_by_well_code(self, well_code: str) -> Optional[Well]:
        return self.get(entity_id=well_code)

    def find_by_name(self, well_name: str) -> List[Well]:
        return self.list(filters={"well_name": well_name})

    def find_by_field_code(self, field_code: str) -> List[Well]:
        return self.list(filters={"field_code": field_code})

class FieldDuckDBRepository(DuckDBGenericRepository[Field], IFieldRepository):
    def __init__(self, connection: duckdb.DuckDBPyConnection, table_name: str = "fields"):
        super().__init__(connection, table_name, Field)

    def get_by_field_code(self, field_code: str) -> Optional[Field]:
        return self.get(entity_id=field_code)

    def find_by_name(self, field_name: str) -> List[Field]:
        return self.list(filters={"field_name": field_name})

class ProductionDuckDBRepository(DuckDBGenericRepository[Production], IProductionRepository):
    def __init__(self, connection: duckdb.DuckDBPyConnection, table_name: str = "production"):
        super().__init__(connection, table_name, Production)

    def get_by_well_code_and_date(self, well_code: str, reference_date: date) -> Optional[Production]:
        return self.get_by_composite_key({"well_code": well_code, "reference_date": reference_date})

    def find_by_well_code(self, well_code: str) -> List[Production]:
        return self.list(filters={"well_code": well_code})
        
    def find_by_date_range(self, start_date: date, end_date: date) -> List[Production]:
        sql = f"SELECT * FROM {self.table_name} WHERE reference_date BETWEEN ? AND ?"
        logger.debug(f"Executing SQL for Production date range: {sql} with {start_date}, {end_date}")
        try:
            results = self.connection.execute(sql, [start_date, end_date]).fetchall()
            column_names = [desc[0] for desc in self.connection.description or []]
            return [self.model(**dict(zip(column_names, row))) for row in results]
        except duckdb.Error as e:
            logger.error(f"Error in find_by_date_range for Production: {e}", exc_info=True)
            raise DatabaseError(message="Error in find_by_date_range for Production", detail=str(e)) from e

        def find_by_well_code_and_date_range(self, well_code: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Production]:
            params: List[Any] = [well_code]
            query = f"SELECT * FROM {self.table_name} WHERE well_code = ?"
            if start_date:
                query += " AND reference_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND reference_date <= ?"
                params.append(end_date)
            query += " ORDER BY reference_date ASC"
            
            logger.debug(f"Executing SQL: {query} with params: {params}")
            try:
                results = self.connection.execute(query, params).fetchall()
                column_names = [desc[0] for desc in self.connection.description or []]
                return [self.model(**dict(zip(column_names, row))) for row in results]
            except duckdb.Error as e:
                logger.error(f"Error in find_by_well_code_and_date_range for Production: {e}", exc_info=True)
                raise DatabaseError(message="Error in find_by_well_code_and_date_range for Production", detail=str(e)) from e

class OilPriceDuckDBRepository(DuckDBGenericRepository[OilPrice], IOilPriceRepository):
    def __init__(self, connection: duckdb.DuckDBPyConnection, table_name: str = "oil_prices"):
        super().__init__(connection, table_name, OilPrice)

    def get_by_field_code_and_date(self, field_code: str, reference_date: date) -> Optional[OilPrice]:
        return self.get_by_composite_key({"field_code": field_code, "reference_date": reference_date})

    def find_by_field_code(self, field_code: str) -> List[OilPrice]:
        return self.list(filters={"field_code": field_code})
    
    def find_by_date_range(self, start_date: date, end_date: date) -> List[OilPrice]:
        sql = f"SELECT * FROM {self.table_name} WHERE reference_date BETWEEN ? AND ?"
        logger.debug(f"Executing SQL for OilPrice date range: {sql} with {start_date}, {end_date}")
        try:
            results = self.connection.execute(sql, [start_date, end_date]).fetchall()
            column_names = [desc[0] for desc in self.connection.description or []]
            return [self.model(**dict(zip(column_names, row))) for row in results]
        except duckdb.Error as e:
            logger.error(f"Error in find_by_date_range for OilPrice: {e}", exc_info=True)
            raise DatabaseError(message="Error in find_by_date_range for OilPrice", detail=str(e)) from e

class ExchangeRateDuckDBRepository(DuckDBGenericRepository[ExchangeRate], IExchangeRateRepository):
    def __init__(self, connection: duckdb.DuckDBPyConnection, table_name: str = "exchange_rates"):
        super().__init__(connection, table_name, ExchangeRate)

    def get_by_date(self, reference_date: date) -> Optional[ExchangeRate]:
        return self.get(entity_id=reference_date)

    def find_by_date_range(self, start_date: date, end_date: date) -> List[ExchangeRate]:
        sql = f"SELECT * FROM {self.table_name} WHERE reference_date BETWEEN ? AND ?"
        logger.debug(f"Executing SQL for ExchangeRate date range: {sql} with {start_date}, {end_date}")
        try:
            results = self.connection.execute(sql, [start_date, end_date]).fetchall()
            column_names = [desc[0] for desc in self.connection.description or []]
            return [self.model(**dict(zip(column_names, row))) for row in results]
        except duckdb.Error as e:
            logger.error(f"Error in find_by_date_range for ExchangeRate: {e}", exc_info=True)
            raise DatabaseError(message="Error in find_by_date_range for ExchangeRate", detail=str(e)) from e

# --- DuckDB Adapter Main Class ---
class DuckDBAdapter:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path if db_path else DATABASE_PATH
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
        logger.info(f"DuckDBAdapter initialized with db_path: {self.db_path}")
        
        self.well_repository: Optional[IWellRepository] = None
        self.field_repository: Optional[IFieldRepository] = None
        self.production_repository: Optional[IProductionRepository] = None
        self.oil_price_repository: Optional[IOilPriceRepository] = None
        self.exchange_rate_repository: Optional[IExchangeRateRepository] = None

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        if self._connection is None or self._connection.closed:
            try:
                logger.info(f"Attempting to connect to DuckDB at {self.db_path}...")
                self._connection = duckdb.connect(database=self.db_path, read_only=False)
                logger.info(f"Successfully connected to DuckDB at {self.db_path}.")
            except Exception as e:
                logger.error(f"Failed to connect to DuckDB at {self.db_path}: {e}", exc_info=True)
                raise DatabaseError(message=f"Failed to connect to DuckDB at {self.db_path}", detail=str(e)) from e
        return self._connection

    def _close_connection(self):
        if self._connection and not self._connection.closed:
            logger.info(f"Closing DuckDB connection to {self.db_path}.")
            self._connection.close()
            logger.info(f"DuckDB connection to {self.db_path} closed.")
        self._connection = None

    def _get_pydantic_field_type(self, model_field: ModelField) -> Type:
        if model_field.outer_type_ is not None and hasattr(model_field.outer_type_, '__origin__') and model_field.outer_type_.__origin__ is Union:
            for arg in model_field.outer_type_.__args__:
                if arg is not type(None):
                    return arg
        return model_field.type_

    def _create_table_if_not_exists(self, entity_model: Type[BaseModel], table_name: str):
        conn = self._get_connection()
        columns_sql_parts = []
        model_pk_info = PRIMARY_KEY_COLUMNS.get(entity_model.__name__)
        logger.debug(f"Creating table '{table_name}' for model '{entity_model.__name__}'. PK info: {model_pk_info}")

        for field_name, model_field in entity_model.__fields__.items():
            actual_type = self._get_pydantic_field_type(model_field)
            sql_type = PYDANTIC_TO_DUCKDB_TYPES.get(actual_type)
            
            if not sql_type:
                msg = f"Unsupported type {actual_type} for field {field_name} in {entity_model.__name__}"
                if issubclass(actual_type, BaseModel):
                    msg = f"Nested BaseModel '{actual_type.__name__}' for field '{field_name}' not supported directly for table creation. Define as simple type (e.g., FK ID)."
                logger.error(msg)
                raise ValueError(msg)

            column_sql = f"{field_name} {sql_type}"
            if model_field.required: column_sql += " NOT NULL"
            else: column_sql += " NULL"
            columns_sql_parts.append(column_sql)
        
        pk_constraint_sql = ""
        if isinstance(model_pk_info, list): 
            pk_cols_str = ", ".join(model_pk_info)
            pk_constraint_sql = f", PRIMARY KEY ({pk_cols_str})"
        elif isinstance(model_pk_info, str): 
            for i, part in enumerate(columns_sql_parts):
                if part.startswith(model_pk_info + " "):
                    columns_sql_parts[i] = part.replace(" NOT NULL", "").replace(" NULL", "") + " PRIMARY KEY"
                    break
        
        columns_sql = ", ".join(columns_sql_parts)
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql}{pk_constraint_sql})"
        logger.debug(f"Executing CREATE TABLE SQL: {create_table_sql}")
        try:
            conn.execute(create_table_sql)
            logger.info(f"Table '{table_name}' (re)checked/created for {entity_model.__name__}.")
        except duckdb.Error as e:
            logger.error(f"Error creating table {table_name}: {e}", exc_info=True)
            raise DatabaseError(message=f"Error creating table {table_name}", detail=str(e)) from e

    def initialize_database(self):
        logger.info("Initializing database: Creating tables...")
        conn = self._get_connection()

        self._create_table_if_not_exists(Well, "wells")
        self._create_table_if_not_exists(Field, "fields")
        self._create_table_if_not_exists(Production, "production")
        self._create_table_if_not_exists(OilPrice, "oil_prices")
        self._create_table_if_not_exists(ExchangeRate, "exchange_rates")
        logger.info("Database tables checked/created.")

        logger.info("Initializing repositories...")
        self.well_repository = WellDuckDBRepository(conn)
        self.field_repository = FieldDuckDBRepository(conn)
        self.production_repository = ProductionDuckDBRepository(conn)
        self.oil_price_repository = OilPriceDuckDBRepository(conn)
        self.exchange_rate_repository = ExchangeRateDuckDBRepository(conn)
        logger.info("Repositories initialized.")

    def get_well_repository(self) -> IWellRepository:
        if not self.well_repository: self.initialize_database()
        return self.well_repository 
    def get_field_repository(self) -> IFieldRepository:
        if not self.field_repository: self.initialize_database()
        return self.field_repository 
    def get_production_repository(self) -> IProductionRepository:
        if not self.production_repository: self.initialize_database()
        return self.production_repository 
    def get_oil_price_repository(self) -> IOilPriceRepository:
        if not self.oil_price_repository: self.initialize_database()
        return self.oil_price_repository 
    def get_exchange_rate_repository(self) -> IExchangeRateRepository:
        if not self.exchange_rate_repository: self.initialize_database()
        return self.exchange_rate_repository 

    def __enter__(self):
        logger.debug("DuckDBAdapter context manager entered.")
        self._get_connection()
        self.initialize_database()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("DuckDBAdapter context manager exited.")
        self._close_connection()

if __name__ == '__main__':
    # Basic logging setup for standalone testing of this module
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("Running DuckDBAdapter example...")
    adapter = DuckDBAdapter(db_path=":memory:")

    with adapter:
        logger.info("Adapter initialized via context manager.")
        
        well_repo = adapter.get_well_repository()
        prod_repo = adapter.get_production_repository()

        logger.info("\n--- Well Example ---")
        test_well = Well(well_code="W001", well_name="Test Well Alpha", field_name="Test Field", field_code="F01")
        added_well = well_repo.add(test_well)
        logger.info(f"Added Well: {added_well}")
        retrieved_well = well_repo.get_by_well_code("W001")
        logger.info(f"Retrieved Well: {retrieved_well}")
        assert retrieved_well and retrieved_well.well_name == "Test Well Alpha"
        
        retrieved_well.field_name = "Updated Test Field"
        updated_well_response = well_repo.update(retrieved_well, retrieved_well.well_code)
        logger.info(f"Updated Well: {updated_well_response}")
        retrieved_again = well_repo.get_by_well_code("W001")
        logger.info(f"Retrieved After Update: {retrieved_again}")
        assert retrieved_again and retrieved_again.field_name == "Updated Test Field"

        logger.info("\n--- Production Example (Composite Key) ---")
        today = date.today()
        # Corrected Production instantiation based on entity definition
        prod_entry = Production(reference_date=today, oil_prod=100.5, gas_prod=50.2, water_prod=20.0, well_code="W001")
        added_prod = prod_repo.add(prod_entry)
        logger.info(f"Added Production: {added_prod}")
        
        retrieved_prod = prod_repo.get_by_well_code_and_date("W001", today)
        logger.info(f"Retrieved Production: {retrieved_prod}")
        assert retrieved_prod and retrieved_prod.oil_prod == 100.5
        
        retrieved_prod.oil_prod = 110.0
        prod_repo.update_by_composite_key(retrieved_prod, {"well_code": "W001", "reference_date": today})
        retrieved_prod_updated = prod_repo.get_by_well_code_and_date("W001", today)
        logger.info(f"Updated Production: {retrieved_prod_updated}")
        assert retrieved_prod_updated and retrieved_prod_updated.oil_prod == 110.0

        prod_repo.delete_by_composite_key({"well_code": "W001", "reference_date": today})
        assert prod_repo.get_by_well_code_and_date("W001", today) is None
        logger.info("Production entry deleted.")

        well_repo.delete(added_well.well_code)
        assert well_repo.get_by_well_code("W001") is None
        logger.info("Well entry deleted.")

    logger.info("\nDuckDBAdapter example finished.")
