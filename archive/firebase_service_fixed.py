"""
Firebase Service for Student Session Tracking
Replaces JSON file storage with cloud-based Firebase Firestore

FIXED VERSION - Improvements:
- Timezone consistency (uses pytz.utc throughout)
- Import optimization (moved to top of file)
- Firestore index error handling with Python fallback
- Better type annotations
"""
import os
import json
import pytz
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
_initialized = False
db = None

def init_firebase():
    """Initialize Firebase Admin SDK with credentials from environment."""
    global _initialized, db

    if _initialized:
        return db

    try:
        # Check if we're using a service account JSON file or environment variable
        firebase_creds_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        firebase_creds_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

        if firebase_creds_json:
            # Use JSON from environment variable (Railway)
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
        elif firebase_creds_path and os.path.exists(firebase_creds_path):
            # Use service account file (local development)
            cred = credentials.Certificate(firebase_creds_path)
        else:
            # Fallback: use default credentials (works on GCP)
            firebase_admin.initialize_app()
            db = firestore.client()
            _initialized = True
            return db

        # Initialize with credentials
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        _initialized = True

        print("[OK] Firebase initialized successfully")
        return db

    except Exception as e:
        print(f"[WARNING] Firebase initialization failed: {e}")
        print("[INFO] Falling back to local JSON storage")
        return None


