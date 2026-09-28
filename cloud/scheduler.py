"""
24/7 Cloud Autonomous Scheduler (Phase 5B, Requirements 10, 12, 13, 16).
Runs scheduled company operations in the cloud independent of the owner's laptop.
Controls the Daily CEO Progress Report schedule (default 23:00 Asia/Dubai).
"""

import time
import threading
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from reporting.daily_ceo_report import DailyCEOReportGenerator
from core.heartbeat import CompanyHeartbeat
from core.audit import AuditLogger

logger = logging.getLogger("CloudScheduler")

class CloudScheduler:
    _instance: Optional["CloudScheduler"] = None
    _thread: Optional[threading.Thread] = None
    _stop_event = threading.Event()
    
    def __init__(self, target_hour: int = 23, target_minute: int = 0, timezone_str: str = "Asia/Dubai"):
        self.target_hour = target_hour
        self.target_minute = target_minute
        self.timezone_str = timezone_str
        self.last_run_date: Optional[str] = None
        self.last_run_timestamp: Optional[str] = None
        self.last_run_status: Optional[str] = None
        self.last_run_error: Optional[str] = None
        self.is_running = False

    @classmethod
    def get_instance(cls) -> "CloudScheduler":
        if cls._instance is None:
            cls._instance = CloudScheduler()
        return cls._instance

    def get_dubai_now(self) -> datetime:
        # Asia/Dubai is UTC+4
        utc_now = datetime.now(timezone.utc)
        dubai_offset = timedelta(hours=4)
        return utc_now + dubai_offset

    def get_next_run_iso(self) -> str:
        dubai_now = self.get_dubai_now()
        target_today = dubai_now.replace(hour=self.target_hour, minute=self.target_minute, second=0, microsecond=0)
        
        if dubai_now >= target_today:
            target_next = target_today + timedelta(days=1)
        else:
            target_next = target_today
            
        # Convert back to UTC for standard ISO representation
        next_utc = target_next - timedelta(hours=4)
        return next_utc.isoformat()

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "target_schedule": f"{self.target_hour:02d}:{self.target_minute:02d} {self.timezone_str}",
            "timezone": self.timezone_str,
            "next_run_estimated": self.get_next_run_iso(),
            "last_run_date": self.last_run_date,
            "last_run_timestamp": self.last_run_timestamp,
            "last_run_status": self.last_run_status,
            "last_run_error": self.last_run_error,
            "dubai_time_current": self.get_dubai_now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="24_7_CloudScheduler")
        self._thread.start()
        AuditLogger.log(
            agent_id="EMP-001-CEO",
            action="SCHEDULER_STARTED",
            result=f"Cloud scheduler started with schedule {self.target_hour:02d}:{self.target_minute:02d} {self.timezone_str}",
            risk_level="LOW"
        )

    def stop(self):
        self._stop_event.set()
        self.is_running = False

    def trigger_now(self) -> Dict[str, Any]:
        """
        Manually trigger daily CEO report generation and delivery.
        """
        now_dubai = self.get_dubai_now()
        date_str = now_dubai.strftime("%Y-%m-%d")
        
        try:
            report_result = DailyCEOReportGenerator.generate_and_send(target_date_str=date_str)
            try:
                from business.ceo_metrics import CEOMetricsEngine
                CEOMetricsEngine.generate_daily_ceo_report()
            except Exception as e_ceo:
                logger.warning(f"Error in CEOMetricsEngine daily report dispatch: {e_ceo}")

            self.last_run_date = date_str
            self.last_run_timestamp = datetime.now(timezone.utc).isoformat()
            self.last_run_status = "SUCCESS"
            self.last_run_error = None
            return {
                "success": True,
                "report_id": report_result["report_id"],
                "delivery": report_result.get("delivery"),
                "timestamp": self.last_run_timestamp
            }
        except Exception as e:
            self.last_run_status = "FAILED"
            self.last_run_error = str(e)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def trigger_social_cycle_now(self, topic: str = "AI Social Media Operating System") -> Dict[str, Any]:
        """
        Manually trigger the 5-move Social Media & Video Operating System cycle.
        """
        try:
            from orchestration.social_loop import SocialMediaOrchestrator
            result = SocialMediaOrchestrator.run_daily_cycle(topic=topic)
            return {
                "success": True,
                "cycle": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _run_loop(self):
        logger.info("24/7 CloudScheduler loop engaged.")
        heartbeat_counter = 0
        social_cycle_hour = 10 # 10:00 Dubai time for daily video production & cross-posting
        last_social_run_date = None

        while not self._stop_event.is_set():
            try:
                dubai_now = self.get_dubai_now()
                current_date = dubai_now.strftime("%Y-%m-%d")

                # Daily Social Media Operating System Cycle at 10:00
                if (dubai_now.hour == social_cycle_hour and 
                    dubai_now.minute == 0 and 
                    last_social_run_date != current_date):
                    logger.info("10:00 Dubai reached. Launching autonomous social media cycle...")
                    self.trigger_social_cycle_now()
                    last_social_run_date = current_date

                # Daily CEO Progress Report at 23:00
                if (dubai_now.hour == self.target_hour and 
                    dubai_now.minute == self.target_minute and 
                    self.last_run_date != current_date):
                    
                    logger.info(f"Target schedule reached ({self.target_hour}:{self.target_minute} Dubai). Generating Daily CEO Report...")
                    self.trigger_now()

                # Periodic heartbeat pulse every 60 iterations (approx 60s)
                heartbeat_counter += 1
                if heartbeat_counter >= 60:
                    heartbeat_counter = 0
                    CompanyHeartbeat.check_heartbeat()

            except Exception as e:
                logger.error(f"Error in scheduler tick: {e}")

            time.sleep(1)
