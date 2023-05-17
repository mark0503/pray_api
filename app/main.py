from fastapi_utils.tasks import repeat_every

from app.core import get_application
from app.handlers import check_status_pray


app = get_application()


@app.on_event("startup")
@repeat_every(seconds=60)  # 1 hour
def remove_expired_tokens_task() -> None:
    check_status_pray()
