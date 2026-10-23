"""주차장 데이터 살펴보기: data/park_data.csv 를 판다스로 읽어 몇 줄·몇 칸인지, 어떤 인코딩인지 보여 준다.

실행:  streamlit run parking.py   → http://localhost:8501
(오늘은 단계마다 조금씩 기능을 늘려 간다.)
"""
from pathlib import Path

import pandas as pd
import streamlit as st

CSV_PATH = Path(__file__).parent / "data" / "park_data.csv"
RAW_PATH = Path(__file__).parent / "data" / "parking_raw.csv"  # .gitignore(data/*_raw.*)로 레포에 안 올라감
SEOUL_PATH = Path(__file__).parent / "data" / "parking_seoul.csv"  # 고른 구 결과 (고를 때마다 덮어씀)
ENCODINGS = ["utf-8-sig", "cp949"]  # 공공데이터는 둘 다 있음 → 순서대로 시도

MAIN_COLS = ["주차장명", "소재지도로명주소", "위도", "경도", "주차기본요금"]
KEEP_COLS = [
    "주차장명", "주차장구분", "주차장유형", "소재지도로명주소", "소재지지번주소",
    "주차구획수", "요금정보", "주차기본시간", "주차기본요금", "위도", "경도", "데이터기준일자",
]
SEOUL_GU = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
]


@st.cache_data
def read_csv(path):
    """인코딩을 차례로 시도해 읽고 (표, 읽은 인코딩)을 돌려준다. 다 실패하면 예외."""
    for encoding in ENCODINGS:
        try:
            df = pd.read_csv(path, encoding=encoding, low_memory=False)
            return df, encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{', '.join(ENCODINGS)} 어느 것으로도 한글을 읽지 못했어요")


st.set_page_config(page_title="주차장 데이터", page_icon="🅿️")
st.title("🅿️ 주차장 데이터 살펴보기")

if not CSV_PATH.exists():
    st.error(f"'{CSV_PATH.name}' 파일이 data 폴더에 없어요")
    st.stop()

try:
    df, encoding = read_csv(CSV_PATH)
except ValueError as e:
    st.error(str(e))
    st.stop()

col1, col2, col3 = st.columns(3)
col1.metric("전체 줄 수", f"{df.shape[0]:,}")
col2.metric("전체 칸 수", f"{df.shape[1]:,}")
col3.metric("인코딩", encoding)

st.subheader(f"칸 이름 전체 ({df.shape[1]}개)")
st.write(", ".join(df.columns))

st.subheader("처음 5줄")
st.dataframe(df.head(5))

st.subheader("원본 저장")
st.caption(f"전체 {len(df):,}줄을 {RAW_PATH.name}로 저장해요 (utf-8-sig: 엑셀에서도 한글이 안 깨짐)")
if st.button(f"{RAW_PATH.name}로 저장"):
    try:
        df.to_csv(RAW_PATH, encoding="utf-8-sig", index=False)
        st.success(f"data/{RAW_PATH.name} 저장 완료 ({len(df):,}줄)")
    except PermissionError:
        st.error(f"{RAW_PATH.name}이(가) 엑셀에서 열려 있어 저장하지 못했어요. 엑셀을 닫고 다시 눌러 주세요")

st.subheader("주요 칸 빈칸 개수")
st.dataframe(df[MAIN_COLS].isna().sum().rename("빈칸 개수"))
with st.expander("칸 34개 전체 빈칸 개수"):
    st.dataframe(df.isna().sum().rename("빈칸 개수"))

# ── 서울 구 하나로 거르기 ──
st.header("서울 구별 주차장")
gu = st.selectbox("구 고르기", SEOUL_GU, index=SEOUL_GU.index("강남구"))
area = f"서울특별시 {gu}"  # 시·도까지 붙여야 "중구"가 다른 도시와 안 섞임

seoul = df[KEEP_COLS].copy()
seoul["주소"] = seoul["소재지도로명주소"].fillna(seoul["소재지지번주소"]).str.strip()
seoul = seoul[seoul["주소"].str.startswith(area, na=False)]

st.metric(f"{area} 주차장 수", f"{len(seoul):,}곳")
st.caption(
    f"센 조건: 소재지도로명주소(비었으면 소재지지번주소)가 '{area}'로 시작하는 줄 · "
    f"데이터 기준일 {', '.join(sorted(seoul['데이터기준일자'].dropna().astype(str).unique())) or '없음'}"
)
st.dataframe(seoul, hide_index=True)

if st.button(f"{area} 결과를 {SEOUL_PATH.name}로 저장"):
    try:
        seoul.to_csv(SEOUL_PATH, encoding="utf-8-sig", index=False)
        st.success(f"data/{SEOUL_PATH.name} 저장 완료 ({area} {len(seoul):,}곳)")
    except PermissionError:
        st.error(f"{SEOUL_PATH.name}이(가) 엑셀에서 열려 있어 저장하지 못했어요. 엑셀을 닫고 다시 눌러 주세요")

st.caption("출처: data/park_data.csv (공공데이터)")
