# 01. 졸업요건 데이터 구축 (시더 / 입력)

- 브랜치: `feat/graduation-base`
- 선행 조건: `00_GRADUATION_SCHEMA` 완료 (엔티티/리포지토리 존재)
- 완료 후: `dev`에 push → `feat/analysis`, `feat/recommendation`이 pull 받고 시작

## 목적
`GraduationRequirement`(및 필요 시 `RequiredCourse`) 샘플 데이터를 실제 값으로 채워
분석/추천 로직 개발 시 바로 사용할 수 있도록 한다.

## 배경
`DataInitializer`(`config` 패키지)가 앱 최초 실행 시 `Student`, `Course` 샘플 데이터를 자동 생성한다.
같은 방식으로 `GraduationRequirement` 시드를 추가한다.

기존 샘플 학생 (README 기준):

| 학번 | 이름 | 학과 | 학년 | 입학년도 |
|---|---|---|---|---|
| 20210001 | 이영동 | 컴퓨터공학과 | 3 | 2021 |
| 20240002 | 김창신 | 컴퓨터공학과 | 1 | 2024 |
| 20230003 | 박수강 | 경영학과 | 2 | 2023 |

→ `department+admissionYear` 조합 기준으로 총 3개 조합(컴퓨터공학과-2021, 컴퓨터공학과-2024,
경영학과-2023)의 졸업요건 데이터가 필요하다. 학과 수(2개)가 아니라 조합 수(3개) 기준이다.

## 작업 항목
- [ ] `DataInitializer`에 `GraduationRequirement` 시드 추가
  - 컴퓨터공학과 (2021, 2024 입학년도)
  - 경영학과 (2023 입학년도)
- [ ] 각 학과 이수구분별 요구 학점 값 결정 (실제 창신대 교육과정 기준 또는 임시값 합의)
- [ ] (선택) `RequiredCourse` 시드 — 전공필수 지정 과목이 있다면 `Course` 시드와 매칭
- [ ] 시드 데이터로 `Student` 샘플 3명 모두 `GraduationRequirement`를 조회 가능한지 확인

## 완료 조건 (Definition of Done)
- 앱 기동 시 `GraduationRequirement` 데이터가 자동 삽입됨
- 샘플 학생 3명 모두 자신의 학과/입학년도에 맞는 요건 데이터를 조회할 수 있음
- `02_ANALYSIS_SERVICE`가 실제 데이터로 바로 로직을 검증할 수 있는 상태
