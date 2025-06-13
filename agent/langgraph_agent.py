import operator
from typing import TypedDict, Annotated, List, Dict, Optional
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from tools.quickcompare_tool import quickcompare_scraper
from agent.prompts import SYSTEM_PROMPT

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

class PriceComparisonAgent:
    """Agent class for price comparison using LangGraph and Gemini."""
    def __init__(self, google_api_key: str, model_name: str = "gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.3,
            google_api_key=google_api_key
        )
        self.tools = [quickcompare_scraper]
        self.tool_node = ToolNode(self.tools)
        self.app = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", self._call_llm)
        workflow.add_node("call_tool", self.tool_node)
        workflow.add_node("end_summary", lambda state: state)
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self._decide_next_step,
            {
                "call_tool": "call_tool",
                "end_summary": "end_summary"
            }
        )
        workflow.add_edge("call_tool", "agent")
        workflow.add_edge("end_summary", END)
        return workflow.compile()

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    async def _call_llm(self, state: AgentState) -> Dict[str, List[BaseMessage]]:
        messages = state["messages"]
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            system_message = HumanMessage(content=self._get_system_prompt())
            messages = [system_message] + messages
        llm_with_tools = self.llm.bind_tools(self.tools)
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    def _decide_next_step(self, state: AgentState) -> str:
        last_message = state["messages"][-1]
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "call_tool"
        else:
            return "end_summary"

    async def run(self, question: str) -> Optional[str]:
        inputs = {"messages": [HumanMessage(content=question)]}
        try:
            final_state = None
            async for step in self.app.astream(inputs):
                for key, value in step.items():
                    if key != "__end__":
                        final_state = value
                if "__end__" in step:
                    final_state = step["__end__"]
                    break
            if final_state and final_state.get("messages"):
                for message in reversed(final_state["messages"]):
                    if hasattr(message, 'content') and isinstance(message.content, str) and message.content.strip():
                        if not (hasattr(message, 'tool_calls') and message.tool_calls):
                            return message.content
                last_message = final_state["messages"][-1]
                if hasattr(last_message, 'content') and last_message.content:
                    return last_message.content
            return None
        except Exception as e:
            import logging
            logging.error(f"Error during agent execution: {e}")
            return None 