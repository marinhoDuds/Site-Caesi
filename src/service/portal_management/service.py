from datetime import date
from typing import List, Optional, Any
from pypika import Table, Query, Order
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
    """Service to handle business logic for the transparency portal operations.

    This service manages the creation, updating, retrieval, and listing of
    operations (artifacts). Updates are append-only to preserve history.

    Attributes
    ----------
    engine : Engine
        The SQLAlchemy engine used to connect to the database.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize a new PortalService.

        Parameters
        ----------
        engine : Engine
            The SQLAlchemy database engine instance.
        """
        self.engine = engine

    def _map_row_to_response(self, row: Any) -> OperationResponse:
        """Map a raw database row to an OperationResponse model.

        Parameters
        ----------
        row : Any
            The database row (usually a tuple or SQLAlchemy Row).

        Returns
        -------
        OperationResponse
            The mapped pydantic response model.
        """
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
        """Create a new transparency operation.

        Parameters
        ----------
        payload : OperationCreate
            The data to create the operation.

        Returns
        -------
        OperationResponse
            The newly created operation data.

        Raises
        ------
        Exception
            If the created operation cannot be fetched from the database.
        """
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
            .orderby("id", order=Order.desc)
            .limit(1)
        )
        result = run_query(self.engine, fetch_query)

        if result and len(result) > 0:
            return self._map_row_to_response(result[0])

        raise Exception("Failed to fetch created operation")

    def update_operation(
        self, previous_id: int, payload: OperationCreate
    ) -> OperationResponse:
        """Update an operation using an append-only strategy.

        This method does not overwrite the existing record. Instead, it creates
        a new record pointing to the old one via the 'previous' field.

        Parameters
        ----------
        previous_id : int
            The ID of the operation being updated.
        payload : OperationCreate
            The new data for the operation.

        Returns
        -------
        OperationResponse
            The newly created operation version data.

        Raises
        ------
        Exception
            If the updated operation cannot be fetched from the database.
        """
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
            .orderby("id", order=Order.desc)
            .limit(1)
        )
        result = run_query(self.engine, fetch_query)

        if result and len(result) > 0:
            return self._map_row_to_response(result[0])

        raise Exception("Failed to fetch created operation")

    def get_operation(self, operation_id: int) -> Optional[OperationHistoryResponse]:
        """Fetch a specific operation and its full modification history.

        Parameters
        ----------
        operation_id : int
            The ID of the operation to retrieve.

        Returns
        -------
        Optional[OperationHistoryResponse]
            The operation data including its historical versions, or None if not found.
        """
        query = (
            Query.from_(operation_table)
            .select("*")
            .where(operation_table.id == operation_id)
        )
        result = run_query(self.engine, query)

        if not result:
            return None

        base_resp = self._map_row_to_response(result[0])
        current = OperationHistoryResponse(**base_resp.model_dump(), history=[])

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
        """List transparency operations, optionally filtered by type.

        Parameters
        ----------
        operation_type : Optional[OperationType], optional
            The operation type to filter by, by default None.

        Returns
        -------
        List[OperationResponse]
            A list of operations matching the criteria.
        """
        query = Query.from_(operation_table).select("*")
        if operation_type:
            query = query.where(operation_table.operation_type == operation_type.value)

        result = run_query(self.engine, query)

        ops = []
        if result:
            for row in result:
                ops.append(self._map_row_to_response(row))
        return ops
