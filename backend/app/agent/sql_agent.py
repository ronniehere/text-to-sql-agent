from langchain_core.messages import AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from .llm import llm
from .tools import get_tools_for_session


def create_sql_agent(session_id: str):
    """Compile a LangGraph text-to-SQL agent bound to a session database."""
    session_tools = get_tools_for_session(session_id)
    db = session_tools["db"]
    tools = session_tools["tools"]
    get_schema_tool = session_tools["get_schema_tool"]
    get_schema_node = session_tools["get_schema_node"]
    run_query_tool = session_tools["run_query_tool"]
    run_query_node = session_tools["run_query_node"]

    def list_tables(state: MessagesState):
        tool_call = {
            "name": "sql_db_list_tables",
            "args": {},
            "id": "list_tables_1",
            "type": "tool_call",
        }
        tool_call_message = AIMessage(content="", tool_calls=[tool_call])
        list_tables_tool = next(t for t in tools if t.name == "sql_db_list_tables")
        tool_message = list_tables_tool.invoke(tool_call)
        response = AIMessage(f"Available tables: {tool_message.content}")
        return {"messages": [tool_call_message, tool_message, response]}

    def call_get_schema(state: MessagesState):
        llm_with_tools = llm.bind_tools([get_schema_tool], tool_choice="any")
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    generate_query_system_prompt = f"""You are an expert agent that converts a user's question into a syntactically correct {db.dialect} query.

Instructions:
1. Identify the entities and intent in the user's question.
2. For fuzzy text matches (names, titles), use case-insensitive LIKE with wildcards, e.g. WHERE LOWER(column) LIKE '%value%'.
3. Never use SELECT *. Only select columns needed to answer the question.
4. Unless the user asks otherwise, limit results to 5 rows.
5. Do not generate destructive DML (DELETE, DROP, TRUNCATE, ALTER). Prefer read-only SELECT queries.

Example (sample HR schema):

User: "Show employees in the Engineering department"

```sql
SELECT id, first_name, last_name, job_title, salary
FROM employees
WHERE LOWER(department) LIKE '%engineering%'
LIMIT 5;
```
"""

    def generate_query(state: MessagesState):
        system_message = {"role": "system", "content": generate_query_system_prompt}
        llm_with_tools = llm.bind_tools([run_query_tool])
        response = llm_with_tools.invoke([system_message] + state["messages"])
        return {"messages": [response]}

    check_query_system_prompt = f"""
You are a SQL expert with strong attention to detail.
Double-check the {db.dialect} query for common mistakes, including:
- NOT IN with NULL values
- UNION vs UNION ALL
- BETWEEN for exclusive ranges
- Data type mismatches in predicates
- Identifier quoting
- Wrong number of function arguments
- Incorrect casts
- Wrong join columns

If there are mistakes, rewrite the query. Otherwise reproduce it unchanged.
Then call the tool to execute the query.
"""

    def check_query(state: MessagesState):
        system_message = {"role": "system", "content": check_query_system_prompt}
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
            tool_call = last_message.tool_calls[0]
            user_message = {"role": "user", "content": tool_call["args"]["query"]}
            llm_with_tools = llm.bind_tools([run_query_tool], tool_choice="any")
            response = llm_with_tools.invoke([system_message, user_message])
            response.id = state["messages"][-1].id
            return {"messages": [response]}
        return {"messages": state["messages"]}

    def should_continue(state: MessagesState):
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
            return "check_query"
        return END

    builder = StateGraph(MessagesState)
    builder.add_node("list_tables", list_tables)
    builder.add_node("call_get_schema", call_get_schema)
    builder.add_node("get_schema", get_schema_node)
    builder.add_node("generate_query", generate_query)
    builder.add_node("check_query", check_query)
    builder.add_node("run_query", run_query_node)

    builder.add_edge(START, "list_tables")
    builder.add_edge("list_tables", "call_get_schema")
    builder.add_edge("call_get_schema", "get_schema")
    builder.add_edge("get_schema", "generate_query")
    builder.add_conditional_edges("generate_query", should_continue)
    builder.add_edge("check_query", "run_query")
    builder.add_edge("run_query", "generate_query")

    return builder.compile()


def run_sql_agent(query: str, session_id: str) -> str:
    """Run the text-to-SQL agent for a natural-language question."""
    try:
        agent = create_sql_agent(session_id)
        result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        return result["messages"][-1].content
    except ValueError as e:
        raise Exception(f"Session error: {str(e)}") from e
    except Exception as e:
        raise Exception(f"SQL agent error: {str(e)}") from e
