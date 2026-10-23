"""memo.txt 의 (가게이름, 주소) 가 실제로 있는지 카카오 장소 검색으로 판정한다.

✅ 이름이 같은 곳이 있고 주소의 구·동(길)이 맞음 / 🟡 있지만 주소가 다름 / ❌ 못 찾음

읽을 수 있는 형식 (줄 앞 번호 1. 2) · 글머리 • - · 표 기호 | --- | 는 떼고 읽음)
  가게이름 | 주소                     ← 한 줄
  • 가게이름  /  • 도로명 주소: 주소     ← 두 줄
"""
import re
import sys
import time

from place import search_place

파일 = sys.argv[1] if len(sys.argv) > 1 else "memo.txt"
최대_줄 = 30  # 쿼터·예절: 한 번에 30곳까지만 검색

시도 = ("서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기",
      "강원", "충북", "충남", "충청", "전북", "전남", "전라", "경북", "경남", "경상", "제주")


def 파일_읽기(경로):
    for 인코딩 in ("utf-8-sig", "cp949"):
        try:
            with open(경로, encoding=인코딩) as f:
                return f.read(), 인코딩
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"'{경로}' 를 utf-8-sig · cp949 로 읽지 못했어요")


def 줄_정리(줄):
    """글머리·번호·표 기호를 뗀다."""
    줄 = 줄.strip().strip("|").strip()
    줄 = re.sub(r"^[•·\-*]\s*", "", 줄)
    줄 = re.sub(r"^\d+\s*[.)]\s*", "", 줄)
    return 줄.strip()


def 주소_줄인가(줄):
    return "주소" in 줄.split(":")[0] and ":" in 줄 or 줄.startswith(시도)


def 주소_꺼내기(줄):
    return 줄.split(":", 1)[1].strip() if ":" in 줄 and "주소" in 줄.split(":")[0] else 줄


def 목록_만들기(글):
    목록, 이름 = [], None
    for 원래 in 글.splitlines():
        if re.fullmatch(r"[\s|:\-]*", 원래):  # 빈 줄, | --- | 줄
            continue
        줄 = 줄_정리(원래)
        if "|" in 줄:
            칸 = [c.strip() for c in 줄.split("|") if c.strip()]
            if 칸 and 칸[0].isdigit():  # | 1 | 이름 | 주소 | 처럼 번호 칸이 있을 때
                칸 = 칸[1:]
            if len(칸) >= 2 and 칸[1] != "주소":  # 표 머리줄(이름 | 주소)은 건너뜀
                목록.append((칸[0], 주소_꺼내기(칸[1])))
            이름 = None
        elif 주소_줄인가(줄):
            if 이름:
                목록.append((이름, 주소_꺼내기(줄)))
                이름 = None
        elif 줄:
            이름 = 줄
    return 목록


def 구_동길(주소):
    """첫 단어(서울특별시/서울)는 빼고, 구 이름과 동·로·길 이름을 꺼낸다."""
    단어들 = 주소.split()[1:]
    구 = next((w for w in 단어들 if w.endswith(("구", "군"))), None)
    동길 = next((w for w in 단어들 if re.search(r"(동|\d*가|로|길)$", w) and w != 구), None)
    return 구, 동길


def 같은_이름(a, b):
    return a.replace(" ", "").lower() == b.replace(" ", "").lower()


def 판정(이름, 주소):
    구, 동길 = 구_동길(주소)
    검색어 = f"{구} {이름}" if 구 else 이름
    try:
        후보들 = search_place(검색어, 개수=15)
    except RuntimeError as 에러:
        if str(에러).startswith("⛔"):
            raise
        return "❌", None
    같은곳 = [p for p in 후보들 if 같은_이름(p["이름"], 이름)]
    if not 같은곳:
        return "❌", None
    for p in 같은곳:
        k구, k동길 = 구_동길(p["주소"])
        if k구 == 구 and (동길 is None or k동길 == 동길):
            return "✅", p
    return "🟡", 같은곳[0]


if __name__ == "__main__":
    try:
        글, 인코딩 = 파일_읽기(파일)
    except (OSError, RuntimeError) as 에러:
        print(f"'{파일}' 를 열지 못했어요" if isinstance(에러, OSError) else 에러)
        sys.exit(1)
    목록 = 목록_만들기(글)
    print(f"'{파일}' 를 {인코딩} 로 읽었어요 → 가게 {len(목록)}곳")
    if len(목록) > 최대_줄:
        print(f"{최대_줄}곳까지만 검사해요")
        목록 = 목록[:최대_줄]

    개수 = {"✅": 0, "🟡": 0, "❌": 0}
    for 번호, (이름, 주소) in enumerate(목록, start=1):
        try:
            결과, 장소 = 판정(이름, 주소)
        except RuntimeError as 에러:
            print(에러)
            print("키·설정·연결 문제라 여기서 멈춰요")
            break
        개수[결과] += 1
        print(f"{번호}. {결과} {이름} | {주소}")
        if 장소 and 결과 == "🟡":
            print(f"      카카오: {장소['이름']} | {장소['주소']}")
        time.sleep(0.1)

    합계 = sum(개수.values())
    if 합계:
        실수율 = (개수["🟡"] + 개수["❌"]) / 합계 * 100
        print(f"\n✅ {개수['✅']}곳 · 🟡 {개수['🟡']}곳 · ❌ {개수['❌']}곳 (전체 {합계}곳)")
        print(f"AI 실수율: {실수율:.1f}%  = (🟡 + ❌) ÷ 전체")
        print("판정 조건: 이름은 띄어쓰기·대소문자만 무시하고 똑같아야 함,"
              " 주소는 첫 단어를 빼고 구 + 동·로·길 이름이 같아야 함 (건물 번호·층은 안 봄)")
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색)")
