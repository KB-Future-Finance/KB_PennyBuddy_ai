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
    template = """Based on the table schema below, write a SQL query that would answer the user's question if the categoryType in the Category table is 1, then it is income and 2, then it is expenditure. You should also think about this when finding the total spend and use join.
    If we wanted to get the current assets, we'd need to subtract total expenses from total revenue, right? We'd need to join the category table, and records's delYn is deleted or not. If delYn = Trun, it is deleted data and should not be aggregated.

    
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

    template = """
    너는 친절하고 귀여운 가상 금융 전문가 챗봇 키키야. 
    아래 SQL 쿼리 결과가 주어지면 이를 해석해서 지출이면 -, 수익이면 + 를 붙여서 금액을 한문장으로 반말로 알려줘
    또한 금융전문가로서 개선방안도 한 문장으로 말해줘 :
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
    print(input_data)
    natural_language_response = response_chain.invoke(input_data).content.strip()

    return natural_language_response