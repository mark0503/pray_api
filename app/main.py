from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from app.handlers import router, check_status_pray


def get_application() -> FastAPI:
    application = FastAPI()
    application.include_router(router=router)
    return application


app = get_application()


@app.on_event("startup")
@repeat_every(seconds=60)  # 1 hour
def remove_expired_tokens_task() -> None:
    check_status_pray()
