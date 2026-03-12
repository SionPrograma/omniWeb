import logging
from typing import Dict, List, Optional
from .communication_models import CommunicationSession, Participant, SessionStatus, LanguageCode

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages real-time conversation sessions and participant lifecycles."""
    
    def __init__(self):
        self.sessions: Dict[str, CommunicationSession] = {}

    def create_session(self, title: str, creator: Participant) -> CommunicationSession:
        session = CommunicationSession(title=title)
        session.participants[creator.user_id] = creator
        self.sessions[session.id] = session
        logger.info(f"GlobalComm: Created session {session.id} - '{title}'")
        return session

    def join_session(self, session_id: str, participant: Participant) -> Optional[CommunicationSession]:
        if session_id in self.sessions:
            self.sessions[session_id].participants[participant.user_id] = participant
            logger.info(f"GlobalComm: User {participant.name} joined session {session_id}")
            return self.sessions[session_id]
        return None

    def leave_session(self, session_id: str, user_id: str):
        if session_id in self.sessions:
            if user_id in self.sessions[session_id].participants:
                del self.sessions[session_id].participants[user_id]
                logger.info(f"GlobalComm: User {user_id} left session {session_id}")
                
            if not self.sessions[session_id].participants:
                self.sessions[session_id].status = SessionStatus.CLOSED
                logger.info(f"GlobalComm: Session {session_id} closed (empty)")

    def get_active_sessions(self) -> List[CommunicationSession]:
        return [s for s in self.sessions.values() if s.status == SessionStatus.ACTIVE]

session_manager = SessionManager()
