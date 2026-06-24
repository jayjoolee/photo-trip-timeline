[English](https://github.com/jayjoolee/photo-trip-timeline/blob/main/README.md) | [简体中文](https://github.com/jayjoolee/photo-trip-timeline/blob/main/README.zh-CN.md) | 한국어

<h1 align="center">photo-trip-timeline</h1>

<p align="center">
Apple 사진에서 여행을 자동으로 찾아 공유 가능한 마크다운 여행 타임라인을 만듭니다 —<br>
<b>장소 이름만 담기고, GPS 좌표는 절대 Mac을 벗어나지 않습니다.</b>
</p>

<p align="center">
<a href="https://github.com/jayjoolee/photo-trip-timeline/actions/workflows/ci.yml"><img src="https://github.com/jayjoolee/photo-trip-timeline/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python 3.10+"></a>
<a href="https://github.com/jayjoolee/photo-trip-timeline/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License: MIT"></a>
<a href="https://github.com/jayjoolee/photo-trip-timeline/blob/main/CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen" alt="PRs welcome"></a>
</p>

<p align="center">
<img src="https://raw.githubusercontent.com/jayjoolee/photo-trip-timeline/main/assets/demo.gif" alt="phototrips --demo" width="800">
</p>

여행을 다녀오면 사진은 수백 장인데, 정리가 귀찮아 글쓰기는 늘 미뤄집니다. 사실 아이폰은
모든 사진에 **언제**와 **어디서**를 이미 새겨두고, Apple 사진은 그 좌표를 **장소 이름**으로
바꿔둡니다. `photo-trip-timeline`은 이걸 기기 안에서 읽어, 어떤 사진이 어느 여행에 속하는지
판단하고, 어디를 다녀왔는지 날짜별로 깔끔한 타임라인을 써줍니다 — **공유하는 파일에는 좌표가
절대 들어가지 않습니다.**

**[설치](#설치) · [빠른 시작](#빠른-시작) · [프라이버시 설계](#프라이버시-설계) · [작동 원리](#작동-원리)**

```markdown
# Photo Travel Timeline

## Busan 2-day trip — 2024.05.03–05.04 (2 days, 142 photos)
Haeundae Beach → Gamcheon Culture Village → Jagalchi Market
- Day 1 (05.03): Haeundae Beach — 51 photos
- Day 2 (05.04): Gamcheon Culture Village, Jagalchi Market — 91 photos
```

*(`phototrips --demo`로 바로 확인하세요 — 사진 보관함 없이 동작합니다. 한국어 출력은 `--lang ko`.)*

## 주요 기능

- 🔒 **좌표는 Mac을 벗어나지 않음** — `timeline.md`에는 장소 이름만 들어가며, 위경도 형태의
  토큰이 섞이면 쓰기 단계의 단언이 실행을 중단시킵니다.
- 🏠 **실패 시 멈추는(fail-closed) 집 탐지** — 집을 높은 확신으로 특정하지 못하면, 추측해서
  집 근처 좌표를 흘리는 대신 멈추고 물어봅니다.
- 🗺️ **여행 자동 분할** — 집 기준 경계(귀가, 공백, 비행 규모 점프, 육로 장거리 이동); 해외
  여행 중의 조용한 휴식일이 하나의 여행을 쪼개지 않습니다.
- 📍 **날짜별 동선** — 여행마다 방문한 장소들을 군집화해 읽기 좋은 동선으로 정렬하고,
  날짜별 사진 수를 함께 보여줍니다.
- 🌏 **다국어 출력** — `--lang en | ko | zh`로 타임라인 언어 전환; 이 README는 영어, 简体中文,
  한국어로 제공됩니다.
- 🧪 **신뢰할 수 있음** — 알고리즘 코어는 `osxphotos`에 의존하지 않으며, 합성 데이터로 도는
  31개 테스트로 검증됩니다. Mac이 필요 없습니다.

## 설치

```bash
git clone https://github.com/jayjoolee/photo-trip-timeline
cd photo-trip-timeline
pip install -e .
```

Apple 사진 앱이 있는 macOS, Python ≥ 3.10, 그리고 `osxphotos`(자동 설치)가 필요합니다.
Apple 사진 보관함 버전 5001에서 검증했으며, `osxphotos`는 다른 버전도 읽습니다.

## 빠른 시작

```bash
# 집을 자동 탐지하고 ./output/{timeline.md, trips.json} 생성
phototrips

# 보관함을 건드리지 않고 예시 출력 바로 보기:
phototrips --demo
```

## 사용법

```bash
phototrips --lang ko                 # 한국어 타임라인 (en | ko | zh; 기본 en)
phototrips --since 2022-07-01        # 특정 날짜 이후 사진만
phototrips --library /path/to/X.photoslibrary

# 집을 확신 있게 탐지하지 못하면 추측하지 않습니다. 둘 중 하나:
phototrips --home-lat 37.5665 --home-lon 126.9780   # 집 좌표를 직접 알려주기
phototrips --no-coords                              # 또는 장소 이름만 출력

phototrips --include-names           # trips.json에 인물 이름 포함 (기본 꺼짐)
```

`--home-lat/--home-lon` 쌍을 여러 개(선택적으로 `--home-from/--home-until`과 함께) 주면
해당 기간에 이사한 경우도 처리됩니다.

두 개의 파일을 생성합니다:

- **`timeline.md`** — 공유 가능한, 사람이 읽는 타임라인. **장소 이름만, 좌표 없음**이라
  블로그 초안에 그대로 붙여넣어도 안전합니다.
- **`trips.json`** — 구조화된 기록(gitignore됨)으로, 블로그 초안 단계의 입력이 됩니다.

### 블로그 초안

`phototrips draft`는 한 여행을 **프롬프트 팩**으로 만듭니다 — 여행 정보(날짜, 날짜별 동선,
주요 장소, 어떤 사진을 넣을지)와 글쓰기 스타일 지침을 한 마크다운 파일에 묶어, Claude /
ChatGPT에 바로 붙여넣어 초안을 받게 합니다. API 키가 필요 없고, 팩에는 장소 이름만 — 좌표는 없습니다.

```bash
phototrips draft --trip auto                 # 사진이 가장 많은 여행
phototrips draft --trip 2025-02-24-rome       # id로 특정 여행 지정
phototrips draft --all --style my-voice.md    # 모든 여행을, 당신의 문체로
phototrips draft --lang en                     # 팩 언어 (ko | en; 기본 ko)
```

`--style path/to/your-style.md`로 당신만의 문체를 넣으세요. 기본 스타일은 `styles/default.md`에
있습니다. 팩은 `output/drafts/`(gitignore됨)에 저장됩니다.

## 프라이버시 설계

이 도구는 당신의 사진을 읽고 사는 곳을 압니다. 그래서 처음부터 프라이버시를 지키도록 만들어졌습니다:

- **`timeline.md`에는 숫자 좌표가 절대 없음** — 장소 이름만, 쓰기 단계 단언으로 보장.
- **집 탐지는 fail-closed** — 확신이 낮으면 추측해서 집 근처 좌표를 흘리는 대신 멈추고 물어봄.
- **`trips.json`, 사진 보관함, `output/`는 gitignore**되며, `pre-commit` 훅이 이들 또는
  좌표 형태 토큰의 커밋을 차단합니다.
- **인물 이름은 옵트인**(`--include-names`); 기본은 개수만 기록.
- **네트워크 없음** — 역지오코딩은 Apple의 기기 내 장소 이름을 사용하며 외부 호출이 없습니다.

[SECURITY.md](https://github.com/jayjoolee/photo-trip-timeline/blob/main/SECURITY.md) 참고.
커밋 가드 설치: `pip install pre-commit && pre-commit install`.

## 기존 도구로는 안 되나요?

사진에서 GPS를 추출하거나 지도에 점을 찍는 프로젝트는 많습니다([osxphotos](https://github.com/RhetTbull/osxphotos),
[mappics](https://github.com/antodippo/mappics) 등). 하지만 정작 여행 블로거가 궁금한 것 —
*“어떤 사진이 한 여행이고, 그 여행은 날짜별로 어디를 갔나?”* — 에는 답하지 못하며, 게다가
집을 지도에 노출하지 않으면서 답하지도 못합니다.

## 작동 원리

1. **추출**(`osxphotos`) — 각 사진의 시간, GPS, Apple의 장소 계층을 보관함에서 직접 읽습니다.
   외부 지오코딩 없이 전부 기기 안에서.
2. **여행으로 분할** — 핵심 단계. 사진은 드문드문이라 단순 밀도 군집으로는 여행 경계를 못
   찾습니다. 그래서 ‘여행’을 집에서 떨어져 보낸 시간으로 정의하고, 집 근처 일상 사진은
   경계로만 쓰고 여행으로 만들지 않습니다. 떨어져 있는 기간 안에서는 긴 공백, 비행 규모의
   점프, 육로 장거리 이동으로 다시 나눕니다.
3. **여행 내 장소 군집**(DBSCAN) — 방문한 서로 다른 장소를 찾아 동선으로 정렬합니다.
4. **이름 짓기 & 요약** — 장소들로 여행 이름을 짓고, 대표 사진을 고르고(Apple 기기 내 미학
   점수 기반), 타임라인과 JSON을 렌더링합니다.

`extract.py`만 `osxphotos`를 건드리고, 그 이후는 전부 평범한 데이터 위에서 돌기 때문에
테스트는 Mac 없이도 알고리즘 전체를 검증합니다.

## 설정

각종 임계값(집과의 거리, 공백 시간, 점프/장거리 거리, 장소 군집 반경 등)은 주석 달린 기본값으로
`config.py`에 있으며 CLI로 덮어쓸 수 있습니다. 전체 목록은 `phototrips --help`로 확인하세요.

## 기여하기

PR 환영합니다 — [CONTRIBUTING.md](https://github.com/jayjoolee/photo-trip-timeline/blob/main/CONTRIBUTING.md) 참고.
`pytest`는 Mac이나 사진 보관함 없이 전체 테스트를 실행합니다. **issue나 PR에 실제 좌표를
붙여넣지 마세요** — `phototrips --demo`나 `tests/`의 합성 데이터로 재현하세요.

## 로드맵

- **블로그 초안** ✅ — `phototrips draft`가 지금 제공됩니다(위 참고). 다음: API 키 설정 시
  LLM 직접 호출 생성, 여행별 사진 내보내기.
- 여행 *제목* 현지화(현재 영어), 선택적 지도 출력(`folium`), PyPI 배포.

## 라이선스

MIT — [LICENSE](https://github.com/jayjoolee/photo-trip-timeline/blob/main/LICENSE) 참고.

---

<sub>영어 `README.md`가 정본이며, 번역은 다소 늦을 수 있습니다.</sub>
<!-- translated from README.md -->
