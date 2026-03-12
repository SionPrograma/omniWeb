import asyncio
import logging
from backend.core.ai_host.command_router import CommandRouter
from backend.core.education_engine.skill_tracker import skill_tracker
from backend.core.education_engine.certification_engine import certification_engine
from backend.core.permissions import set_chip_context

async def main():
    router = CommandRouter()
    user_id = "test_user_mentor"
    
    with set_chip_context("core"):
        # 1. Test conversational interaction
        print("Testing Learning request...")
        response = await router.route("enseñame sobre thermodynamics", modality="text")
        print(f"AI Response: {response.message}")
        
        # 2. Test evaluation
        print("\nTesting Knowledge Evaluation...")
        from backend.core.education_engine.knowledge_evaluator import knowledge_evaluator
        eval_res = await knowledge_evaluator.evaluate_mastery("Thermodynamics", "Thermodynamics is a branch of physics that deals with heat and temperature.")
        print(f"Evaluation Feedback: {eval_res['feedback']}")
        
        # 3. Check profile
        profile = skill_tracker.get_user_profile()
        print(f"\nUser Profile Skills: {[s.concept for s in profile[:3]]}")
        
        # 4. Certification check
        # Force mastery for certification test
        skill_tracker.update_skill("Thermodynamics", level_boost=1.0)
        certs = certification_engine.check_for_certifications(user_id)
        print(f"New Certifications: {[c.title for c in certs]}")

if __name__ == "__main__":
    asyncio.run(main())
