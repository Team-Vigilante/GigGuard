from langgraph.graph import StateGraph, END
from app.agents.state import GigGuardState
from app.agents.parser import parser_node
from app.agents.researcher_node import researcher_node
from app.agents.drafter_node import drafter_node
from app.agents.navigator import navigator_node


def build_graph() -> StateGraph:
    graph = StateGraph(GigGuardState)

    graph.add_node("parser", parser_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("drafter", drafter_node)
    graph.add_node("navigator", navigator_node)

    graph.set_entry_point("parser")
    graph.add_edge("parser", "researcher")
    graph.add_edge("researcher", "drafter")
    graph.add_edge("drafter", "navigator")
    graph.add_edge("navigator", END)

    return graph.compile()


gigguard_graph = build_graph()