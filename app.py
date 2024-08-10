from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import os
import re
import threading
import queue

from flask_cors import CORS
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.schema.runnable import RunnablePassthrough
from langchain.callbacks.base import BaseCallbackHandler

from news_summary import summarize_news
from ocr import ocr_with_clova
from parse import parse_ocr_data
from query_generator import generate_sql_query, execute_and_convert_to_natural_language
import openai
from db import get_database_engine

# .env 파일의 경로를 명시적으로 설정
dotenv_path = os.path.join(os.path.dirname(__file__), 'env/.env')
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)
CORS(app)

def load_environment_variables():
    required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'OPENAI_API_KEY', 'CLOVA_API_KEY',
                     'CLOVA_ENDPOINT', 'LANGCHAIN_ENDPOINT']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is missing")

load_environment_variables()

# LangChain 챗봇 설정
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(api_key=openai_api_key, temperature=0.1)
memory = ConversationSummaryBufferMemory(
    llm=llm,
    max_token_limit=80,
    memory_key="chat_history",
    return_messages=True,
)

def load_memory():
    return memory.load_memory_variables({})["chat_history"]

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 사람과 대화하는 친절한 가계부 AI 챗봇입니다. 키키라는 이름을 가지고 있어. "),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}"),
])

get_chat_history_func = lambda: load_memory()

chain = RunnablePassthrough.assign(chat_history=get_chat_history_func) | prompt | llm

class ThreadedGenerator:
    def __init__(self):
        self.queue = queue.Queue()

    def __iter__(self):
        return self

    def __next__(self):
        item = self.queue.get()
        if item is StopIteration:
            raise item
        return item

    def send(self, data):
        self.queue.put(data)

    def close(self):
        self.queue.put(StopIteration)


class ChainStreamHandler(BaseCallbackHandler):
    def __init__(self, gen):
        self.gen = gen

    def on_llm_new_token(self, token: str, **kwargs):
        self.gen.send(token)

def llm_thread(g, prompt):
    try:
        chat = ChatOpenAI(
            api_key=openai_api_key,
            verbose=True,
            streaming=True,
            callbacks=[ChainStreamHandler(g)],
            temperature=0.7,
        )
        chat([HumanMessage(content=prompt)])
    finally:
        g.close()

def chain_stream(prompt):
    g = ThreadedGenerator()
    threading.Thread(target=llm_thread, args=(g, prompt)).start()
    return g

@app.route('/chatbot/', methods=['POST'])
def chatbot():
    print('chatbot 실행됨')
    data = request.json
    user_input = data.get('question', '')

    if not user_input:
        return jsonify({"error": "메시지가 제공되지 않았습니다."}), 400

    return Response(chain_stream(user_input), mimetype='text/plain')

@app.route('/execute-sql/', methods=['POST'])
def query_expenses():
    """자연어 질문을 받아서 가계부 데이터를 반환"""
    data = request.get_json()
    user_question = data.get('question')

    if not user_question:
        return jsonify({"error": "질문이 제공되지 않았습니다."}), 400

    def stream_sql_response():
        try:
            generated_query = generate_sql_query(user_question)

            engine = get_database_engine()
            natural_language_response = execute_and_convert_to_natural_language(engine, generated_query)
            yield f"{natural_language_response}"
        except Exception as e:
            yield f"서버 오류 발생: {e}\n"

    return Response(stream_sql_response(), mimetype='text/plain')

@app.route('/parse-ocr/', methods=['POST'])
def parse_ocr():
    """업로드된 파일에서 OCR 데이터 파싱"""
    if 'file' not in request.files:
        return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "파일 이름이 없습니다."}), 400

    try:
        clova_secret_key = os.getenv('CLOVA_API_KEY')
        clova_api_url = os.getenv('CLOVA_ENDPOINT')
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        LangChain_api_url = os.getenv('LANGCHAIN_ENDPOINT')

        file_location = f"temp_{file.filename}"
        file.save(file_location)

        ocr_data = ocr_with_clova(file_location, clova_secret_key, clova_api_url)
        print("OCR Data Extracted:", ocr_data)

        result = parse_ocr_data(ocr_data, OPENAI_API_KEY, LangChain_api_url)
        print("Parsed OCR Data:", result)

        os.remove(file_location)
        print(result.dict);
        return jsonify(result.dict())
    except FileNotFoundError:
        return jsonify({"error": "파일을 찾을 수 없습니다."}), 500
    except Exception as e:
        print(f"서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {e}"}), 500

@app.route('/summarize-news/', methods=['GET'])
def summarize_news_endpoint():
    """뉴스 기사 링크를 요약"""
    def stream_news_summary():
        try:
            response = summarize_news()
            yield f"{response.get('response')}"
            yield f"웹사이트 link : {response.get('url')}"
        except Exception as e:
            yield f"서버 오류 발생: {e}\n"

    return Response(stream_news_summary(), mimetype='text/plain')

openai.api_key = os.getenv('OPENAI_API_KEY')

def analyze_input(user_input):
    if "뉴스" in user_input:
        return "summarize-news"
    # elif "OCR" in user_input:
    #     return "parse-ocr"
    elif is_expense_query(user_input):
        return "execute-sql"
    else:
        return "chatbot"

def is_expense_query(user_input):
    expense_patterns = [
        r"\d{4}\s*년\s*\d{1,2}\s*월\s*에\s*얼마\s*썼어",         # 2024년 7월에 얼마 썼어
        r"\d{2}\s*년\s*\d{1,2}\s*월\s*에\s*얼마\s*썼어",          # 24년 7월에 얼마 썼어
        r"\d{1,2}\s*월\s*에\s*얼마\s*썼어",                     # 7월에 얼마 썼어
        r"올해\s*얼마나\s*많이\s*돈\s*을\s*썼(어|지)",           # 올해 얼마나 많이 돈을 썼어/썼지
        r"여태까지\s*쓴\s*지출\s*내역\s*(알려줘)?",             # 여태까지 쓴 지출 내역 알려줘
        r"지난\s*달\s*소비\s*내역\s*(알려줘)?",                 # 지난 달 소비 내역 알려줘
        r"이번\s*달\s*지출\s*(알려줘)?",                       # 이번 달 지출 알려줘
        r"최근\s*소비\s*기록\s*(알려줘)?",                      # 최근 소비 기록 알려줘
        r"소비", r"얼마", r"지출", r"수입", r"수익", r"내역", r"자산",
    ]
    for pattern in expense_patterns:
        if re.search(pattern, user_input):
            return True
    return False

@app.route('/analyze-and-execute/', methods=['POST'])
def analyze_and_execute():
    data = request.json
    user_input = data.get('question', '')

    if not user_input:
        return jsonify({"error": "질문이 제공되지 않았습니다."}), 400

    endpoint = analyze_input(user_input)
    response = None

    if endpoint == "summarize-news":
        response = summarize_news_endpoint()
    elif endpoint == "parse-ocr":
        response = parse_ocr()
    elif endpoint == "execute-sql":
        response = query_expenses()
    else:
        response = chatbot()

    return response

if __name__ == '__main__':
    app.run(debug=True)