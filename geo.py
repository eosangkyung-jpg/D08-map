"""주소 → (위도, 경도) → 다시 주소. 카카오 로컬 API 두 개를 이어 부른다."""
import os

import requests
from dotenv import load_dotenv

API = {
    "주소로_좌표": "https://dapi.kakao.com/v2/local/search/address.json",  # 🔌 주소로 좌표 변환
    "좌표로_주소": "https://dapi.kakao.com/v2/local/geo/coord2address.json",  # 🔌 좌표로 주소 변환
}

load_dotenv(override=True)


class GeoError(Exception):
    """화면에 그대로 보여 줄 한국어 한 줄을 담는 에러. ⛔로 시작하면 키·설정·연결 문제."""


def _kakao_get(name, params):
    """카카오 로컬 API를 부르고 JSON을 돌려준다. 주소·헤더·응답 원문은 출력하지 않는다."""
    key = os.getenv("KAKAO_REST_API_KEY")
    if not key:
        raise GeoError("⛔ .env 에 KAKAO_REST_API_KEY 가 없어요")
    try:
        res = requests.get(API[name], headers={"Authorization": f"KakaoAK {key}"}, params=params, timeout=10)  # 🔌 API 호출
    except requests.Timeout:
        raise GeoError("⛔ 카카오 서버가 10초 안에 답하지 않았어요") from None
    except requests.RequestException:
        raise GeoError("⛔ 인터넷 연결을 확인해 주세요") from None

    if res.status_code == 401:
        raise GeoError("⛔ 카카오 REST API 키가 틀렸어요 (JavaScript 키를 넣지 않았는지 확인)")
    if res.status_code == 403:
        raise GeoError("⛔ 카카오맵 사용 설정을 켜 주세요 (developers.kakao.com → 내 앱 → 카카오맵)")
    if res.status_code != 200:
        raise GeoError(f"⛔ 카카오 API가 실패했어요 (상태 코드 {res.status_code})")
    return res.json()


def _check_korea(lat, lng):
    """한국 밖 좌표(뒤집힌 x·y, 0 좌표)는 쓰지 않는다."""
    if not (33 <= lat <= 39 and 124 <= lng <= 132):
        raise GeoError(f"좌표 ({lat}, {lng}) 가 한국 밖이에요. 위도·경도가 뒤바뀌지 않았는지 확인해 주세요")


def address_to_latlng(address):
    """주소 → (위도, 경도). 카카오 응답의 x = 경도, y = 위도 (글자라서 float로 바꾼다)."""
    data = _kakao_get("주소로_좌표", {"query": address})
    documents = data.get("documents", [])
    if not documents:
        raise GeoError(f"'{address}'을(를) 찾지 못했어요")
    first = documents[0]
    lat = float(first["y"])
    lng = float(first["x"])
    _check_korea(lat, lng)
    return lat, lng


def latlng_to_address(lat, lng):
    """(위도, 경도) → 도로명 주소. 도로명(road_address)이 없으면 지번 주소."""
    _check_korea(lat, lng)
    data = _kakao_get("좌표로_주소", {"x": lng, "y": lat})  # 요청은 x=경도, y=위도
    documents = data.get("documents", [])
    if not documents:
        raise GeoError(f"({lat}, {lng}) 위치의 주소를 찾지 못했어요")
    first = documents[0]
    road = first.get("road_address")  # 비어 있을 수 있음(null)
    if road:
        return "도로명", road["address_name"]
    return "지번", first["address"]["address_name"]


def main():
    address = input("주소를 입력하세요: ").strip()
    if not address:
        print("주소를 입력해 주세요")
        return

    try:
        lat, lng = address_to_latlng(address)
    except GeoError as e:
        print(e)
        return
    print(f"① 좌표: (위도 {lat}, 경도 {lng})")

    try:
        kind, back = latlng_to_address(lat, lng)
        print(f"② 다시 주소({kind}): {back}")
    except GeoError as e:
        print(e)

    print("\n출처: 카카오 로컬 API (주소로 좌표 변환 · 좌표로 주소 변환)")


if __name__ == "__main__":
    main()
