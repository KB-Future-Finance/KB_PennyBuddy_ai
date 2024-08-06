from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models import Topic


def parse_ocr_data(ocr_data: str, secret_key: str, api_url: str) -> Topic:
    """OCR 데이터를 JSON 형식으로 파싱"""
    try:
        chat_model = ChatOpenAI(
            api_key=secret_key,
            temperature=1.0,
            max_tokens=2048,
            model_name="gpt-4o-mini"
        )

        question = ocr_data + "\n\n이 영수증 데이터를 가지고 JSON 파싱을 진행할거야. 아래 기준에 따라 데이터를 추출해줘."

        parser = JsonOutputParser(pydantic_object=Topic)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "당신은 친절한 AI 어시스턴트입니다. 아래의 OCR 데이터를 추론하여 JSON 형식으로 파싱하세요."),
                ("user", "{format_instructions}\n\n{question}"),
            ]
        )

        prompt = prompt.partial(format_instructions=parser.get_format_instructions())
        chain = prompt | chat_model | parser
        result = chain.invoke({"question": question})

        # dict로 변환 후 Topic 모델로 변환
        if isinstance(result, dict):
            result = Topic(**result)

        # 카테고리 ID와 이름 매핑
        category_mapping = {
            "1": ['소득'],
            "2": ['저축 출금'],
            "3": ['차입'],
            "4": ['세금 · 공과금'],
            "5": ['식품', '식료품', '식비'],
            "6": ['주거'],
            "7": ['피복'],
            "8": ['보건위생'],
            "9": ['교육'],
            "10": ['여가 활동'],
            "11": ['교통'],
            "12": ['통신'],
            "13": ['효도'],
            "14": ['기타'],
            "15": ['특비'],
            "16": ['저축'],
            "17": ['차입금 상환']
        }

        # 카테고리 ID 검증 및 기본값 설정
        category_name = result.category_Id
        print(category_name)
        print(category_mapping.values())

        # 카테고리 이름을 ID로 매핑
        category_id = None
        for cat_id, names in category_mapping.items():
            if category_name in names:
                category_id = cat_id
                break

        if category_id is None:
            print(f"Invalid category name: {result.category_Id}")
            category_id = "14"  # '기타'는 기본값으로 14로 설정

        result.category_Id = category_id

        print(result)
        return result
    except Exception as e:
        raise Exception(f"오류 발생: {e}")
