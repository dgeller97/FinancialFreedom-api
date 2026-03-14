from .accounts import account_handlers
from .auth import auth_handlers
from .categories import category_handlers
from .transactions import transaction_handlers

route_handlers = [
    *auth_handlers,
    *account_handlers,
    *category_handlers,
    *transaction_handlers,
]
