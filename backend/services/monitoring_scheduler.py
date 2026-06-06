import logging
import uuid
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from backend.config import settings
from backend.services.databases.postgres import AsyncSessionLocal, DBSubscription, DBAlert, DBCase
from backend.workflow.graph import run_screening_workflow
from backend.models.entity import EntityIntake

logger = logging.getLogger(__name__)

class MonitoringScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Monitoring APScheduler started.")
            # Schedule periodic job to check subscriptions
            # Every 10 minutes for testing/monitoring purposes
            self.scheduler.add_job(
                self.check_subscriptions,
                'interval',
                minutes=10,
                id='check_subscriptions_job',
                replace_existing=True
            )

    async def check_subscriptions(self):
        logger.info("Running scheduled check for monitoring subscriptions...")
        async with AsyncSessionLocal() as session:
            try:
                # Select active subscriptions that need checking
                # Check based on last_checked interval
                now = datetime.datetime.utcnow()
                query = select(DBSubscription).where(
                    DBSubscription.is_active == True
                )
                result = await session.execute(query)
                subscriptions = result.scalars().all()
                
                for sub in subscriptions:
                    # Determine if check is due
                    time_elapsed = now - sub.last_checked
                    is_due = False
                    if sub.frequency == 'Daily' and time_elapsed >= datetime.timedelta(days=1):
                        is_due = True
                    elif sub.frequency == 'Weekly' and time_elapsed >= datetime.timedelta(weeks=1):
                        is_due = True
                    elif sub.frequency == 'One-time':
                        is_due = False # Handled synchronously at screening
                    
                    if is_due or settings.ENVIRONMENT == "development": # always run in dev mode for testing
                        await self.process_monitoring_update(sub, session)
                
                await session.commit()
            except Exception as e:
                logger.error(f"Error checking monitoring subscriptions: {e}")
                await session.rollback()

    async def process_monitoring_update(self, sub: DBSubscription, session):
        logger.info(f"Processing monitoring check for target: {sub.entity_name}")
        # Build EntityIntake model
        entity_intake = EntityIntake(
            name=sub.entity_name,
            entity_type=sub.entity_type,
            country=sub.country,
            industry=sub.industry,
            website=sub.website,
            registration_number=sub.registration_number
        )
        
        # Run standard screening pipeline
        try:
            workflow_result = await run_screening_workflow(entity_intake, monitoring_frequency=sub.frequency)
            new_score = workflow_result.get("risk_score", 0)
            
            # Fetch latest case for this entity name to compare risk score
            case_query = select(DBCase).where(
                DBCase.entity_name == sub.entity_name
            ).order_by(DBCase.created_at.desc()).limit(1)
            
            case_result = await session.execute(case_query)
            last_case = case_result.scalar_one_or_none()
            
            # Update subscription last checked timestamp
            sub.last_checked = datetime.datetime.utcnow()
            
            # If there was a previous case and the risk score has changed or if new articles were found, raise alert
            if last_case:
                old_score = last_case.risk_score
                if new_score != old_score:
                    # Create Alert
                    alert_id = str(uuid.uuid4())
                    alert = DBAlert(
                        id=alert_id,
                        subscription_id=sub.id,
                        case_id=workflow_result.get("case_id"),
                        alert_type="Risk Score Change",
                        description=f"Monitoring Alert: Risk score for {sub.entity_name} changed from {old_score} to {new_score}.",
                        severity="HIGH" if new_score > 50 else "MEDIUM",
                        is_read=False,
                        created_at=datetime.datetime.utcnow()
                    )
                    session.add(alert)
                    logger.info(f"Generated Risk Score Change Alert for {sub.entity_name} (ID: {alert_id})")
            else:
                # First check, generate new alert
                alert_id = str(uuid.uuid4())
                alert = DBAlert(
                    id=alert_id,
                    subscription_id=sub.id,
                    case_id=workflow_result.get("case_id"),
                    alert_type="New Article",
                    description=f"Monitoring Alert: Initial screening completed for monitored entity {sub.entity_name}.",
                    severity="LOW",
                    is_read=False,
                    created_at=datetime.datetime.utcnow()
                )
                session.add(alert)
                logger.info(f"Generated Initial Screening Alert for {sub.entity_name} (ID: {alert_id})")
        except Exception as e:
            logger.error(f"Failed to process monitoring update for {sub.entity_name}: {e}")

monitoring_scheduler = MonitoringScheduler()
