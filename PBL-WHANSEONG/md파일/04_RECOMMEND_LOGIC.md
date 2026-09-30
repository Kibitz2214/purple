# 04. 우선 수강 추천 로직

- 브랜치: `feat/recommendation`
- 선행 조건: `dev`에 머지된 `00`/`01` (기반), `02_ANALYSIS_SERVICE`의 `GraduationStatus` API
- 진행 방식: `feat/analysis`가 `dev`에 먼저 머지되면 `feat/recommendation`은 `dev`를 최신화(rebase 또는 merge)한 뒤 이어서 작업
- 완료 후: `dev`에 머지

## 목적
`AnalysisService`가 계산한 "부족 카테고리"를 기반으로,
학생이 우선적으로 들어야 할 개설 과목을 추천하는 로직을 만든다.

## 설계

### RecommendService (신규, `service` 패키지)
```
List<Course> recommend(Student student)
```

### 후보 필터링
1. `GraduationStatus`에서 `remaining > 0`인 카테고리 목록 추출
2. 해당 카테고리에 속하는 개설 `Course` 중:
   - 이미 수강한(`Enrollment` 존재) 과목 제외
   - 정원 초과(`isFull()`) 과목 제외
   - 학생의 기존 시간표와 `conflictsWith()` 충돌하는 과목 제외
3. 1차 정렬 기준 (본 단계 범위): 부족 학점이 큰 카테고리 우선 → 같은 카테고리 내에서는 학점(credit) 큰 순
   - 평점 기반 정렬 고도화는 `06_REVIEW_ENHANCE`에서 다룸

## 작업 항목
- [ ] `RecommendService.recommend(Student)` 구현
- [ ] 필터링 조건(수강 완료/정원초과/시간표충돌) 단위 테스트
- [ ] 정렬 기준 팀 합의 및 구현
- [ ] 추천 결과 개수 제한 정책 결정 (예: 카테고리별 상위 N개)

## 완료 조건 (Definition of Done)
- 부족 카테고리가 없는 학생은 추천 목록이 비어있음(=졸업요건 충족)
- 시간표 충돌/정원초과 과목이 추천 목록에 나오지 않음
- `05_PAGE_RECOMMEND`가 바로 소비할 수 있는 서비스 API 확정
