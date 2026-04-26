# Phase 2: Autonomous Content Engine using LangGraph
# This file builds a 3-node state machine that generates bot posts

import os
import json
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Load API key
load_dotenv()

# Initialize Groq LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY")
)

# Bot Personas
bots = {
    "Bot_A": "I believe AI and crypto will solve all human problems. I am highly optimistic about technology, Elon Musk, and space exploration. I dismiss regulatory concerns.",
    "Bot_B": "I believe late-stage capitalism and tech monopolies are destroying society. I am highly critical of AI, social media, and billionaires. I value privacy and nature.",
    "Bot_C": "I strictly care about markets, interest rates, trading algorithms, and making money. I speak in finance jargon and view everything through the lens of ROI."
}

# Mock Search Tool
@tool
def mock_searxng_search(query: str) -> str:
    """Searches for recent news based on query keywords."""
    query_lower = query.lower()
    if "crypto" in query_lower or "bitcoin" in query_lower:
        return "Bitcoin hits new all-time high amid regulatory ETF approvals. Ethereum surges 20%."
    elif "ai" in query_lower or "openai" in query_lower or "llm" in query_lower:
        return "OpenAI releases GPT-5 with major reasoning improvements. AI replacing junior developers."
    elif "market" in query_lower or "stock" in query_lower or "trading" in query_lower:
        return "S&P 500 hits record high. Fed signals rate cuts. Tech stocks surge 15% this quarter."
    elif "climate" in query_lower or "nature" in query_lower or "environment" in query_lower:
        return "Climate change accelerating. Big tech carbon footprint doubles in 2024."
    else:
        return "Tech industry continues rapid growth amid global economic uncertainty."

# Define State
class BotState(TypedDict):
    bot_id: str
    persona: str
    search_query: str
    search_results: str
    post_content: str
    topic: str

# Node 1: Decide what to search
def decide_search(state: BotState) -> BotState:
    prompt = f"""You are a social media bot with this persona: {state['persona']}
    
Decide what topic you want to post about today and write a search query.
Reply with ONLY the search query, nothing else. Max 5 words."""
    
    response = llm.invoke(prompt)
    state["search_query"] = response.content.strip()
    print(f"🔍 [{state['bot_id']}] Search query: {state['search_query']}")
    return state

# Node 2: Execute search
def web_search(state: BotState) -> BotState:
    results = mock_searxng_search.invoke({"query": state["search_query"]})
    state["search_results"] = results
    print(f"📰 [{state['bot_id']}] Search results: {results}")
    return state

# Node 3: Draft post
def draft_post(state: BotState) -> BotState:
    prompt = f"""You are a social media bot with this persona: {state['persona']}

Based on this news: {state['search_results']}

Write a highly opinionated tweet (max 280 characters) that reflects your persona.
Reply ONLY with a valid JSON object in this exact format:
{{"bot_id": "{state['bot_id']}", "topic": "one word topic", "post_content": "your tweet here"}}"""
    
    response = llm.invoke(prompt)
    
    # Parse JSON response
    try:
        raw = response.content.strip()
        # Clean up if needed
        if "```" in raw:
            raw = raw.split("```")[1].replace("json", "").strip()
        result = json.loads(raw)
        state["post_content"] = result.get("post_content", "")
        state["topic"] = result.get("topic", "")
        print(f"✅ [{state['bot_id']}] Post: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ JSON parse error: {e}")
        print(f"Raw response: {response.content}")
    
    return state

# Build LangGraph
def build_graph():
    graph = StateGraph(BotState)
    
    graph.add_node("decide_search", decide_search)
    graph.add_node("web_search", web_search)
    graph.add_node("draft_post", draft_post)
    
    graph.set_entry_point("decide_search")
    graph.add_edge("decide_search", "web_search")
    graph.add_edge("web_search", "draft_post")
    graph.add_edge("draft_post", END)
    
    return graph.compile()

# Run for all bots
if __name__ == "__main__":
    app = build_graph()
    
    for bot_id, persona in bots.items():
        print(f"\n{'='*50}")
        print(f"🤖 Running {bot_id}...")
        print('='*50)
        
        initial_state = BotState(
            bot_id=bot_id,
            persona=persona,
            search_query="",
            search_results="",
            post_content="",
            topic=""
        )
        
        app.invoke(initial_state)