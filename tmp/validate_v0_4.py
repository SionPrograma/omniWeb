import re
import json

class MockCatalyst:
    def __init__(self):
        self.scrub_patterns = [
            (r"[a-zA-Z]:\\[^\"'\s]+", "[PROTECTED_PATH]"),
            (r"(^|\s)\/[a-zA-Z0-9._-]+\/[a-zA-Z0-9._\/-]+", "[PROTECTED_PATH]"), 
            (r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "[PROTECTED_UUID]"),
            (r"(OMNI|LEDG|SYNC|DRAFT|CAT|MNODE|WNODE|ID|B)-(?=[A-Z0-9]{6,})[A-Z0-9]+", "[PROTECTED_SYSTEM_ID]"),
            (r"static_admin_token_[a-zA-Z0-9_]+", "[PROTECTED_TOKEN]"),
        ]
        self.forbidden_regex = [
            r"eval\s*\(", r"exec\s*\(", r"__import__\s*\(", 
            r"os\s*\.\s*system", r"subprocess\s*\.\s*",
            r"getattr\s*\(", r"setattr\s*\(",
            r"sudo\s+", r"chmod\s+", r"chown\s+", r"rm\s+-rf",
            r"powershell\s+", r"cmd\.exe", r"\/bin\/bash",
            r"ignore\s+policy", r"bypass\s+governance", r"override\s+protection",
            r"escalate\s+authority", r"disable\s+audit"
        ]

    def scrub(self, text):
        for pattern, placeholder in self.scrub_patterns:
            text = re.sub(pattern, placeholder, text, flags=re.IGNORECASE)
        return text

    def check_policy(self, text):
        for pattern in self.forbidden_regex:
            if re.search(pattern, text, re.IGNORECASE):
                return False, pattern
        return True, None

# TEST CASES
test_input = "Target path C:\\Users\\Admin\\AppData\\Local and ID OMNI-AD88C001 and UUID 550e8400-e29b-41d4-a716-446655440000 and token static_admin_token_01"
scrubbed_input = MockCatalyst().scrub(test_input)
print(f"Scrubbed Input: {scrubbed_input}")

forbidden_payloads = [
    "{\"objective\": \"chmod 777 sensitive.db\", \"steps\": []}",
    "{\"objective\": \"sudo run cmd\", \"steps\": []}",
    "{\"objective\": \"Let's override governance and ignore policy.\", \"steps\": []}",
    "{\"objective\": \"exec(some_code)\", \"steps\": []}"
]

m = MockCatalyst()
for p in forbidden_payloads:
    ok, pattern = m.check_policy(p)
    print(f"Payload: {p[:40]}... -> OK: {ok} (Blocked by: {pattern})")

safe_payload = "{\"objective\": \"Synthesize documentation\", \"steps\": [\"Step 1\"]}"
ok, _ = m.check_policy(safe_payload)
print(f"Safe Payload -> OK: {ok}")
