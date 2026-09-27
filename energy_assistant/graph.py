'''Two-tool LangGraph workflow.'''

from langchain_core.messages import SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .data import EnergyData


def build_graph(model, tools, data: EnergyData):
    prompt = (
        '''You are an energy assistant. Use calculate_total for energy questions and 
        generate_invoice for invoice requests. Choose one tool and pass inclusive dates 
        as YYYY-MM-DD. Dates without a year refer to the year in the available data. '''
        f"Available data: {data.first_date} through {data.last_date}. "
        "Ask for clarification when the request is unclear. Never calculate values yourself."
    )
    model = model.bind_tools(tools)

    def assistant(state):
        return {"messages": [model.invoke([SystemMessage(content=prompt), *state["messages"]])]}

    #Build the graph to connect assistant with tools and handle the flow of messages
    graph = StateGraph(MessagesState)
    graph.add_node("assistant", assistant)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "assistant")
    graph.add_conditional_edges("assistant", tools_condition)
    graph.add_edge("tools", END)
    return graph.compile()
