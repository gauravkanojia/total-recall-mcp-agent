"""
Audit repository.
"""

from app.database.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session):
        self.session = session

    async def create(
        self,
        *,
        tool_name: str,
        request_id: str,
        principal_id: str | None,
        status: str,
        error_message: str | None = None,
    ):

        audit = AuditLog(
            tool_name=tool_name,
            request_id=request_id,
            principal_id=principal_id,
            status=status,
            error_message=error_message,
        )

        self.session.add(audit)

        await self.session.flush()

        return audit
