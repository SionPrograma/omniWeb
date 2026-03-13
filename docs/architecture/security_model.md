# Security Model: The Creator Fortress

OmniWeb is designed with a **Zero Trust Lifecycle** for creator-level tools while providing a secure workspace for users.

## Security Layers

### 1. Identity Layer
Supports universal login via OAuth providers (Google, GitHub, etc.). It manages sessions and user-specific isolation.

### 2. The Creator Security Fortress
The most sensitive systems (Code Control, System Auditor, Chip Generation) are protected by:
- **CREATOR_ID Verification**: Only the designated architect's ID can access administrative endpoints.
- **Trusted Device Registration**: Access to Creator Mode requires a signature from a verified device hardware ID.
- **Hardware-Level MFA**: Prevents unauthorized access even if session tokens are compromised.

### 3. Chip Capabilities
A granular permission system ensures chips only access what they need:
- `storage_read/write`
- `network_access`
- `user_logbook_access`
- `creator_tools_access` (Restricted)

## Audit Logging

Every sensitive action is recorded in the **Security Audit Trail**. This log is immutable and can be reviewed in real-time through the **Mission Control Security Tab**.

## Data Privacy

Personal data is isolated per user. In the Multi-user mode, cross-contamination is prevented by the `Workspace Manager`, which silos SQLite and local storage per `user_id`.
