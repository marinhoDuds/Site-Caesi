import os
import dotenv
from typing import Any
from pypika import Query, QmarkParameter
from sqlalchemy import text, create_engine as sa_create_engine, Engine

dotenv.load_dotenv()


def create_engine() -> Engine:
    connection_string = os.getenv("SQL_ALCHEMY_CONNECTION")
    if not connection_string:
        raise ValueError(
            "SQL_ALCHEMY_CONNECTION is not set. Configure it in your .env file."
        )

    engine = sa_create_engine(connection_string)
    return engine


def run_query(engine: Engine, query: Any) -> Any:
    param_handler = QmarkParameter()
    sql_query = query.get_sql(parameter=param_handler)
    parameters = param_handler.get_parameters()
    with engine.connect() as conn:
        result = conn.execute(text(sql_query), parameters)
        conn.commit()

        if result.returns_rows:
            return result.all()

        return result.rowcount
