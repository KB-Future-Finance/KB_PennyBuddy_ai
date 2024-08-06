import random

from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup as bs

from ocr import ocr_with_clova
from parse import parse_ocr_data
from query_generator import generate_sql_query
from sql_executor import execute_sql_query
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# .env 파일의 경로를 명시적으로 설정
dotenv_path = os.path.join(os.path.dirname(__file__), 'env/.env')
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)


def load_environment_variables():
    required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT', 'DB_NAME', 'OPENAI_API_KEY', 'CLOVA_API_KEY',
                     'CLOVA_ENDPOINT', 'LANGCHAIN_ENDPOINT']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is missing")


load_environment_variables()

# LLM 객체 생성
llm = ChatOpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=1.0,
    max_tokens=2048,
    model_name="gpt-4o-mini"
)


def get_article_link(search_url, n):
    # USER_AGENT 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # 네이버 뉴스 검색 결과 페이지 로드
    page = requests.get(search_url, headers=headers)
    soup = bs(page.text, "html.parser")

    # 기사 링크 가져오기
    elements = soup.select(".news_tit")

    # 기사 링크가 n번째 요소를 선택
    if n < 1 or n > len(elements):
        raise ValueError("주어진 n 값이 유효하지 않습니다.")

    article_element = elements[n - 1]
    article_url = article_element.get('href')

    return article_url


def summarize_url(url):
    # 웹 페이지 로드
    loader = WebBaseLoader(url)
    text = loader.load_and_split()

    # 내용 추출
    load_content = text[0].page_content

    # 텍스트 분할
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    texts = text_splitter.create_documents([load_content])

    # 프롬프트 정의
    prompt_template = """당신은 시사 상식 전문가입니다. 내용을 말투는 캐주얼한 톤앤 매너와 이모티콘을 추가해서 시사 상식을 잘 모르는 사람도 알 수 있게 쉬운 설명으로 3줄로 말해주세요:
    "{text}"
   """
    prompt = PromptTemplate.from_template(prompt_template)

    # LLM 체인 정의
    llm_chain = LLMChain(llm=llm, prompt=prompt)

    # StuffDocumentsChain 정의
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")

    # 요약 결과 출력
    summary = stuff_chain.run(texts)
    return summary


@app.route('/chatbot/', methods=['POST'])
def query_expenses():
    """자연어 질문을 받아서 가계부 데이터를 반환"""
    data = request.get_json()
    user_question = data.get('question')

    if not user_question:
        return jsonify({"error": "질문이 제공되지 않았습니다."}), 400

    try:
        generated_query = generate_sql_query(user_question)
        print("Generated SQL Query:", generated_query)
        result = execute_sql_query(generated_query)
        print("Query Result:", result)
        return jsonify({"query": generated_query, "response": result})
    except Exception as e:
        return jsonify({"error": f"서버 오류 발생: {e}"}), 500


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

        return jsonify(result.dict())
    except FileNotFoundError:
        return jsonify({"error": "파일을 찾을 수 없습니다."}), 500
    except Exception as e:
        print(f"서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {e}"}), 500


@app.route('/summarize-news/', methods=['GET'])
def summarize_news():
    """뉴스 기사 링크를 요약"""
    search_url = "https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query=kb"
    n = random.randint(1, 5)  # 1~5 사이의 정수

    try:
        article_url = get_article_link(search_url, n)
        print(f"선택된 기사 링크: {article_url}")

        # 요약 결과 출력
        summary = summarize_url(article_url)
        print(f"\n요약내용 : {summary}")

        return jsonify({"url": article_url, "summary": summary})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"서버 오류 발생: {e}")
        return jsonify({"error": f"서버 오류 발생: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
