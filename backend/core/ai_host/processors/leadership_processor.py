from typing import Dict, Any, Optional
import logging
from .base import CommandProcessor, AICommandResponse
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class LeadershipProcessor(CommandProcessor):
    """
    OMNIWEB LEADERSHIP ONBOARDING SYSTEM
    Handles the intelligent onboarding protocol for Beta Testers.
    """
    
    ONBOARDING_STEPS = {
        1: {
            "title": "Welcome to OmniWeb Mission",
            "intent": "leadership_welcome",
            "content": (
                "OmniWeb is more than a platform; it's a living ecosystem designed to connect learning, "
                "collaboration, and opportunity. You were selected as a Beta Tester because of your "
                "potential to lead in this new digital frontier. Our mission is to scale human potential "
                "through collective intelligence."
            )
        },
        2: {
            "title": "The Beta Tester Role",
            "intent": "leadership_role",
            "content": (
                "As a Beta Tester, you are a pioneer. \n\n"
                "**Allowed**: Explore 모든 chips, document findings, and help fellow users. \n"
                "**Expected**: Provide constructive friction—break things so we can fix them. \n"
                "**NOT Allowed**: Malicious exploitation or sharing of unreleased core protocols."
            )
        },
        3: {
            "title": "Evaluation System",
            "intent": "leadership_evaluation",
            "content": (
                "Your progress is tracked via transparent metrics: \n"
                "• **Activity**: Frequency and depth of system usage.\n"
                "• **Feedback**: Quality and clarity of your suggestions.\n"
                "• **Reporting**: Precision in identifying anomalies (bugs).\n"
                "• **Citizenship**: Constructive behavior in community spaces."
            )
        },
        4: {
            "title": "The Evolutionary Path",
            "intent": "leadership_evolution",
            "content": (
                "Your journey in OmniWeb is dynamic:\n"
                "User → **Beta Tester** (You) → Admin Candidate → Admin\n\n"
                "Promotion is decided by the Creator based on your performance metrics. "
                "Consistency in feedback and community help is key."
            )
        },
        5: {
            "title": "Introduction Training",
            "intent": "leadership_pitch",
            "content": (
                "When introducing OmniWeb, use this simple speech: \n\n"
                "*'OmniWeb is a platform designed to connect learning, collaboration, knowledge, and "
                "opportunity in a single ecosystem. We are currently testing the system before public release.'*"
            )
        },
        6: {
            "title": "Tester Guidance",
            "intent": "leadership_focus",
            "content": (
                "Focus your current efforts on: \n"
                "1. Exploring every available Chip.\n"
                "2. Identifying UI/UX improvements.\n"
                "3. Helping new users understand the shell.\n"
                "4. Testing the bounds of the AI Host's reasoning."
            )
        },
        7: {
            "title": "Transition to Mentor Mode",
            "intent": "leadership_mentor",
            "content": (
                "Protocol complete. I am now transitioning to **Mentor Mode**. \n\n"
                "I will be here to answer any questions, guide your exploration, and help you "
                "discover hidden platform features. How can I help you begin your deep dive?"
            )
        },
        8: {
            "title": "Governance Foundation",
            "intent": "governance_intro",
            "content": (
                "OmniWeb is governed by its users. In the future, as an Admin Candidate, you will "
                "participate in protocol votes and conflict resolution. Responsible onboarding is "
                "the first step: ensuring new users understand the ethical use of the knowledge market."
            )
        },
        9: {
            "title": "Community Management",
            "intent": "community_intro",
            "content": (
                "A leader in OmniWeb manages the 'vibe' as much as the code. You will learn to "
                "identify toxic patterns and promote collaborative ones. The AI Host assists by "
                "summarizing sentiment trends across the mesh."
            )
        },
        10: {
            "title": "Final Onboarding Milestone",
            "intent": "leadership_terminal",
            "content": (
                "You have completed the initial Leadership Protocol. Your status is now 'Senior Beta Tester'. "
                "Keep contributing feedback and guiding others. The Creator monitors this space closely. "
                "Welcome to the inner circle."
            )
        }
    }

    async def can_handle(self, command: str) -> bool:
        """Determines if the command is part of the leadership onboarding flow."""
        # Prioritize if user is in an active onboarding session
        keywords = ["encantado", "listo", "ready", "next", "siguiente", "continuar", "continue", "who am i", "role", "mission", "governance", "admin"]
        return any(k in command.lower() for k in keywords)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        user_id = context.get("user_id", "default_user") if context else "default_user"
        from backend.core.user_memory_timeline.manager import timeline_manager
        
        # Get current step
        step = self._get_current_step(user_id)
        
        # If user says "ready" or "next" or similar, move to next step
        if any(k in msg.lower() for k in ["ready", "next", "listo", "siguiente", "entendido", "continuar", "continue"]):
            # Only increment if not finished or if they are explicitly moving forward
            if step <= 10:
                step += 1
                self._update_step(user_id, step)
                
                # Record milestone in timeline
                if step in self.ONBOARDING_STEPS:
                    timeline_manager.record_milestone(
                        user_id=user_id,
                        milestone_type="onboarding_progress",
                        description=f"Reached onboarding step {step}: {self.ONBOARDING_STEPS[step]['title']}"
                    )

        if step in self.ONBOARDING_STEPS:
            data = self.ONBOARDING_STEPS[step]
            
            # Protocol Step 8: Hidden Skill Detection
            skill_note = self._detect_skills(user_id, msg, step)

            # Protocol Step 9: Adaptive Personalization (Add custom insights based on previous interactions)
            adaptive_insight = self._get_adaptive_insight(user_id, step)

            return AICommandResponse(
                intent=data["intent"],
                status="success",
                message=f"### {data['title']}\n\n{data['content']}{skill_note}{adaptive_insight}\n\n*Type 'continue' to proceed.*",
                payload={"step": step, "onboarding": True}
            )
        
        # Mark completion if step 11
        if step == 11:
             timeline_manager.record_milestone(user_id, "onboarding_complete", "Completed leadership onboarding protocol.")
             from backend.core.governance.manager import governance_manager
             governance_manager.record_interaction("system", user_id, "onboarding_complete", trust_score=0.5)

        # Default fallback to Mentor Mode if step exceeds initial onboarding
        return AICommandResponse(
            intent="mentor_mode",
            status="success",
            message=(
                "You are now in **Mentor Mode**. Based on your interaction patterns, I've flagged your "
                "analytical and communication skills for the Creator. I'm ready to help you discover "
                "platform features or deep-dive into governance. What's on your mind?"
            ),
            payload={"mode": "mentor"}
        )

    def _detect_skills(self, user_id: str, msg: str, step: int) -> str:
        """Logic for Protocol Step 8: Hidden Skill Detection."""
        from backend.core.user_memory_timeline.manager import timeline_manager
        note = ""
        # 1. Analytical Thinking (Long, structured messages)
        if len(msg) > 50 and any(k in msg for k in ["porque", "porque", "due to", "implies"]):
            note = "\n\n✨ **Hidden Strength Detected**: *Analytical Thinking*. You tend to look for underlying causes."
            timeline_manager.record_milestone(user_id, "hidden_skill", "Analytical Thinking detected.", metadata={"trigger": msg})
        
        # 2. Leadership Potential (Decisive language)
        elif any(k in msg for k in ["hagamos", "let's", "goal", "mission", "objective"]):
             note = "\n\n✨ **Hidden Strength Detected**: *Leadership Potential*. You focus on mission and collective action."
             timeline_manager.record_milestone(user_id, "hidden_skill", "Leadership Potential detected.", metadata={"trigger": msg})
        
        # 3. Technical Curiosity (Asking how things work)
        elif any(k in msg for k in ["cómo", "how", "protocol", "architecture", "code"]):
             note = "\n\n✨ **Hidden Strength Detected**: *Technical Curiosity*. You have a natural drive to understand the core engine."
             timeline_manager.record_milestone(user_id, "hidden_skill", "Technical Curiosity detected.", metadata={"trigger": msg})
             
        return note

    def _get_adaptive_insight(self, user_id: str, step: int) -> str:
        """Logic for Protocol Step 9: Adaptive Personalization."""
        if step == 7:
             return "\n\n💡 **Adaptive Path**: *Based on your interests, I've prioritized the 'Knowledge Mesh' chip for your exploration.*"
        return ""

    def _get_current_step(self, user_id: str) -> int:
        try:
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT step_reached FROM onboarding_analytics WHERE user_id = ?", (user_id,)).fetchone()
                return row["step_reached"] if row else 1
        except:
            return 1

    def _update_step(self, user_id: str, step: int):
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO onboarding_analytics (user_id, step_reached)
                    VALUES (?, ?)
                """, (user_id, step))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update onboarding step: {e}")

leadership_processor = LeadershipProcessor()
