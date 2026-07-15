from datetime import date
from typing import List, Optional, Any
from pypika import Table, Query
from sqlalchemy import Engine

from src.service.database import run_query
from src.routes.portal.schemas import (
    OperationCreate,
    OperationType,
    OperationResponse,
    OperationHistoryResponse,
)

operation_table = Table("operation")


class PortalService:
    def __init__(self, engine: Engine):
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> OperationResponse:
        """Helper to unpack a row into an OperationResponse."""

        op_id, created_at, value, description, op_type, previous = row
        return OperationResponse(
            id=op_id,
            created_at=created_at,
            value=value,
            description=description,
            operation_type=op_type,
            previous=previous,
        )

    def create_operation(self, payload: OperationCreate) -> OperationResponse:
        current_date = date.today()

        insert_query = (
            Query.into(operation_table)
            .columns("created_at", "value", "description", "operation_type", "previous")
            .insert(
                current_date,
                payload.value,
                payload.description,
                payload.operation_type.value,
                None,
            )
        )

        run_query(self.engine, insert_query)

        fetch_query = (
            Query.from_(operation_table)
            .select("*")
            .orderby("id", order=Query.desc())
            .limit(1)
        )
        result = run_query(self.engine, fetch_query)

        if result and len(result) > 0:
            return self._map_row_to_response(result[0])

        raise Exception("Failed to fetch created operation")

    def update_operation(
        self, previous_id: int, payload: OperationCreate
    ) -> OperationResponse:
        current_date = date.today()
        insert_query = (
            Query.into(operation_table)
            .columns("created_at", "value", "description", "operation_type", "previous")
            .insert(
                current_date,
                payload.value,
                payload.description,
                payload.operation_type.value,
                previous_id,
            )
        )

        run_query(self.engine, insert_query)

        fetch_query = (
            Query.from_(operation_table)
            .select("*")
            .orderby("id", order=Query.desc())
            .limit(1)
        )
        result = run_query(self.engine, fetch_query)

        if result and len(result) > 0:
            return self._map_row_to_response(result[0])

        raise Exception("Failed to fetch created operation")

    def get_operation(self, operation_id: int) -> Optional[OperationHistoryResponse]:
        query = (
            Query.from_(operation_table)
            .select("*")
            .where(operation_table.id == operation_id)
        )
        result = run_query(self.engine, query)

        if not result:
            return None

        base_resp = self._map_row_to_response(result[0])
        current = OperationHistoryResponse(
            **base_resp.model_dump(),
            history=[]
        )

        history = []
        prev_id = current.previous
        while prev_id is not None:
            prev_query = (
                Query.from_(operation_table)
                .select("*")
                .where(operation_table.id == prev_id)
            )
            prev_result = run_query(self.engine, prev_query)
            if prev_result:
                p_resp = self._map_row_to_response(prev_result[0])
                history.append(p_resp)
                prev_id = p_resp.previous
            else:
                prev_id = None

        current.history = history
        return current

    def list_operations(
        self, operation_type: Optional[OperationType] = None
    ) -> List[OperationResponse]:
        query = Query.from_(operation_table).select("*")
        if operation_type:
            query = query.where(operation_table.operation_type == operation_type.value)

        result = run_query(self.engine, query)

        ops = []
        if result:
            for row in result:
                ops.append(self._map_row_to_response(row))
        return ops
