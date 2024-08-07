from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.utilities import SQLDatabase
import os
from db import get_database_engine
from sqlalchemy import text
from sqlalchemy.engine import Engine  # 여기에 Engine을 import

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

def execute_and_convert_to_natural_language(engine: Engine, sql_query: str) -> str:
    """SQL 쿼리를 실행하고 결과를 자연어로 변환"""
    with engine.connect() as connection:
        result = connection.execute(text(sql_query)).fetchall()
        result_str = str(result)

    template = """아래 SQL 쿼리 결과가 주어지면 이를 자연어 응답으로 변환합니다.:
    SQL Query: {query}
    SQL Result: {result}
    Natural Language Response:"""

    model = ChatOpenAI(openai_api_key=os.getenv('OPENAI_API_KEY'))

    prompt = ChatPromptTemplate.from_template(template)

    response_chain = (
        RunnablePassthrough.assign(query=lambda _: sql_query, result=lambda _: result_str)
        | prompt
        | model
    )

    input_data = {"query": sql_query, "result": result_str}
    natural_language_response = response_chain.invoke(input_data).content.strip()

    return natural_language_response