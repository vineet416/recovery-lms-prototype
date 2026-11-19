# Importing every model here lets create_all see all 7 tables.
from app.models.account import Account
from app.models.allocation_history import AllocationHistory
from app.models.call_log import CallLog
from app.models.office import Office
from app.models.payment import Payment
from app.models.ptp import Ptp
from app.models.user import User

__all__ = [
    "Account",
    "AllocationHistory",
    "CallLog",
    "Office",
    "Payment",
    "Ptp",
    "User",
]
