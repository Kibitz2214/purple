# 02. 이수현황 분석 로직 (미이수 과목 계산)

- 브랜치: `feat/analysis`
- 선행 조건: `dev`에 머지된 `00_GRADUATION_SCHEMA` + `01_GRADUATION_DATA`
- 완료 후: `dev`에 머지 (`feat/recommendation`은 `dev` rebase/merge로 최신화)
- 참고: `AnalysisService.analyze(Student)` 시그니처와 `GraduationStatus`/`CategoryStatus` DTO는
  `00_GRADUATION_SCHEMA.md`에서 이미 확정됨. 이 단계는 실제 구현만 담당.

## 목적
학생의 `Enrollment` 이력을 `GraduationRequirement`와 비교해
- 이수구분별 취득 학점 / 요구 학점 / 부족 학점을 계산하고
- 아직 이수하지 않은 항목(부족 카테고리)을 판단하는 서비스 로직을 만든다.

## 설계

### AnalysisService (신규, `service` 패키지)
```
GraduationStatus analyze(Student student)
```

### 계산 로직
1. `student.department` + `student.admissionYear`로 `GraduationRequirement` 조회
2. `EnrollmentRepository`에서 해당 학생의 전체 `Enrollment` → `Course.category`별 학점 합산
   - 같은 과목 중복 신청은 없음 (`Enrollment` 유니크 제약: student_id + course_id)
3. 카테고리별 `취득 학점 = Σ course.credit` (해당 category에 속하는 것만)
4. `부족 학점 = max(0, 요구 학점 - 취득 학점)`
5. 총 이수 학점 합계 vs `totalCredit` 비교

### 결과 DTO (제안)
```
GraduationStatus {
  int totalRequired, totalEarned, totalRemaining
  List<CategoryStatus> categories
}
CategoryStatus {
  Category category
  int required, earned, remaining
}
```

## 작업 항목
- [ ] `GraduationStatus`, `CategoryStatus` DTO 작성
- [ ] `AnalysisService.analyze(Student)` 구현
- [ ] 단위 테스트: 요건 충족 / 미충족 / 초과 이수 각각의 케이스
- [ ] `GraduationRequirement`가 없는 학과·입학년도 조회 시 예외/기본값 처리 정책 결정

## 완료 조건 (Definition of Done)
- 샘플 학생 3명 기준으로 카테고리별 부족 학점이 정확히 계산됨
- `03_PAGE_CHECKLIST`, `04_RECOMMEND_LOGIC`이 바로 소비할 수 있는 서비스 API 확정
