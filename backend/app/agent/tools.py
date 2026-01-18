from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import ToolNode
import redis

from app.agent.llm import llm
from app.config.settings import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True,
)


def get_db_for_session(session_id: str) -> SQLDatabase:
    """Resolve the SQLAlchemy database handle for a session."""
    db_uri = redis_client.get(f"db_uri:{session_id}")
    if not db_uri:
        raise ValueError(f"No database connection found for session {session_id}")
    return SQLDatabase.from_uri(db_uri)


def get_tools_for_session(session_id: str) -> dict:
    """Build LangChain SQL toolkit + ToolNodes for a session's database."""
    db = get_db_for_session(session_id)
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    tools = toolkit.get_tools()

    get_schema_tool = next(t for t in tools if t.name == "sql_db_schema")
    get_schema_node = ToolNode([get_schema_tool], name="get_schema")

    run_query_tool = next(t for t in tools if t.name == "sql_db_query")
    run_query_node = ToolNode([run_query_tool], name="run_query")

    return {
        "db": db,
        "tools": tools,
        "get_schema_tool": get_schema_tool,
        "get_schema_node": get_schema_node,
        "run_query_tool": run_query_tool,
        "run_query_node": run_query_node,
    }
