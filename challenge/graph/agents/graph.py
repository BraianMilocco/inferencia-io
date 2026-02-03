import logging
from langgraph.graph import StateGraph, END
from graph.agents.state import VideoAnalysisState

from .nodes import extraction_node, sentiment_analysis_node, structuring_node

logger = logging.getLogger(__name__)


def should_continue(
    state: VideoAnalysisState, status_end: list[str] = ["failed", "skipped"]
) -> str:
    """Decides whether to continue based on the state"""
    logger.info(
        "Checking continuation",
        extra={"status": state.get("status"), "errors": state.get("errors")},
    )
    if state.get("errors") or state.get("status") in status_end:
        return "end"
    return "continue"


# Even though both functions below do almost the same, they are separated for clarity and future modifications/customization
def should_continue_after_extraction(state: VideoAnalysisState) -> str:
    """Decides whether to continue after the extraction node"""
    return should_continue(state)


def should_continue_after_sentiment(state: VideoAnalysisState) -> str:
    """Decides whether to continue after the sentiment analysis node"""
    return should_continue(state)


###############################################################################


def create_video_analysis_graph():
    """
    Creates and compiles the video analysis graph.

    Flow:
    START -> extraction -> sentiment_analysis -> structuring -> END
    """
    logger.info("Creating video analysis graph")
    # Create the state graph
    workflow = StateGraph(VideoAnalysisState)

    # Add nodes
    workflow.add_node("extraction", extraction_node)
    workflow.add_node("sentiment_analysis", sentiment_analysis_node)
    workflow.add_node("structuring", structuring_node)

    # Set entry point
    workflow.set_entry_point("extraction")

    # Connect nodes with error handling
    workflow.add_conditional_edges(
        "extraction",
        should_continue_after_extraction,
        {"continue": "sentiment_analysis", "end": END},
    )

    workflow.add_conditional_edges(
        "sentiment_analysis",
        should_continue_after_sentiment,
        {"continue": "structuring", "end": END},
    )

    workflow.add_edge("structuring", END)

    # Compile the graph
    graph = workflow.compile()
    logger.info("Video analysis graph compiled")
    return graph
