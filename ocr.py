import json
import requests
import uuid
import time

def ocr_with_clova(image_path: str, secret_key: str, api_url: str) -> str:
    """Clova OCR API를 사용하여 이미지에서 텍스트 추출"""
    try:
        request_json = {
            'images': [{'format': 'png', 'name': 'demo'}],
            'requestId': str(uuid.uuid4()),
            'version': 'V2',
            'timestamp': int(round(time.time() * 1000))
        }

        payload = {'message': json.dumps(request_json).encode('UTF-8')}
        files = [('file', open(image_path, 'rb'))]
        headers = {'X-OCR-SECRET': secret_key}

        response = requests.post(api_url, headers=headers, data=payload, files=files)

        if response.status_code == 200:
            ocr_results = response.json()
            all_texts = []
            for image_result in ocr_results['images']:
                for field in image_result['fields']:
                    text = field['inferText']
                    all_texts.append(text)

            # 모든 텍스트를 띄어쓰기로 연결하여 출력
            full_text = ' '.join(all_texts)
            return full_text
        else:
            raise Exception(f"OCR 결과를 받아오지 못했습니다. 상태 코드: {response.status_code}")
    except Exception as e:
        raise Exception(f"오류 발생: {e}")

# 예시 사용법:
# api_url = "https://your-clova-api-url"
# secret_key = "your-clova-secret-key"
# image_path = "path/to/your/image.png"
# print(ocr_with_clova(image_path, secret_key, api_url))
