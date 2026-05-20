# from langchain_core.prompts import ChatPromptTemplate
# from langchain_groq import ChatGroq
# import api_keys

# template = "You are a helpful assistant that answers questions about the world."

# user_question = "What is the capital of France?"

# llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

# prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", template),
#         ("user", "{question}")
#     ]
# )

# final_prompt = prompt.invoke({"question": user_question})

# response = llm.invoke(final_prompt)

# print(response.content)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
import api_keys
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that answers questions about the world."),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{question}")
    ]
)

chain = prompt | llm

chat_history = {}

def get_session_history(session_id):
    if session_id not in chat_history:
        chat_history[session_id] = ChatMessageHistory()
    return chat_history[session_id]

conversation_chain = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history"
)

response1 = conversation_chain.invoke(
    {"question": "What is the capital of France?"},
    config={"configurable": {"session_id": "user_1"}}
)

print(response1.content)

response2 = conversation_chain.invoke(
    {"question": "What is its population?"},
    config={"configurable": {"session_id": "user_1"}}
)

print(response2.content)



