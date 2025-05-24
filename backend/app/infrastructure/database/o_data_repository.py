import duckdb
import json
from typing import List, Dict, Any
from app.domain.interfaces.o_data_repository import ODataRepository

class DuckDBODataRepository(ODataRepository):
    def __init__(self, db_path: str = 'odata.db'):
        self.connection = duckdb.connect(db_path)
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS odata_data (
            odata_id VARCHAR,
            odata_etag VARCHAR,
            odata_editLink VARCHAR,
            UserName VARCHAR,
            FirstName VARCHAR,
            LastName VARCHAR,
            Emails TEXT,
            AddressInfo TEXT,
            Gender VARCHAR,
            Concurrency BIGINT
        );
        """
        self.connection.execute(create_table_query)

    def save(self, data: List[Dict[str, Any]]) -> None:
        for record in data:
            odata_id = record.get('@odata.id')
            odata_etag = record.get('@odata.etag')
            odata_editLink = record.get('@odata.editLink')
            user_name = record.get('UserName')
            first_name = record.get('FirstName')
            last_name = record.get('LastName')
            emails = json.dumps(record.get('Emails', []))
            address_info = json.dumps(record.get('AddressInfo', []))
            gender = record.get('Gender')
            concurrency = record.get('Concurrency')

            insert_query = """
            INSERT INTO odata_data (
                odata_id, odata_etag, odata_editLink, UserName, FirstName, LastName, Emails, AddressInfo, Gender, Concurrency
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            self.connection.execute(insert_query, (odata_id, odata_etag, odata_editLink, user_name, first_name, last_name, emails, address_info, gender, concurrency))
