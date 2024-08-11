# 🤖 AI Server

<p align="center">
<br>

![image](https://github.com/user-attachments/assets/d8bc91d2-06a5-44fe-b5b9-abadc2f4167a)

<br>
</p>

## 만든이
<table>
<tbody>
<tr>
<td align="center"><a href="https://github.com/pq5910"><img src="https://avatars.githubusercontent.com/u/81617589?v=4" width="100px;" alt=""/><br /><sub><b> 김우정 </b></sub></a><br /></td>
<td align="center"><a href="https://github.com/testjd1"><img src="https://avatars.githubusercontent.com/u/87185470?v=4" width="100px;" alt=""/><br /><sub><b> 김재동 </b></sub></a><br /></td>
<td align="center"><a href="https://github.com/lee-JunR"><img src="https://avatars.githubusercontent.com/u/68640939?v=4" width="100px;" alt=""/><br /><sub><b> 이준렬 </b></sub></a><br /></td>
</tr>
</tbody>
</table>

## 프로젝트 소개

<p align="justify">
이 프로젝트는 AI 기반 서버 애플리케이션으로, 다양한 AI 모델과 데이터베이스 연동 기능을 제공합니다.
</p>

## 실행 방법

1. 프로젝트 클론

먼저 GitHub에서 이 프로젝트를 클론합니다:
```
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

2. 가상 환경 설정(선택 사항) -> 가상 환경을 설정하여 의존성 충돌을 방지합니다:
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
3. 필수 패키지 설치 -> 필요한 패키지를 requirements.txt 파일을 통해 설치합니다:
```
pip install -r requirements.txt
```
4. 환경 변수 설정

.루트 디렉토리의 env/ 폴더의 env 파일을 아래와 같은 형식으로 환경 변수를 설정합니다:
```
# OpenAI 설정
OPENAI_API_KEY=openapi 키를 입력하세요

# LangChain 설정
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=랭체인 api 키를 입력하세요
LANGCHAIN_PROJECT=당신의 프로젝트 이름을 입력하세요

# Clova 설정
CLOVA_API_KEY=클로바 api 키를 입력하세요
CLOVA_ENDPOINT=클로바 endpoint를 입력하세요

# 데이터베이스 설정
DB_USER=db username 을 입력하세요
DB_PASSWORD=username 패스워드를 입력하세요
DB_HOST=localhost  # 또는 당신의 db 호스트를 입력하세요
DB_PORT=3306  # 또는 당신의 db 포트를 입력하세요.
DB_NAME=testkb  # 사용할 데이터베이스 이름을 입력하세요
```
5. 서버 실행

이제 서버를 실행합니다:
```
python app.py
```
6. (선택 사항) 의존성 문제 해결

서버 실행 중 의존성 문제(특히 LangChain 관련)가 발생하는 경우, 아래 명령어로 최신 버전을 설치합니다:
```
pip install -U langchain-community
```
7. 서버 접근

서버가 정상적으로 실행되면, 브라우저 또는 API 클라이언트를 통해 서버에 접근할 수 있습니다. 기본적으로 서버는 http://127.0.0.1:5000 에서 실행됩니다.


## 구현 기능
•	뉴스 요약 (news_summary.py)
	•	OCR(광학 문자 인식) (ocr.py)
	•	질의 생성 (query_generator.py)
	•	SQL 실행기 (sql_executor.py)

## API 엔드포인트 설명

1. /chatbot/ (POST)

	•	설명: 사용자의 질문을 받아 ChatGPT 기반의 챗봇이 응답을 생성합니다.
	•	사용법: POST 요청 시, JSON 형식으로 question 필드를 포함하여 질문을 보냅니다.

2. /execute-sql/ (POST)

	•	설명: 자연어로 된 질문을 받아 SQL 쿼리를 생성하고, 결과를 반환합니다.
	•	사용법: POST 요청 시, JSON 형식으로 question 필드를 포함하여 SQL 쿼리를 생성할 질문을 보냅니다.

3. /parse-ocr/ (POST)

	•	설명: 업로드된 이미지 파일에서 OCR 데이터를 추출하고, 이를 JSON 형식으로 파싱합니다.
	•	사용법: POST 요청 시, 이미지 파일을 file 필드에 포함하여 전송합니다. 서버는 파일을 처리한 후 추출된 데이터를 JSON으로 반환합니다.

4. /summarize-news/ (GET)

	•	설명: 뉴스 기사 링크를 요약하여 텍스트로 반환합니다.
	•	사용법: GET 요청으로 호출하며, 서버는 뉴스 요약 텍스트와 원본 링크를 스트리밍 형태로 반환합니다.

5. /analyze-and-execute/ (POST)

	•	설명: 사용자의 입력을 분석하여 적절한 엔드포인트로 라우팅하고, 그 결과를 반환합니다.
	•	사용법: POST 요청 시, JSON 형식으로 question 필드를 포함하여 전송합니다. 입력된 질문에 따라 적절한 API 엔드포인트가 자동으로 선택되어 실행됩니다.


라이센스

MIT © NoHack 템플릿
