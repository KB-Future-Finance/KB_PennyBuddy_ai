from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from ocr import ocr_with_clova
from parse import parse_ocr_data

# .env 파일의 경로를 명시적으로 설정
dotenv_path = os.path.join(os.path.dirname(__file__), 'env/.env')
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)


@app.route('/parse-ocr/', methods=['POST'])
def parse_ocr():
    """업로드된 파일에서 OCR 데이터 파싱"""
    if 'file' not in request.files:
        return jsonify({"error": "파일이 업로드되지 않았습니다."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "파일 이름이 없습니다."}), 400

    try:
        # 환경 변수 로드
        clova_secret_key = os.getenv('CLOVA_API_KEY')
        clova_api_url = os.getenv('CLOVA_ENDPOINT')
        chatgpt_secret_key = os.getenv('openai_api_key')
        LangChain_api_url = os.getenv('LANGCHAIN_ENDPOINT')

        # 파일 저장
        file_location = f"temp_{file.filename}"
        file.save(file_location)

        # OCR 데이터 추출
        ocr_data = ocr_with_clova(file_location, clova_secret_key, clova_api_url)
        print("ocr_data 추출 완료")
        print(ocr_data)

        # OCR 데이터 파싱
        result = parse_ocr_data(ocr_data, chatgpt_secret_key, LangChain_api_url)
        print("ocr_data 파싱 완료")
        print(result)

        # 임시 파일 삭제
        os.remove(file_location)

        return jsonify(result.dict())
    except Exception as e:
        return jsonify({"error": f"서버 오류 발생: {e}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
