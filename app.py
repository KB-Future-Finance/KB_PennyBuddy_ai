from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os

from news_summary import summarize_news
from ocr import ocr_with_clova
from parse import parse_ocr_data
from query_generator import generate_sql_query
from sql_executor import execute_sql_query

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
def summarize_news_endpoint():
    """뉴스 기사 링크를 요약"""
    response = summarize_news()
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=True)
