# 창신대 맞춤 수강 도우미 — 수강신청 사이트

2026학년도 RISE사업 비교과 PBL 과제(「창신대 맞춤 수강 도우미」) 기본 틀.
웹 기반 수강신청 사이트의 핵심 기능을 구현한 독립 프로젝트입니다.

> ⚠️ 이 프로젝트는 **foodguard 와 완전히 별개**입니다.
> 디렉터리(`PBL/`), 포트(8081), DB(`pbl_sugang`) 모두 분리되어 있어 서로 충돌하지 않습니다.

## 기술 스택
- Java 17 / Spring Boot 3.5
- Spring Data JPA (Hibernate)
- Thymeleaf (서버 사이드 렌더링)
- MySQL 8.0
- Gradle (wrapper 포함)

## 사전 준비
- JDK 17
- 로컬 MySQL 8.0 (root / 1234) — 실행 중이어야 함
- DB 스키마는 자동 생성되지 않으므로 최초 1회 생성:
  ```sql
  CREATE DATABASE IF NOT EXISTS pbl_sugang
      DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```
  (테이블·샘플 데이터는 앱 최초 실행 시 자동 생성됩니다.)

## 실행
```powershell
.\gradlew.bat bootRun
```
브라우저에서 http://localhost:8081 접속.

## 로그인용 샘플 학번
| 학번 | 이름 | 학과 | 학년 |
|------|------|------|------|
| 20210001 | 준호 | 컴퓨터공학과 | 3 |
| 20210002 | 태현 | 컴퓨터공학과 | 3 |
| 20210003 | 환성 | 컴퓨터공학과 | 3 |

신규 학생은 `/register` 에서 등록할 수 있습니다.

## 구현된 기능
- 학번 기반 로그인 / 학생 등록 (세션)
- 개설 강의 목록 조회
- 검색(과목명·교수명) / 이수구분 필터 / 평점순 정렬
- 수강신청 / 취소
  - 중복 신청 방지
  - 정원 초과 방지
  - 시간표 충돌 검증
- 내 신청내역(시간표) · 신청 학점 합계
- **강의평가** (과목명 클릭 → 강의 상세)
  - 평점(1~5) + 한줄 후기 작성 / 수정 / 삭제 (학생당 강의별 1건)
  - 평가 평균이 강의 목록 평점에 실시간 반영 (평점순 정렬과 연동)

## 구조
```
src/main/java/com/pbl/sugang/
  ├─ domain/      엔티티 (Student, Course, Enrollment, CourseReview, Category)
  ├─ repository/  Spring Data JPA 리포지토리
  ├─ service/     업무 로직 (수강신청 검증 등)
  ├─ controller/  웹 컨트롤러 (로그인/강의/수강신청)
  └─ config/      샘플 데이터 초기화
src/main/resources/
  ├─ templates/   Thymeleaf 화면 (login, register, courses, my)
  ├─ static/css/  스타일시트
  └─ application.properties
```

## 향후 확장 (과제 계획서 기준)
- 학과·학번별 졸업요건 자동 분석 및 미이수 과목 표시
- 졸업요건 우선 매칭 과목 추천
- 강의평가(평점/후기) 데이터 수집 및 추천 정렬 고도화
