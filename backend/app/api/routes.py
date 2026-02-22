from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_community.utilities import SQLDatabase
from sqlalchemy import MetaData, create_engine, inspect, select
import redis

from app.agent.sql_agent import run_sql_agent
from app.config.settings import settings

router = APIRouter()
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=settings.REDIS_PASSWORD or None,
    decode_responses=True,
)


def get_db_uri_from_session(session_id: str) -> str:
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID not provided")
    db_uri = redis_client.get(f"db_uri:{session_id}")
    if not db_uri:
        raise HTTPException(
            status_code=400,
            detail="No database connection established for this session",
        )
    return db_uri


class DBConnectRequest(BaseModel):
    db_uri: str
    session_id: str


class SessionRequest(BaseModel):
    session_id: str


class TableRequest(BaseModel):
    session_id: str
    table_name: str


class QueryRequest(BaseModel):
    query: str
    session_id: str


class QueryResponse(BaseModel):
    answer: str


@router.post("/connect-db")
async def connect_db(request: DBConnectRequest):
    """Validate a SQLAlchemy URI and bind it to the session (24h TTL in Redis)."""
    try:
        db = SQLDatabase.from_uri(request.db_uri)
        db.run("SELECT 1")
        redis_client.set(f"db_uri:{request.session_id}", request.db_uri, ex=24 * 60 * 60)
        return {"message": "Database connection established"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Database connection failed")


@router.post("/disconnect-db")
async def disconnect_db(request: SessionRequest):
    """Drop the session's stored database URI."""
    try:
        redis_client.delete(f"db_uri:{request.session_id}")
        return {"message": "Database disconnected"}
    except Exception:
        raise HTTPException(status_code=400, detail="Database disconnection failed")


@router.post("/db-tables")
async def list_tables(request: SessionRequest):
    """List table names in the session database."""
    try:
        db_uri = get_db_uri_from_session(request.session_id)
        engine = create_engine(db_uri)
        inspector = inspect(engine)
        return {"tables": inspector.get_table_names()}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to list tables")


@router.post("/db-table")
async def fetch_table(request: TableRequest):
    """Return all rows from a named table (demo browse helper)."""
    try:
        if not request.table_name:
            raise HTTPException(status_code=400, detail="No table name")
        db_uri = get_db_uri_from_session(request.session_id)
        engine = create_engine(db_uri)
        metadata = MetaData()
        metadata.reflect(bind=engine)
        table = metadata.tables[request.table_name]
        with engine.connect() as conn:
            rows = conn.execute(select(table)).fetchall()
        return {"data": [dict(row._mapping) for row in rows]}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to fetch table data")


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Run a natural-language question through the text-to-SQL agent."""
    try:
        get_db_uri_from_session(request.session_id)
        result = run_sql_agent(request.query, request.session_id)
        return QueryResponse(answer=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
