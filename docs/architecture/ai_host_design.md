# AI Host: Design & Intent Orchestration

The **AI Host** is the primary interface for OmniWeb. It transforms the OS from a passive tool into an active collaborator.

## Architectural Design

The AI Host follows a **Processor-Registry Pattern**:

1.  **Command Ingestion**: Receives text or voice input.
2.  **Intent Classification**: The `CommandRouter` determines if the input is a system command, a knowledge query, or a chip-specific action.
3.  **Processor Delegation**: The command is handed off to specialized `CommandProcessor` instances.

### Key Processors

- **Knowledge Processor**: Queries the User Knowledge Graph.
- **Logbook Processor**: Manages personal entries and idea capture.
- **Permission Processor**: Explains and manages chip capabilities.
- **Healing Processor**: Interacts with the AutoFix engine to resolve system issues.

## Multimodal Bridge

The AI Host is not limited to text. The **Language Bridge** module enables:
- Real-time speech-to-text (STT) for hands-free operation.
- Multilingual translation and subtitles for international scaling.
- Text-to-speech (TTS) for eyes-busy scenarios.

## Cognitive Integration

The AI Host is deeply integrated with the **Long Term Memory** and **Actionable Insight Engine**. This allows it to:
- "Remember" previous interactions.
- Proactively suggest tasks based on detected patterns in the User Logbook.
- Context-switch between different project scopes (Chips) seamlessly.
