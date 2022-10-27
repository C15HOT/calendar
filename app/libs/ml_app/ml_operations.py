from app.libs.ml_app.libs.priority import PriorityEstimator
from app.libs.ml_app.libs.transfer_variants import get_cancellations
from app.libs.ml_app.models.event import EventCalendar

def get_prority(text: str):
    return PriorityEstimator.get_text_priority(text)

async def get_transfer_variants(event: EventCalendar, user_id):
    result = await get_cancellations(event, user_id)
    return result
