"""place.py 의 search_place 로 장소 10개를 찾아 카카오 지도 위에 마커로 찍은 map.html 을 만든다.

다른 파일에서:  from make_map import kakao_map   (HTML 글자를 돌려준다)
REST 키는 HTML에 넣지 않는다. 지도에는 KAKAO_JS_KEY 만 쓴다.
"""
import json
import os

from dotenv import load_dotenv

from place import search_place

API = {
    "지도SDK": "https://dapi.kakao.com/v2/maps/sdk.js",  # 🔌 카카오 지도 JavaScript SDK (브라우저가 부름)
}

load_dotenv(override=True)

최대_마커 = 200

HTML_틀 = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__제목__</title>
<style>
  body { margin: 0; font-family: sans-serif; }
  #map { width: 100%; height: 500px; background: #ddd; }
  .안내 { padding: 8px 12px; font-size: 14px; color: #555; }
  .말풍선 { padding: 6px 10px; font-size: 13px; line-height: 1.4; min-width: 160px; }
  .말풍선 b { display: block; }
  .알림 { margin: 0; padding: 10px 12px; font-size: 15px; background: #fff8e1; border-bottom: 1px solid #f0d58c; }
</style>
</head>
<body>
__알림__<div id="map"></div>
<p class="안내">지도가 회색이면: ① 카카오맵 사용 설정 ② 지금 주소(포트까지) 등록 ③ 서버 주소로 열기</p>
<script src="__SDK__?appkey=__JS키__&autoload=false"></script>
<script>
const 장소들 = __데이터__;
kakao.maps.load(function () {
  const map = new kakao.maps.Map(document.getElementById("map"), {
    center: new kakao.maps.LatLng(__중심위도__, __중심경도__),
    level: 5,
  });
  const 범위 = new kakao.maps.LatLngBounds();
  let 열린창 = null;

  장소들.forEach(function (장소) {
    const 위치 = new kakao.maps.LatLng(장소.위도, 장소.경도);  // (위도, 경도) 순서
    const 마커 = new kakao.maps.Marker({ map: map, position: 위치 });
    범위.extend(위치);

    // 이름·주소는 textContent 로 넣어 따옴표·태그가 있어도 안 깨지게
    const 내용 = document.createElement("div");
    내용.className = "말풍선";
    const 이름 = document.createElement("b");
    이름.textContent = 장소.이름;
    const 주소 = document.createElement("span");
    주소.textContent = 장소.주소;
    내용.append(이름, 주소);
    const 창 = new kakao.maps.InfoWindow({ content: 내용, removable: true });

    kakao.maps.event.addListener(마커, "click", function () {
      if (열린창) 열린창.close();
      창.open(map, 마커);
      열린창 = 창;
    });
  });

  if (장소들.length > 1) {
    map.setBounds(범위);
  } else if (장소들.length === 1) {
    map.setCenter(new kakao.maps.LatLng(장소들[0].위도, 장소들[0].경도));
  }
});
</script>
</body>
</html>
"""


def kakao_map(장소들, 제목="카카오 지도", 알림=None, 중심=(37.5665, 126.9780)):
    """[{이름, 주소, 위도, 경도}, ...] 를 마커로 찍은 지도 HTML 글자를 돌려준다.

    알림: 지도 위에 보여 줄 안내 한 줄 (없으면 안 보임)
    중심: 마커가 없을 때 지도를 둘 (위도, 경도). 마커가 있으면 마커에 맞춘다.

    KAKAO_JS_KEY 가 없으면 한국어 한 줄로 RuntimeError 를 낸다.
    """
    js키 = os.getenv("KAKAO_JS_KEY")
    if not js키:
        raise RuntimeError("⛔ .env 에 KAKAO_JS_KEY 가 없어요")

    데이터 = [
        {"이름": p["이름"], "주소": p["주소"], "위도": p["위도"], "경도": p["경도"]}
        for p in 장소들[:최대_마커]
    ]
    # json.dumps 로 넣고, 이름에 </script> 가 있어도 스크립트가 끊기지 않게 </ 를 바꾼다
    데이터_글자 = json.dumps(데이터, ensure_ascii=False).replace("</", "<\\/")
    제목_글자 = 제목.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    알림_글자 = ""
    if 알림:
        알림_글자 = '<p class="알림">' + 알림.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") + "</p>\n"

    return (
        HTML_틀.replace("__SDK__", API["지도SDK"])
        .replace("__JS키__", js키)
        .replace("__제목__", 제목_글자)
        .replace("__알림__", 알림_글자)
        .replace("__중심위도__", str(float(중심[0])))
        .replace("__중심경도__", str(float(중심[1])))
        .replace("__데이터__", 데이터_글자)  # 장소 이름에 __제목__ 같은 글자가 있어도 안 바뀌게 맨 마지막
    )


if __name__ == "__main__":
    검색어 = input("검색어를 입력하세요 (예: 성수동 카페): ").strip()
    if not 검색어:
        print("검색어가 비어 있어요")
    else:
        try:
            장소들 = search_place(검색어, 개수=10)
            with open("map.html", "w", encoding="utf-8") as f:
                f.write(kakao_map(장소들, 제목=f"{검색어} 지도"))
            for 번호, 장소 in enumerate(장소들, start=1):
                print(f"{번호}. {장소['이름']}, {장소['주소']}, ({장소['위도']}, {장소['경도']})")
            print(f"\nmap.html 을 만들었어요 (마커 {len(장소들)}개)")
            print("여는 법: 이 폴더에서  python -m http.server 8000 --bind 127.0.0.1")
            print("        → 브라우저로 http://localhost:8000/map.html")
        except RuntimeError as 에러:
            print(에러)
    print("\n출처: 카카오 로컬 API (키워드로 장소 검색) · 카카오 지도 JavaScript SDK")
