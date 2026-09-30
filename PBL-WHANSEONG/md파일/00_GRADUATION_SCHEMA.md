# 00. 졸업요건 엔티티 설계 / ERD 반영

- 브랜치: `feat/graduation-base`
- 선행 조건: 없음 (최초 작업)
- 완료 후: `dev`에 push → `feat/analysis`, `feat/recommendation`이 pull 받고 시작

## 목적
학과 · 입학년도별 졸업요건(이수구분별 요구 학점, 총 이수 학점)을 저장하고,
학생의 `Enrollment` 내역과 비교할 수 있는 데이터 구조를 만든다.

## 배경
기존 도메인:
- `Student` (studentNo, name, department, grade, admissionYear)
- `Course` (courseCode, name, professor, credit, category: `Category`, department, ...)
- `Enrollment` (student, course, enrolledAt)
- `Category`: MAJOR_REQUIRED / MAJOR_ELECTIVE / GENERAL_REQUIRED / GENERAL_ELECTIVE

졸업요건은 `department + admissionYear` 조합으로 다르게 적용되는 것을 기준으로 설계한다
(입학년도별 교육과정 개편 반영).

## 신규 엔티티 (제안)

### GraduationRequirement
학과 · 입학년도별 졸업 기준.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | Long (PK) | |
| department | String | `Student.department`와 매칭 |
| admissionYear | int | `Student.admissionYear`와 매칭 |
| totalCredit | int | 졸업 총 이수학점 |
| majorRequiredCredit | int | 전공필수 요구 학점 |
| majorElectiveCredit | int | 전공선택 요구 학점 |
| generalRequiredCredit | int | 교양필수 요구 학점 |
| generalElectiveCredit | int | 교양선택 요구 학점 |

유니크 제약: `(department, admissionYear)`

### RequiredCourse (선택 — 필요 시 02단계에서 확정)
특정 과목이 무조건 이수되어야 하는 경우(예: 전공필수 지정 과목) 대비.

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | Long (PK) | |
| graduationRequirement | FK → GraduationRequirement | |
| course | FK → Course | 필수 지정 과목 |

> RequiredCourse는 02_ANALYSIS_SERVICE 설계 중 "카테고리별 학점 합산"만으로 충분하면 생략 가능.
> 실제 필요 여부는 분석 로직 설계 시 재확인한다.

## 설계 노트
majorRequiredCredit / majorElectiveCredit / generalRequiredCredit / generalElectiveCredit
4개 컬럼은 Category enum 4종과 1:1로 대응하도록 의도적으로 단순화한 설계다.

이수구분이 추후 추가되면 컬럼 확장이 필요하다는 점을 감안하고 채택한 트레이드오프이며,
현재 프로젝트 범위(4개 고정 카테고리)에서는 별도 테이블/Map 구조보다 개발 속도가 빠르다는 이유로 선택했다.

## ERD 반영 관계
```
Student (department, admissionYear) ──┐
                                       ├─ 매칭 기준
GraduationRequirement (department, admissionYear)

GraduationRequirement 1 ──< RequiredCourse >── 1 Course (선택)
```

## AnalysisService 인터페이스 사전 확정
feat/recommendation이 feat/analysis 완료를 기다리지 않고 병렬로 개발을 시작할 수 있도록,
AnalysisService.analyze(Student) 메서드 시그니처와 GraduationStatus / CategoryStatus
DTO 구조를 이 단계에서 미리 확정한다 (실제 구현은 02에서 진행).

확정된 시그니처:
```
GraduationStatus analyze(Student student)
GraduationStatus { int totalRequired, totalEarned, totalRemaining, List<CategoryStatus> categories }
CategoryStatus { Category category, int required, earned, remaining }
```

feat/recommendation은 이 시그니처를 기준으로 목(mock)/스텁 구현체를 만들어 먼저 개발을 진행할 수 있다.

## 작업 항목
- [ ] `GraduationRequirement` 엔티티 작성 (`domain` 패키지)
- [ ] `GraduationRequirementRepository` 작성 (`findByDepartmentAndAdmissionYear`)
- [ ] (선택) `RequiredCourse` 엔티티/리포지토리
- [ ] ERD 다이어그램 업데이트 (README 또는 별도 `docs/erd.png`)

## 완료 조건 (Definition of Done)
- 엔티티/리포지토리 컴파일 및 애플리케이션 정상 기동
- ERD에 신규 엔티티와 관계가 반영됨
- `01_GRADUATION_DATA`에서 바로 시드 데이터를 넣을 수 있는 상태
