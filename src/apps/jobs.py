# from core.db import async_session
# from core.utils import logger


# async def job() -> None:
#     """
#     Perform a cron job.

#     This function is executed as a cron job. It may perform various tasks, including but not limited to checking
#     subscription status.

#     Returns:
#         None: This function does not return any meaningful value upon completion.
#     """
#     logger.info("Running cron job!")
#     async with async_session() as session:
#         async with session.begin():
#             await session.execute()
#     logger.info("Finished cron job!")
#     return None

from datetime import datetime, timedelta
from sqlalchemy import select, extract
import pytz

from apps.user.models import UserModel
from core.db import async_session, redis
from core.utils import logger

IST = pytz.timezone("Asia/Kolkata")

async def job(app) -> None:
    """
    Daily birthday cron job.
    Runs at configured time (ex: 4 PM IST).
    """

    logger.info("Running birthday cron job!")


    # # 🔒 Prevent multiple workers running same job
    # lock = await redis.set("birthday_cron_lock", "1", nx=True, ex=5)
    # if not lock:
    #     logger.info("Cron already running in another worker.")
    #     return

    async with async_session() as session:
        now = datetime.now(IST)
        today = now.date()

        stmt = select(UserModel).where(
            extract("month", UserModel.date_of_birth) == today.month,
            extract("day", UserModel.date_of_birth) == today.day,
            UserModel.is_deleted.is_(False)
        )

        result = await session.scalars(stmt)
        users = result.all()

        logger.info(f"Found {len(users)} birthday users")

        for user in users:

            redis_key = f"birthday_sent:{user.id}:{today}"

            already_sent = await redis.get(redis_key)

            if not already_sent:
                # 🎉 Replace this with real notification logic
                logger.info(f"Sending birthday notification to {user.first_name}")

                # expire at midnight
                midnight = IST.localize(
                        datetime.combine(today + timedelta(days=1), datetime.min.time())
                    )
                seconds_left = int((midnight - now).total_seconds())

                await redis.set(redis_key, "sent", ex=seconds_left)

    logger.info("Finished birthday cron job!")