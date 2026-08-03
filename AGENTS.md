# Engineering Guidelines
The objective is to produce code that is maintainable, testable, extensible, and production-ready.

---

# 1. Follow SOLID Principles
Every implementation should follow the SOLID design principles.

* Each class should have a single responsibility.
* Modules should be open for extension and closed for modification.
* Derived classes should behave correctly wherever their base classes are used.
* Prefer small, focused interfaces over large, monolithic ones.
* Depend on abstractions rather than concrete implementations.

Avoid tightly coupled code.

---

# 2. Single Responsibility Components

Every component should perform one well-defined task.

Examples include:
* One service for document ingestion.
* One service for document parsing.
* One service for embedding generation.
* One service for vector storage.
* One service for retrieval.
* One service for LLM interaction.

Do not combine unrelated responsibilities into a single module.

---

# 3. Layered Architecture
Separate the application into logical layers.
Typical layers include:

* API
* Services
* Domain
* Repositories
* Infrastructure
* Configuration

Business logic must never reside inside API route handlers.

---

# 4. Dependency Injection
Dependencies should be injected rather than instantiated directly.
Avoid creating objects using constructors inside business logic whenever possible.
Use Constructor dependency injection. Do not use setter dependency injection.
---

# 5. Configuration Management
Never hardcode configuration values.
All configurable values must come from environment variables, including:
* API keys
* Database locations
* Model names
* Embedding model names
* Storage paths
* Chunk sizes
* Retrieval parameters
* Logging configuration
* Server configuration

Provide sensible defaults where appropriate.

---

# 6. Keep Functions Small
Functions should perform one clearly defined task.
Prefer readable code over clever implementations.
If a function becomes difficult to understand, split it into smaller functions.

---

# 7. Strong Typing
Use Python type hints throughout the project.
Public methods should define:
* Parameter types
* Return types
Avoid using `Any` unless absolutely necessary.

---

# 8. Meaningful Naming

Choose descriptive names.
Names should clearly communicate intent.
Avoid abbreviations unless they are widely accepted.

---

# 9. Error Handling

Handle expected failures gracefully.
Do not silently ignore exceptions.
Return meaningful error messages.
Log unexpected failures.
Never expose internal implementation details to API consumers.

---

# 10. Logging

Use structured logging.
Log important events including:

* Document uploads
* Processing stages
* Retrieval operations
* LLM requests
* Errors
* Performance metrics

Avoid excessive logging.
Never log secrets or sensitive information.

---

# 11. Performance
Avoid unnecessary computation.
Reuse expensive resources whenever possible.
Minimize repeated model loading.

Design for efficient retrieval.

---

# 12. Code Reuse
Avoid duplicated logic.
Extract reusable functionality into shared components.
Follow the DRY (Don't Repeat Yourself) principle.

---

# 13. Testing
New functionality should be designed to be testable.
Prefer modular code that can be unit tested independently.
Avoid tightly coupling business logic with external services.
---

# 14. Documentation
Document all public classes and methods.
Complex logic should include concise explanations describing *why* the implementation exists, rather than *what* the code does.

---

# 15. Security

Treat all external input as untrusted.

Validate user input before processing.

Never expose secrets in source code.

Never commit credentials to version control.

---

# 16. Maintainability

Optimize for readability over brevity.

Future contributors should be able to understand the implementation with minimal effort.

Code should be easy to modify without introducing regressions.

---

# 17. Consistency

Follow the existing project structure and coding style.

Reuse existing abstractions before introducing new ones.

Avoid multiple implementations of the same concept.

---

# 18. Incremental Development

Implement features in small, verifiable steps.

Ensure each completed step leaves the application in a working state before moving to the next feature.

Avoid partially implemented functionality.

---

# Guiding Principle

Every implementation should prioritize clarity, maintainability, extensibility, correctness, and simplicity over clever or overly complex solutions.


# Project Structure

Unless instructed otherwise, follow this repository layout.

app/
    api/
    core/
    services/
    repositories/
    models/
    schemas/
    utils/

tests/
docs/
scripts/