from datetime import datetime
from app.constants.enums import ActivityAction, ActivitySubAction
from app.schemas.common import CamelModel


class ActivityLogResponse(CamelModel):
    id: int
    action: ActivityAction
    sub_action: ActivitySubAction
    created_on: datetime
