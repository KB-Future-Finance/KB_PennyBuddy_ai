from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
import os

def get_database_engine() -> Engine:
    """환경 변수를 사용하여 데이터베이스 연결 엔진을 생성합니다."""
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')

    connection_string = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(connection_string)
    return engine

def get_session():
    """SQLAlchemy 세션을 반환합니다."""
    engine = get_database_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def test_database_connection(engine: Engine) -> bool:
    """데이터베이스 연결 테스트를 수행합니다."""
    try:
        with engine.connect() as connection:
            # 데이터베이스 연결 테스트 쿼리 실행
            result = connection.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        print(f"데이터베이스 연결 테스트 중 오류 발생: {e}")
        return False
if __name__ == "__main__":
    print(test_database_connection(get_database_engine()))