class FirebaseTrackingService:
    """Service to manage student tracking data in Firebase Firestore."""

    def __init__(self):
        self.db = init_firebase()
        self.use_firebase = self.db is not None

        # Collection names
        self.USERS_COLLECTION = "users"
        self.SESSIONS_COLLECTION = "sessions"
        self.REPORTS_COLLECTION = "reports"
        self.CHAT_HISTORY_COLLECTION = "chat_history"

    def get_all_users(self) -> Dict[str, Any]:
        """Get all users from Firebase."""
        if not self.use_firebase:
            return {}

        try:
            users_ref = self.db.collection(self.USERS_COLLECTION)
            docs = users_ref.stream()
            return {doc.id: doc.to_dict() for doc in docs}
        except Exception as e:
            print(f"Error getting users: {e}")
            return {}

    def get_user(self, user_token: str) -> Optional[Dict[str, Any]]:
        """Get a specific user by token."""
        if not self.use_firebase:
            return None

        try:
            doc_ref = self.db.collection(self.USERS_COLLECTION).document(user_token)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Error getting user {user_token}: {e}")
            return None

    def save_user(self, user_token: str, user_data: Dict[str, Any]):
        """Save or update a user."""
        if not self.use_firebase:
            return

        try:
            doc_ref = self.db.collection(self.USERS_COLLECTION).document(user_token)
            doc_ref.set(user_data, merge=True)
        except Exception as e:
            print(f"Error saving user {user_token}: {e}")

    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all sessions from Firebase."""
        if not self.use_firebase:
            return {}

        try:
            sessions_ref = self.db.collection(self.SESSIONS_COLLECTION)
            docs = sessions_ref.stream()
            return {doc.id: doc.to_dict() for doc in docs}
        except Exception as e:
            print(f"Error getting sessions: {e}")
            return {}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session by ID."""
        if not self.use_firebase:
            return None

        try:
            doc_ref = self.db.collection(self.SESSIONS_COLLECTION).document(session_id)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            print(f"Error getting session {session_id}: {e}")
            return None

    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save or update a session."""
        if not self.use_firebase:
            return

        try:
            doc_ref = self.db.collection(self.SESSIONS_COLLECTION).document(session_id)
            doc_ref.set(session_data, merge=True)
        except Exception as e:
            print(f"Error saving session {session_id}: {e}")

    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Get all problem reports."""
        if not self.use_firebase:
            return []

        try:
            reports_ref = self.db.collection(self.REPORTS_COLLECTION)

            # Try with Firestore ordering (requires index)
            try:
                docs = reports_ref.order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as index_error:
                if "index" in str(index_error).lower():
                    print(f"[WARNING] Firestore index needed for reports ordering")
                    print(f"[INFO] Using Python sorting as fallback...")
                    # Fallback: get without ordering and sort in Python
                    docs = reports_ref.stream()
                    reports = [doc.to_dict() for doc in docs]
                    return sorted(reports, key=lambda x: x.get('timestamp', ''), reverse=True)
                else:
                    raise  # Re-raise if not an index error

        except Exception as e:
            print(f"Error getting reports: {e}")
            return []

    def save_report(self, report_data: Dict[str, Any]):
        """Save a problem report."""
        if not self.use_firebase:
            return

        try:
            reports_ref = self.db.collection(self.REPORTS_COLLECTION)
            reports_ref.add(report_data)
        except Exception as e:
            print(f"Error saving report: {e}")

    def get_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics from Firebase data."""
        if not self.use_firebase:
            return {}

        try:
            users = self.get_all_users()
            sessions = self.get_all_sessions()

            total_users = len(users)
            total_sessions = len(sessions)

            # Calculate additional stats
            module_counts = defaultdict(int)
            mode_counts = defaultdict(int)
            total_problems_solved = 0
            total_hints = 0
            total_why = 0

            for session in sessions.values():
                module_counts[session.get("module", "unknown")] += 1
                mode_counts[session.get("mode", "unknown")] += 1
                total_problems_solved += session.get("problems_solved", 0)
                total_hints += session.get("hints_requested", 0)
                total_why += session.get("why_requested", 0)

            return {
                "total_unique_users": total_users,
                "total_sessions": total_sessions,
                "total_problems_solved": total_problems_solved,
                "total_hints": total_hints,
                "total_why": total_why,
                "by_unit": dict(module_counts),
                "by_support_level": dict(mode_counts),
                "last_updated": datetime.now(pytz.utc).isoformat()  # ✅ FIXED: Added timezone
            }
        except Exception as e:
            print(f"Error generating summary: {e}")
            return {}

    def save_chat_message(self, session_id: str, message_data: Dict[str, Any]):
        """Save a chat message with timestamp."""
        if not self.use_firebase:
            return

        try:
            # ✅ FIXED: Add timezone-aware timestamp if not present
            if 'timestamp' not in message_data:
                message_data['timestamp'] = datetime.now(pytz.utc)

            chat_ref = self.db.collection(self.CHAT_HISTORY_COLLECTION)
            chat_ref.add({
                'session_id': session_id,
                'message': message_data,
                'created_at': message_data['timestamp']
            })
        except Exception as e:
            print(f"Error saving chat message: {e}")

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a specific session."""
        if not self.use_firebase:
            return []

        try:
            chat_ref = self.db.collection(self.CHAT_HISTORY_COLLECTION)

            # ✅ FIXED: Try with Firestore ordering (requires index), fallback to Python sorting
            try:
                query = chat_ref.where('session_id', '==', session_id).order_by('created_at')
                docs = query.stream()
                return [doc.to_dict().get('message', {}) for doc in docs]
            except Exception as index_error:
                if "index" in str(index_error).lower():
                    print(f"[WARNING] Firestore index needed for chat history ordering")
                    print(f"[INFO] Using Python sorting as fallback...")
                    # Fallback: get without ordering and sort in Python
                    query = chat_ref.where('session_id', '==', session_id)
                    docs = query.stream()
                    messages = [doc.to_dict().get('message', {}) for doc in docs]
                    # Sort by timestamp, with safe handling of missing timestamps
                    return sorted(messages, key=lambda m: m.get('timestamp', datetime.min.replace(tzinfo=pytz.utc)))
                else:
                    raise  # Re-raise if not an index error

        except Exception as e:
            print(f"Error getting chat history for session {session_id}: {e}")
            return []

    def cleanup_old_chat_history(self, days: int = 7):
        """Delete chat messages older than specified days (default: 7 days)."""
        if not self.use_firebase:
            return

        try:
            # ✅ FIXED: Use timezone-aware datetime
            cutoff_date = datetime.now(pytz.utc) - timedelta(days=days)
            chat_ref = self.db.collection(self.CHAT_HISTORY_COLLECTION)

            # Query for old messages
            old_messages = chat_ref.where('created_at', '<', cutoff_date).stream()

            # Delete in batches
            batch = self.db.batch()
            count = 0
            deleted_count = 0

            for doc in old_messages:
                batch.delete(doc.reference)
                count += 1
                deleted_count += 1

                # Commit batch every 500 operations (Firestore limit)
                if count >= 500:
                    batch.commit()
                    batch = self.db.batch()
                    count = 0

            # Commit any remaining deletions
            if count > 0:
                batch.commit()

            if deleted_count > 0:
                print(f"[CLEANUP] Deleted {deleted_count} chat messages older than {days} days")

        except Exception as e:
            print(f"Error cleaning up old chat history: {e}")
