"""
Database utilities and connection management.
"""
import os
import dotenv
from typing import Any
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

    engine = sa_create_engine(connection_string)
    return engine


def run_query(engine: Engine, query: Any) -> Any:
    """Execute a PyPika query using the provided SQLAlchemy engine."""
    param_handler = QmarkParameter()
    sql_query = query.get_sql(parameter=param_handler)
    parameters = param_handler.get_parameters()
    
    named_params = {}
    for i, val in enumerate(parameters):
        sql_query = sql_query.replace('?', f':p{i}', 1)
        named_params[f'p{i}'] = val

    with engine.connect() as conn:
        result = conn.execute(text(sql_query), named_params)
        conn.commit()

        if result.returns_rows:
            return result.all()

        return result.rowcount
