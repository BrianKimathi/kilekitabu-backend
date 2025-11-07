"""
Keep Alive Scheduler
Pings the server every 7 minutes to prevent Render.com from spinning down
"""
import logging
import threading
import time
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeepAliveScheduler:
    """Scheduler to keep the server alive by pinging it periodically"""
    
    def __init__(self, base_url: str):
        """
        Initialize keep alive scheduler.
        
        Args:
            base_url: Base URL of the server (e.g., https://your-app.onrender.com)
        """
        self.base_url = base_url.rstrip('/')
        self.keep_alive_url = f"{self.base_url}/api/health/keep-alive"
        self.running = False
        self.thread = None
        self.interval_minutes = 7  # Ping every 7 minutes
    
    def start_scheduler(self):
        """Start the keep alive scheduler"""
        if self.running:
            logger.warning("Keep alive scheduler is already running")
            return
        
        logger.info("🚀 Starting keep alive scheduler...")
        logger.info(f"📡 Will ping: {self.keep_alive_url}")
        logger.info(f"⏰ Interval: Every {self.interval_minutes} minutes")
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("✅ Keep alive scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the keep alive scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Keep alive scheduler stopped")
    
    def _run_scheduler(self):
        """Main scheduler loop - pings server every 7 minutes"""
        # Wait 1 minute before first ping (to let server fully start)
        time.sleep(60)
        
        while self.running:
            try:
                self._ping_server()
                # Sleep for 7 minutes (420 seconds)
                time.sleep(self.interval_minutes * 60)
            except Exception as e:
                logger.error(f"Error in keep alive scheduler: {e}")
                # If error, wait 1 minute before retrying
                time.sleep(60)
    
    def _ping_server(self):
        """Ping the keep-alive endpoint"""
        try:
            logger.info(f"🔄 Pinging server to keep alive: {self.keep_alive_url}")
            response = requests.get(
                self.keep_alive_url,
                timeout=10,
                headers={'User-Agent': 'KileKitabu-KeepAlive/1.0'}
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Server ping successful: {response.status_code}")
            else:
                logger.warning(f"⚠️ Server ping returned status: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to ping server: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error pinging server: {e}")

