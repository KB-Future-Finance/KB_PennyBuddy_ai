from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.utilities import SQLDatabase
import os
from db import get_database_engine

def generate_sql_query(user_question: str) -> str:
    """사용자 질문에 기반한 SQL 쿼리 생성"""
    template = """Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Question: {question}
    SQL Query:"""

    engine = get_database_engine()
    db = SQLDatabase(engine)

    prompt = ChatPromptTemplate.from_template(template)

    def get_schema(_):
        return db.get_table_info()

    model = ChatOpenAI(openai_api_key=os.getenv('OPENAI_API_KEY'))

    sql_response_chain = (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | model.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )

    intermediate_result = sql_response_chain.invoke({"question": user_question})
    generated_query = intermediate_result.strip()

    return generated_query
