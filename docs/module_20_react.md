# Module 20: React Debugging Dashboard

## 1. Concept
A React-based single-page application (SPA) acting as the primary user interface for the Software Debugging Agent.

## 2. Problem
CLI interfaces are great for quick operations, but debugging complex AI workflows requires high-density information display. We need to visualize agent reasoning, code diffs, logs, and timelines simultaneously in a way that terminal output cannot handle gracefully.

## 3. Why this project needs it
Our agent generates rich hypotheses and executes multiple steps in a LangGraph workflow. A React dashboard allows us to separate concerns: the backend handles the intelligence and execution (FastAPI + LangGraph), while the frontend focuses entirely on visualization (Timeline, Agent Graph, Diffs).

## 4. Alternatives
- Text-based UI (TUI) like Textual or Rich (Python) -> Hard to build responsive, rich media interfaces.
- Server-side rendered templates (Jinja2) -> Does not provide the dynamic, single-page experience required for streaming live agent status.

## 5. Decision
We chose Vite + React + TypeScript. Vite provides a fast development experience, React allows for component-based architecture which fits our modular dashboard design (Sidebar, Workspace, Agent Panel), and TypeScript provides type safety for our API responses. We used Vanilla CSS for the design system to ensure strict compliance with the customized AI/Developer aesthetic.

## 6. Implementation
- Bootstrapped using `create-vite`.
- Implemented a design system using CSS variables supporting Light and Dark modes.
- Built `AppLayout` for navigation.
- Created `Dashboard`, `Repositories`, and `Investigations` views to monitor and interact with the agent.
- Configured Vite proxy to route API requests to `http://localhost:8000`.

## 7. Integration
The frontend connects to the FastAPI backend implemented in Module 18. The proxy in `vite.config.ts` ensures that API calls like `fetch('/repositories/')` are automatically routed to the backend server.
