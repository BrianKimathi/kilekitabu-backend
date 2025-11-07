import requests
import json
import os
import time
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import logging

logger = logging.getLogger(__name__)

class FCMV1Service:
    """FCM v1 Service using the new API"""
    
    def __init__(self, credentials_path, project_id):
        self.credentials_path = credentials_path
        self.project_id = project_id
        self.access_token = None
        self.token_expiry = None
        
    def _get_access_token(self):
        """Get access token for FCM v1 API"""
        try:
            if self.access_token and self.token_expiry and self.token_expiry > time.time():
                return self.access_token
                
            # Load service account credentials
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=['https://www.googleapis.com/auth/firebase.messaging']
            )
            
            # Refresh the token
            credentials.refresh(Request())
            
            self.access_token = credentials.token
            self.token_expiry = credentials.expiry.timestamp() if credentials.expiry else None
            
            logger.info("✅ FCM v1 access token obtained")
            return self.access_token
            
        except Exception as e:
            logger.error(f"❌ Failed to get FCM v1 access token: {e}")
            return None
    
    def send_notification(self, fcm_token, title, body, data=None):
        """Send notification using FCM v1 API"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                logger.error("❌ No access token available")
                return False
            
            # FCM v1 API URL
            url = f"https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send"
            
            # Headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Simple message payload for debt notifications
            message = {
                "message": {
                    "token": fcm_token,
                    "notification": {
                        "title": title,
                        "body": body
                    },
                    "data": data or {},
                    "android": {
                        "priority": "high",
                        "notification": {
                            "icon": "ic_notification",
                            "color": "#0C57A6",
                            "sound": "default"
                        }
                    }
                }
            }
            
            logger.info(f"📤 Sending FCM v1 notification to: {fcm_token[:20]}...")
            logger.info(f"📋 Message: {json.dumps(message, indent=2)}")
            
            # Send request
            response = requests.post(url, headers=headers, json=message)
            
            logger.info(f"📊 FCM v1 Response Status: {response.status_code}")
            logger.info(f"📝 FCM v1 Response: {response.text}")
            
            if response.status_code == 200:
                logger.info("✅ FCM v1 notification sent successfully")
                return True
            else:
                logger.error(f"❌ FCM v1 notification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending FCM v1 notification: {e}")
            return False

# Mock service for when Firebase is not available
class MockFCMV1Service:
    def __init__(self, *args, **kwargs):
        pass
    
    def send_notification(self, fcm_token, title, body, data=None):
        logger.info(f"🔧 Mock FCM v1: Would send notification to {fcm_token[:20]}...")
        logger.info(f"📝 Title: {title}")
        logger.info(f"📄 Body: {body}")
        logger.info(f"📊 Data: {data}")
        return True
