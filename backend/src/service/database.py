"""
Database utilities and connection management.
"""
import os
from typing import Any

import dotenv
from pypika import QmarkParameter
from sqlalchemy import text, create_engine as sa_create_engine, Engine

dotenv.load_dotenv()


def create_engine() -> Engine:
    """Create and return a new SQLAlchemy Engine instance."""
    connection_string = os.getenv("SQL_ALCHEMY_CONNECTION")
    if not connection_string:
        raise ValueError(
            "SQL_ALCHEMY_CONNECTION is not set. Configure it in your .env file."
        )
    if not connection_string.startswith("mysql"):
        raise ValueError("SQL_ALCHEMY_CONNECTION must use a MySQL connection URL.")

    return sa_create_engine(connection_string)


def run_query(engine: Engine, query: Any) -> Any:
    """Execute a PyPika query using the provided SQLAlchemy engine."""
    param_handler = QmarkParameter()
    sql_query = query.get_sql(quote_char="`", parameter=param_handler)
    parameters = param_handler.get_parameters()
    
    named_params = {}
    for index, value in enumerate(parameters):
        sql_query = sql_query.replace('?', f':p{index}', 1)
        named_params[f'p{index}'] = value

    with engine.connect() as conn:
        result = conn.execute(text(sql_query), named_params)
        conn.commit()
        return result.all() if result.returns_rows else result.rowcount
