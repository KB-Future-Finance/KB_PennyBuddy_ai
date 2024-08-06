from db import get_session
from sqlalchemy import text

def execute_sql_query(generated_query: str) -> str:
    """생성된 SQL 쿼리를 실행하고 결과를 반환"""
    try:
        session = get_session()
        # SQLAlchemy text 객체로 쿼리 감싸기
        result = session.execute(text(generated_query))
        session.commit()  # 데이터 변경 시 커밋 필요

        # 결과가 있을 경우
        if result.returns_rows:
            result_data = result.fetchall()
            result_str = "\n".join(str(row) for row in result_data)
        else:
            # 결과가 없을 경우 (예: INSERT, UPDATE, DELETE)
            result_str = "쿼리 실행 완료"
        session.close()
        return result_str
    except Exception as e:
        print(f"쿼리 실행 중 오류 발생: {e}")
        return f"쿼리 실행 중 오류 발생: {e}"
