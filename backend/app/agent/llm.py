from google.cloud import aiplatform
from langchain.chat_models import init_chat_model
from app.config.settings import settings

aiplatform.init(project=settings.GCP_PROJECT_ID, location=settings.GCP_REGION)

llm = init_chat_model(settings.VERTEX_AI_MODEL, model_provider="google_vertexai")
