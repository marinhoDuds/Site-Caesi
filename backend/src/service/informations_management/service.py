from typing import List, Optional
from pypika import Query, Table, Order
from sqlalchemy import Engine
from src.service.database import run_query

class InformationService:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.table = Table("information")

    def create_information(self, information_type: str, content: str) -> dict:
        q = Query.into(self.table).columns(
            self.table.information_type,
            self.table.content
        ).insert(
            information_type,
            content
        )
        # Using returning id to get the inserted id since pypika with sqlite doesn't easily return id without dialect specific logic
        # For simplicity, we just use the cursor's lastrowid from run_query
        result = run_query(self.engine, q.get_sql())
        # To get the inserted id reliably, we just query the last inserted row
        return self.get_latest_information()
        
    def get_latest_information(self):
        q = Query.from_(self.table).select("*").orderby(self.table.id, order=Order.desc).limit(1)
        result = run_query(self.engine, q.get_sql())
        return dict(result[0]) if result else None

    def get_information_by_id(self, info_id: int) -> Optional[dict]:
        q = Query.from_(self.table).select("*").where(self.table.id == info_id)
        result = run_query(self.engine, q.get_sql())
        return dict(result[0]) if result else None

    def get_informations_by_type(self, information_type: str) -> List[dict]:
        q = Query.from_(self.table).select("*").where(self.table.information_type == information_type)
        result = run_query(self.engine, q.get_sql())
        return [dict(r) for r in result]

    def update_information(self, info_id: int, information_type: str, content: str) -> Optional[dict]:
        q = Query.update(self.table).set(
            self.table.information_type, information_type
        ).set(
            self.table.content, content
        ).where(self.table.id == info_id)
        run_query(self.engine, q.get_sql())
        return self.get_information_by_id(info_id)

    def delete_information(self, info_id: int) -> bool:
        q = Query.from_(self.table).delete().where(self.table.id == info_id)
        run_query(self.engine, q.get_sql())
        return True
