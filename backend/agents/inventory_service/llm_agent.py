from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
# from llm_config import get_llm
 from config import settings

llm = ChatOpenAI(model="gpt-4o-mini",openai_api_key=settings.OPENAI_API_KEY)
# Setup retriever using MongoDB vector search



# Define prompt with system role
SYSTEM_PROMPT = """You are a helpful assistant managing a vegetable/fruit inventory. 
You work with a collection named `current_inventory` that contains items with fields:
- item (string, singular like 'tomato')
- quantity (integer)
- stored_on (date in YYYY-MM-DD)

Your job is to:
1. Detect user intent: insert / update / delete / fetch
2. For insert/update/delete, extract data and respond in JSON without comments as below with no other explanation:
   Respond only in pure JSON format as a list. No markdown, no comments, no multiple objects separated by newlines.
   {{"Intent": "insert",
   "Data": {{"item": ..., "quantity": ..., "stored_on": ...}}
    }}
3. For inventory questions (like "show all items" or "what do we have today?"), use the provided records from the current inventory to answer naturally.
Only use the context when generating answers, not for CRUD actions.
{context}
"""

prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT),
    HumanMessagePromptTemplate.from_template("User: {query_text}\n\nContext:\n{context}")
])
