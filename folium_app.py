"""우리동네지도: 장소를 검색해 그 반경 안의 카테고리 장소 15개를 가까운 순으로 folium 지도에 찍는다.

실행:  streamlit run folium_app.py   → http://localhost:8501
.env 를 고쳤으면 터미널에서 Ctrl+C 후 다시 streamlit run
지도 그림은 OpenStreetMap 타일(키 없음)이라 카카오 JS 키·도메인 등록은 필요 없다.
"""
import html
import os

import folium
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

API = {
    "키워드검색": "https://dapi.kakao.com/v2/local/search/keyword.json",  # 🔌 카카오 키워드로 장소 검색 (중심 좌표)
    "카테고리검색": "https://dapi.kakao.com/v2/local/search/category.json",  # 🔌 카카오 카테고리로 장소 검색 (주변)
}

load_dotenv(override=True)

카테고리 = {
    "카페": "CE7", "음식점": "FD6", "편의점": "CS2", "약국": "PM9", "병원": "HP8",
    "지하철역": "SW8", "주차장": "PK6", "대형마트": "MT1", "은행": "BK9",
    "관광명소": "AT4", "문화시설": "CT1",
}


def 한국_좌표인가(위도, 경도):
    return 33 <= 위도 <= 39 and 124 <= 경도 <= 132


def 카카오_부르기(이름, params):
    """카카오 로컬 API를 부르고 documents 를 돌려준다. 실패하면 한국어 한 줄로 RuntimeError."""
    키 = os.getenv("KAKAO_REST_API_KEY")
    try:
        res = requests.get(  # 🔌 API 호출
            API[이름], headers={"Authorization": f"KakaoAK {키}"}, params=params, timeout=10,
        )
    except requests.RequestException:
        raise RuntimeError("⛔ 카카오 서버에 연결하지 못했어요 (인터넷 연결을 확인해 주세요)") from None
    if res.status_code == 401:
        raise RuntimeError("⛔ 카카오 REST API 키가 틀렸어요 (JavaScript 키를 넣지 않았는지 확인)")
    if res.status_code == 403:
        raise RuntimeError("⛔ 카카오맵 사용 설정을 켜 주세요 (카카오 개발자 콘솔)")
    if res.status_code != 200:
        raise RuntimeError(f"카카오 장소 검색이 실패했어요 (상태 코드 {res.status_code})")
    return res.json().get("documents", [])


def 장소_정리(장소):
    """카카오의 x·y(글자)를 위도·경도(숫자)로 바꾸고 한글 칸 이름을 붙인다. 한국 밖이면 None."""
    try:
        위도 = float(장소["y"])  # y = 위도
        경도 = float(장소["x"])  # x = 경도
    except (KeyError, ValueError):
        return None
    if not 한국_좌표인가(위도, 경도):
        return None
    return {
        "이름": 장소.get("place_name", ""),
        "주소": 장소.get("road_address_name") or 장소.get("address_name", ""),
        "거리(m)": int(장소["distance"]) if 장소.get("distance") else None,
        "전화": 장소.get("phone", ""),
        "위도": 위도,
        "경도": 경도,
    }


@st.cache_data(ttl=600)
def 중심_찾기(검색어):
    """검색어의 첫 결과를 중심으로 쓴다. 에러는 예외로 내서 캐시에 남지 않게 한다."""
    for 장소 in 카카오_부르기("키워드검색", {"query": 검색어, "size": 5}):
        정리 = 장소_정리(장소)
        if 정리:
            return 정리
    raise RuntimeError(f"'{검색어}'을(를) 찾지 못했어요")


@st.cache_data(ttl=600)
def 주변_찾기(코드, 위도, 경도, 반경):
    문서들 = 카카오_부르기("카테고리검색", {
        "category_group_code": 코드,
        "x": 경도, "y": 위도,  # 요청은 x=경도, y=위도
        "radius": 반경, "sort": "distance", "size": 15,
    })
    return [p for p in map(장소_정리, 문서들) if p]


def 지도_만들기(중심, 장소들, 반경):
    지도 = folium.Map(location=[중심["위도"], 중심["경도"]], zoom_start=15)  # [위도, 경도] 순서
    folium.Circle([중심["위도"], 중심["경도"]], radius=반경, color="#3388ff", fill=True, fill_opacity=0.05).add_to(지도)
    folium.Marker(
        [중심["위도"], 중심["경도"]],
        tooltip=html.escape(f"검색 위치: {중심['이름']}"),
        icon=folium.Icon(color="red", icon="star"),
    ).add_to(지도)
    for 번호, p in enumerate(장소들, start=1):
        # 이름·주소는 escape 해서 따옴표·태그가 있어도 화면이 안 깨지게
        말풍선 = f"<b>{번호}. {html.escape(p['이름'])}</b><br>{html.escape(p['주소'])}<br>{p['거리(m)']}m"
        folium.Marker(
            [p["위도"], p["경도"]],
            tooltip=html.escape(f"{번호}. {p['이름']}"),
            popup=folium.Popup(말풍선, max_width=250),
        ).add_to(지도)
    if 장소들:
        점들 = [[중심["위도"], 중심["경도"]]] + [[p["위도"], p["경도"]] for p in 장소들]
        지도.fit_bounds(점들)  # 마커가 다 화면 안에
    return 지도


st.set_page_config(page_title="우리동네지도", page_icon="🗺️", layout="wide")
st.title("🗺️ 우리동네지도")

if not os.getenv("KAKAO_REST_API_KEY"):
    st.error(".env 에 KAKAO_REST_API_KEY 가 없어요. 키를 넣은 뒤 Ctrl+C 하고 다시 streamlit run 해 주세요")
    st.stop()

with st.sidebar:
    검색어 = st.text_input("어디 근처를 볼까요?", value="성수역")
    고른것 = st.selectbox("카테고리", list(카테고리))
    반경 = st.slider("반경 (m)", min_value=100, max_value=3000, value=500, step=100)

if not 검색어.strip():
    st.info("왼쪽에 장소를 입력해 주세요")
    st.stop()

try:
    중심 = 중심_찾기(검색어.strip())
except RuntimeError as 에러:
    st.error(str(에러))
    st.stop()

try:
    장소들 = 주변_찾기(카테고리[고른것], 중심["위도"], 중심["경도"], 반경)
except RuntimeError as 에러:
    st.error(str(에러))
    장소들 = []

st.caption(f"검색 위치: {중심['이름']} · {중심['주소']} (위도 {중심['위도']:.5f}, 경도 {중심['경도']:.5f})")

왼쪽, 가운데, 오른쪽 = st.columns(3)
왼쪽.metric(f"반경 {반경}m 안 {고른것}", f"{len(장소들)}곳")
가운데.metric("가장 가까운 곳", f"{장소들[0]['거리(m)']}m" if 장소들 else "-")
오른쪽.metric("가장 먼 곳", f"{장소들[-1]['거리(m)']}m" if 장소들 else "-")
if 장소들:
    st.caption(f"가장 가까운 곳: {장소들[0]['이름']}")
else:
    st.info(f"반경 {반경}m 안에 {고른것}을(를) 찾지 못했어요. 반경을 넓혀 보세요")

st.iframe(지도_만들기(중심, 장소들, 반경).get_root().render(), height=520)

if 장소들:
    표 = pd.DataFrame(장소들)
    표.index = range(1, len(표) + 1)
    st.dataframe(표, width="stretch")

st.caption("출처: 카카오 로컬 API (키워드로 장소 검색 · 카테고리로 장소 검색) · 지도 © OpenStreetMap")
