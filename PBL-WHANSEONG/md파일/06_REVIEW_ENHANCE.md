# 06. 강의평가 기반 추천 고도화

- 브랜치: `feat/recommendation`
- 선행 조건: `04_RECOMMEND_LOGIC`, `05_PAGE_RECOMMEND` 완료 (같은 브랜치 내 마지막 단계)
- 완료 후: `dev`에 머지

## 목적
`CourseReview`(평점 + 후기) 데이터를 추천 정렬에 반영해,
같은 카테고리 내 후보 과목 중 평가가 좋은 과목을 우선 추천하도록 고도화한다.

## 배경
`Course.avgRating`은 `CourseReview` 등록/수정 시마다 실시간 갱신됨 (`ReviewService` 참고).
현재 `courses.html`의 "평점순 정렬"과 동일한 데이터를 추천 로직에서도 활용 가능.

## 설계
`04_RECOMMEND_LOGIC`의 1차 정렬(부족 카테고리 → 학점 큰 순)에
2차 기준으로 `avgRating` 내림차순을 추가.

우선순위 예시:
1. 부족 학점이 큰 카테고리 우선
2. 동일 카테고리 내: `avgRating` 높은 순
3. 평점이 동일하거나 리뷰 수가 적어(예: 3건 미만) 신뢰도가 낮은 경우 처리 방식 결정 (표시만 하되 순위 가중치는 낮춤 등)

## 작업 항목
- [ ] `RecommendService` 정렬 로직에 `avgRating` 반영
- [ ] 리뷰 수(신뢰도) 고려 여부 팀 합의 (`CourseReviewRepository`에 카운트 쿼리 추가 필요 시)
- [ ] 추천 화면(`05_PAGE_RECOMMEND`)에 평점/리뷰 요약 노출

## 완료 조건 (Definition of Done)
- 동일 부족 카테고리 내에서 평점 높은 과목이 상단에 노출됨
- 기존 `courses.html` 평점순 정렬과 일관된 데이터(`avgRating`) 사용
- 추천 묶음(`feat/recommendation`)의 마지막 작업 — 완료 시 `dev` 머지 준비 완료
