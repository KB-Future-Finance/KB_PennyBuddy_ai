from pydantic import BaseModel, Field

class Topic(BaseModel):
    """OCR 데이터의 Pydantic 모델 정의"""
    amount: str = Field(description="총 금액")
    reg_date: str = Field(description="날짜 및 시간")
    member_Id: int = 1
    category_Id: str = Field(
        description="적합한 카테고리를 골라줘 가능한 카테고리 :  소득, 저축 출금, 차입, 세금 · 공과금, 식비, 주거, 피복, 보건위생, 교육, 여가 활동, 교통, 통신, 효도, 기타, 특비, 저축, 차입금 상환"
    )
    record_memo: str = Field(description="메모 제목을 요약해서 적어줘")
    record_details: str = Field(description="영수증을 보고 이 영수증을 받은 사람이 뭘 했는지 추론해서 적어줘")
    delYn: int = 0
