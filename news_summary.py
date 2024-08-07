import random
import requests
from bs4 import BeautifulSoup as bs
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os

dotenv_path = os.path.join(os.path.dirname(__file__), 'env/.env')
load_dotenv(dotenv_path=dotenv_path)

# 환경변수에서 API 키를 불러옵니다
llm = ChatOpenAI(
    api_key=os.getenv('OPENAI_API_KEY'),
    temperature=1.0,
    max_tokens=2048,
    model_name="gpt-4o-mini"
)

def get_article_link(search_url, n):
    """뉴스 검색 결과 페이지에서 n번째 기사의 링크를 가져옵니다"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    page = requests.get(search_url, headers=headers)
    soup = bs(page.text, "html.parser")
    elements = soup.select(".news_tit")
    if n < 1 or n > len(elements):
        raise ValueError("주어진 n 값이 유효하지 않습니다.")
    article_element = elements[n - 1]
    article_url = article_element.get('href')
    return article_url

def summarize_url(url):
    """주어진 URL의 내용을 요약합니다"""
    loader = WebBaseLoader(url)
    text = loader.load_and_split()
    load_content = text[0].page_content

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    texts = text_splitter.create_documents([load_content])

    prompt_template = """당신은 시사 상식 전문가입니다. 내용을 말투는 캐주얼한 톤앤 매너(존댓말)와 이모티콘을 추가해서 시사 상식을 잘 모르는 사람도 알 수 있게 쉬운 설명으로 3줄로 말해주세요:
    "{text}"
   """
    prompt = PromptTemplate.from_template(prompt_template)
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=llm_chain, document_variable_name="text")
    summary = stuff_chain.run(texts)
    return summary

def summarize_news():
    """뉴스 기사 링크를 요약합니다"""
    search_url = "https://search.naver.com/search.naver?where=news&ie=utf8&sm=nws_hty&query=kb"
    n = random.randint(1, 5)  # 1~5 사이의 정수
    try:
        article_url = get_article_link(search_url, n)
        summary = summarize_url(article_url)
        return {"url": article_url, "response": summary}
    except ValueError as e:
        return {"error": str(e)}, 400
    except Exception as e:
        return {"error": f"서버 오류 발생: {e}"}, 500
