from datetime import datetime

from app.core.config import get_settings


def format_order_number(sequence: int) -> str:
    settings = get_settings()
    year = datetime.now().year
    return f"{settings.order_id_prefix}-{year}{sequence:04d}"
