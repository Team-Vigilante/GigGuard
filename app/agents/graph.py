from langgraph.graph import StateGraph, END
from app.agents.state import GigGuardState
from app.agents.parser import parser_node

# ── Placeholder nodes ──────────────────────────────────────────
# Each node receives the full state, does its work, and returns
# an updated copy. For now they are all pass-through stubs.


def researcher_node(state: GigGuardState) -> GigGuardState:
    """
    Agent 2 — Legal Researcher (Person 2 owns this)
    Will query ChromaDB and assess case strength.
    """
    print(f"[researcher_node] parsed_data={state.get('parsed_data')}")
    return state


def drafter_node(state: GigGuardState) -> GigGuardState:
    """
    Agent 3 — Drafter (Person 2 owns this)
    Will generate multilingual grievance letter.
    """
    print(f"[drafter_node] legal_analysis={state.get('legal_analysis')}")
    return state


def navigator_node(state: GigGuardState) -> GigGuardState:
    """
    Agent 4 — Navigator (Person 4 owns this)
    Will file grievance and track escalation.
    """
    print(f"[navigator_node] grievance_letter={state.get('grievance_letter')}")
    return state


# ── Build the graph ────────────────────────────────────────────
def build_graph() -> StateGraph:
    graph = StateGraph(GigGuardState)

    # Register all 4 nodes
    graph.add_node("parser", parser_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("drafter", drafter_node)
    graph.add_node("navigator", navigator_node)

    # Wire them sequentially
    graph.set_entry_point("parser")
    graph.add_edge("parser", "researcher")
    graph.add_edge("researcher", "drafter")
    graph.add_edge("drafter", "navigator")
    graph.add_edge("navigator", END)

    return graph.compile()


# ── Export compiled graph ──────────────────────────────────────
gigguard_graph = build_graph()