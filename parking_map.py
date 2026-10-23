"""data/parking_seoul.csv 에서 무료 주차장만 골라 make_map.py 의 kakao_map 으로 마커를 찍은 map.html 을 만든다.

실행:  python parking_map.py
여는 법: 이 폴더에서  python -m http.server 8000 --bind 127.0.0.1  → http://localhost:8000/map.html
"""
from pathlib import Path

import pandas as pd

from make_map import kakao_map

CSV_PATH = Path(__file__).parent / "data" / "parking_seoul.csv"
MAP_PATH = Path(__file__).parent / "map.html"
ENCODINGS = ["utf-8-sig", "cp949"]


def read_csv(path):
    """인코딩을 차례로 시도해 읽고 (표, 읽은 인코딩)을 돌려준다."""
    for encoding in ENCODINGS:
        try:
            return pd.read_csv(path, encoding=encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{', '.join(ENCODINGS)} 어느 것으로도 한글을 읽지 못했어요")


def 요금_글자(요금):
    return "정보 없음" if pd.isna(요금) else f"{int(요금):,}원"


if __name__ == "__main__":
    if not CSV_PATH.exists():
        print(f"'{CSV_PATH.name}'이(가) 없어요. parking.py 에서 먼저 저장해 주세요")
        raise SystemExit

    df, encoding = read_csv(CSV_PATH)
    print(f"읽은 인코딩: {encoding} / {df.shape[0]}줄 × {df.shape[1]}칸")
    print("빈칸 개수:", df.isna().sum().to_dict())

    # "무료" 같은 글자는 0으로 바꾼 뒤 숫자로 (못 바꾸는 값은 빈칸)
    df["주차기본요금"] = pd.to_numeric(df["주차기본요금"].replace("무료", 0), errors="coerce")
    df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
    df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

    if "요금정보" not in df.columns:
        print("parking_seoul.csv 에 '요금정보' 칸이 없어요. parking.py 에서 다시 저장해 주세요")
        raise SystemExit

    무료 = df[df["요금정보"].astype(str).str.strip() == "무료"]
    # 한국 밖(뒤바뀐·0) 좌표는 쓰지 않는다
    한국안 = 무료["위도"].between(33, 39) & 무료["경도"].between(124, 132)
    if (~한국안).sum():
        print(f"좌표가 한국 밖이라 뺀 곳: {(~한국안).sum()}곳")
    무료 = 무료[한국안]

    print(f"\n센 조건: 요금정보 == '무료' (전체 {len(df)}곳 중 무료 {len(무료)}곳)")
    print("요금정보별 개수:", df["요금정보"].value_counts(dropna=False).to_dict())
    기준일 = ", ".join(sorted(df["데이터기준일자"].dropna().astype(str).unique()))
    print(f"데이터 기준일: {기준일}")

    # 지역 이름(예: 서울특별시 강남구)은 주소 앞 두 낱말 중 가장 많은 것
    지역 = df["주소"].dropna().str.split().str[:2].str.join(" ").mode()
    지역 = 지역.iloc[0] if not 지역.empty else "이 지역"

    장소들 = [
        {
            "이름": row["주차장명"],
            # kakao_map 은 정보창 둘째 줄에 '주소' 값을 보여 줌 → 유형·기본 요금을 넣는다
            "주소": f"{row['주차장유형']} · 기본 요금 {요금_글자(row['주차기본요금'])}",
            "위도": row["위도"],
            "경도": row["경도"],
        }
        for _, row in 무료.iterrows()
    ]
    if 장소들:
        알림 = f"{지역} 무료 주차장 {len(장소들)}곳 (기준일 {기준일})"
    else:
        알림 = f"{지역}에는 무료 주차장이 없어요 (전체 {len(df)}곳 모두 유료·혼합, 기준일 {기준일})"

    # 마커가 없을 때는 이 지역 주차장 전체 좌표의 가운데에 지도를 둔다
    좌표 = df[df["위도"].between(33, 39) & df["경도"].between(124, 132)]
    중심 = (좌표["위도"].mean(), 좌표["경도"].mean()) if not 좌표.empty else (37.5665, 126.9780)

    try:
        with open(MAP_PATH, "w", encoding="utf-8") as f:
            f.write(kakao_map(장소들, 제목="무료 주차장 지도", 알림=알림, 중심=중심))
        for 번호, 장소 in enumerate(장소들, start=1):
            print(f"{번호}. {장소['이름']}, {장소['주소']}, ({장소['위도']}, {장소['경도']})")
        print(f"\n{알림}")
        print(f"map.html 을 만들었어요 (마커 {len(장소들)}개)")
        print("여는 법: 이 폴더에서  python -m http.server 8000 --bind 127.0.0.1")
        print("        → 브라우저로 http://localhost:8000/map.html")
    except RuntimeError as 에러:
        print(에러)

    print("\n출처: data/parking_seoul.csv (공공데이터 park_data.csv에서 거른 것) · 카카오 지도 JavaScript SDK")
