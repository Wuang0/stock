import os
from dotenv import load_dotenv

load_dotenv()

# LLM API配置
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_API_BASE = os.getenv("LLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4")
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4.7")

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
