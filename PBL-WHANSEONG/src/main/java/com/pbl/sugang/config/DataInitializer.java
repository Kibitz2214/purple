package com.pbl.sugang.config;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.CompletedCourse;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.CourseReview;
import com.pbl.sugang.domain.GraduationRequirement;
import com.pbl.sugang.domain.Department;
import com.pbl.sugang.domain.RequiredCourse;
import com.pbl.sugang.domain.Staff;
import com.pbl.sugang.domain.StaffRole;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.repository.CompletedCourseRepository;
import com.pbl.sugang.repository.CourseRepository;
import com.pbl.sugang.repository.CourseReviewRepository;
import com.pbl.sugang.repository.DepartmentRepository;
import com.pbl.sugang.repository.GraduationRequirementRepository;
import com.pbl.sugang.repository.RequiredCourseRepository;
import com.pbl.sugang.repository.StaffRepository;
import com.pbl.sugang.repository.StudentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Stream;

/** 최초 1회 샘플 데이터(학생/강의/강의평가/졸업요건) 생성 */
@Component
@RequiredArgsConstructor
public class DataInitializer implements CommandLineRunner {

    private static final String CSE_DEPT = "컴퓨터공학과";

    private final StudentRepository studentRepository;
    private final CourseRepository courseRepository;
    private final CourseReviewRepository reviewRepository;
    private final GraduationRequirementRepository requirementRepository;
    private final RequiredCourseRepository requiredCourseRepository;
    private final CompletedCourseRepository completedCourseRepository;
    private final StaffRepository staffRepository;
    private final DepartmentRepository departmentRepository;

    @Override
    public void run(String... args) {
        // 학과 목록 — 졸업요건 등록 화면의 학과 선택지가 된다.
        // 강의나 학생이 아직 없는 학과에도 요건을 먼저 등록할 수 있어야 하므로 별도로 채워 둔다.
        if (departmentRepository.count() == 0) {
            departmentRepository.saveAll(Stream.of(
                    CSE_DEPT, "교양", "경영학과", "전자공학과", "기계공학과", "건축학과",
                    "간호학과", "물리치료학과", "작업치료학과", "응급구조학과", "보건행정학과",
                    "사회복지학과", "유아교육과", "심리학과", "실용음악학과", "뷰티디자인학과",
                    "항공서비스학과", "반려동물학과", "소방안전학과", "영어영문학과"
            ).map(name -> Department.builder().name(name).build()).toList());
        }

        // 교수·조교 샘플 계정 — 교수 이름은 강의의 교수명과 같아야 담당 강의가 연결된다
        if (staffRepository.count() == 0) {
            staffRepository.saveAll(List.of(
                    Staff.builder().loginId("prof-hong").name("홍길동").department(CSE_DEPT).role(StaffRole.PROFESSOR).build(),
                    Staff.builder().loginId("prof-kim").name("김교수").department(CSE_DEPT).role(StaffRole.PROFESSOR).build(),
                    Staff.builder().loginId("prof-lee").name("이교수").department(CSE_DEPT).role(StaffRole.PROFESSOR).build(),
                    Staff.builder().loginId("ta-cse").name("박조교").department(CSE_DEPT).role(StaffRole.ASSISTANT).build()
            ));
        }

        if (studentRepository.count() == 0) {
            studentRepository.saveAll(List.of(
                    Student.builder().studentNo("20210001").name("준호").department("컴퓨터공학과").grade(3).admissionYear(2021).build(),
                    Student.builder().studentNo("20210002").name("태현").department("컴퓨터공학과").grade(3).admissionYear(2021).build(),
                    Student.builder().studentNo("20210003").name("환성").department("컴퓨터공학과").grade(3).admissionYear(2021).build()
            ));
        }

        if (courseRepository.count() == 0) {
            courseRepository.saveAll(List.of(
                    course("CSE101", "자료구조", "홍길동", 3, Category.MAJOR_REQUIRED, "컴퓨터공학과", 40, "월", 1, 3, "공학관 301", 4.6),
                    course("CSE102", "운영체제", "김교수", 3, Category.MAJOR_REQUIRED, "컴퓨터공학과", 35, "화", 2, 4, "공학관 302", 4.2),
                    course("CSE201", "데이터베이스", "이교수", 3, Category.MAJOR_REQUIRED, "컴퓨터공학과", 30, "수", 3, 5, "공학관 401", 4.8),
                    course("CSE202", "웹프로그래밍", "최교수", 3, Category.MAJOR_ELECTIVE, "컴퓨터공학과", 30, "목", 1, 3, "공학관 402", 4.5),
                    course("CSE203", "인공지능개론", "정교수", 3, Category.MAJOR_ELECTIVE, "컴퓨터공학과", 25, "금", 2, 4, "공학관 403", 4.7),
                    course("BUS101", "경영학원론", "강교수", 3, Category.MAJOR_REQUIRED, "경영학과", 50, "월", 4, 6, "경상관 201", 3.9),
                    course("GEN101", "대학영어", "Smith", 2, Category.GENERAL_REQUIRED, "교양", 60, "화", 5, 6, "인문관 101", 4.0),
                    course("GEN102", "글쓰기와의사소통", "윤교수", 2, Category.GENERAL_REQUIRED, "교양", 60, "수", 1, 2, "인문관 102", 4.1),
                    course("GEN201", "심리학의이해", "한교수", 2, Category.GENERAL_ELECTIVE, "교양", 80, "목", 5, 6, "사회관 301", 4.4),
                    course("GEN202", "현대사회와윤리", "조교수", 2, Category.GENERAL_ELECTIVE, "교양", 80, "금", 6, 7, "사회관 302", 3.7)
            ));
        }

        // 샘플 강의평가 (강의/학생이 모두 준비된 경우 1회)
        if (reviewRepository.count() == 0
                && courseRepository.count() > 0 && studentRepository.count() > 0) {
            Student s1 = studentRepository.findByStudentNo("20210001").orElse(null);
            Student s2 = studentRepository.findByStudentNo("20210002").orElse(null);
            Student s3 = studentRepository.findByStudentNo("20210003").orElse(null);
            Course cse101 = findCourse("CSE101");
            Course cse201 = findCourse("CSE201");

            if (s1 != null && s2 != null && cse201 != null) {
                review(s1, cse201, 5, "DB 설계부터 SQL까지 실무에 바로 쓸 수 있게 가르쳐 주세요. 강추!");
                review(s2, cse201, 4, "과제가 조금 많지만 그만큼 확실하게 배웁니다.");
            }
            if (s1 != null && s3 != null && cse101 != null) {
                review(s1, cse101, 5, "자료구조 개념을 그림으로 차근차근 설명해 주셔서 이해가 잘 돼요.");
                review(s3, cse101, 4, "기초가 부족해도 따라갈 수 있었어요.");
            }
        }

        // 졸업요건 (컴퓨터공학과)
        if (requirementRepository.findByDepartment(CSE_DEPT).isEmpty()) {
            requirementRepository.saveAll(List.of(
                    GraduationRequirement.builder().department(CSE_DEPT).admissionYear(2021).category(Category.MAJOR_REQUIRED).requiredCredits(30).build(),
                    GraduationRequirement.builder().department(CSE_DEPT).admissionYear(2021).category(Category.MAJOR_ELECTIVE).requiredCredits(21).build(),
                    GraduationRequirement.builder().department(CSE_DEPT).admissionYear(2021).category(Category.GENERAL_REQUIRED).requiredCredits(12).build(),
                    GraduationRequirement.builder().department(CSE_DEPT).admissionYear(2021).category(Category.GENERAL_ELECTIVE).requiredCredits(6).build()
            ));
        }

        // 필수 지정 과목 (컴퓨터공학과)
        if (requiredCourseRepository.findByDepartment(CSE_DEPT).isEmpty()) {
            List<Course> required = List.of(findCourse("CSE101"), findCourse("CSE102"), findCourse("CSE201"));
            requiredCourseRepository.saveAll(required.stream()
                    .map(c -> RequiredCourse.builder().department(CSE_DEPT).course(c).build())
                    .toList());
        }

        // 샘플 수강 이력 (학생별 이수 완료 과목)
        if (completedCourseRepository.count() == 0) {
            Student s1 = studentRepository.findByStudentNo("20210001").orElse(null);
            Student s2 = studentRepository.findByStudentNo("20210002").orElse(null);
            Course cse101 = findCourse("CSE101");
            Course cse102 = findCourse("CSE102");
            Course cse201 = findCourse("CSE201");
            Course cse202 = findCourse("CSE202");
            Course gen101 = findCourse("GEN101");
            Course gen102 = findCourse("GEN102");
            Course gen201 = findCourse("GEN201");

            if (s1 != null) {
                completedCourseRepository.saveAll(List.of(
                        completed(s1, cse101, 2022, 1),
                        completed(s1, cse102, 2022, 2),
                        completed(s1, cse201, 2023, 1),
                        completed(s1, cse202, 2023, 2),
                        completed(s1, gen101, 2021, 1),
                        completed(s1, gen102, 2021, 2),
                        completed(s1, gen201, 2022, 1)
                ));
            }
            if (s2 != null) {
                completedCourseRepository.saveAll(List.of(
                        completed(s2, cse101, 2022, 1),
                        completed(s2, cse202, 2023, 1),
                        completed(s2, gen101, 2021, 1)
                ));
            }
            // 환성(20210003)은 아직 이수한 과목이 없는 상태로 남겨 둠
        }
    }

    private CompletedCourse completed(Student student, Course course, int year, int semester) {
        return CompletedCourse.builder()
                .student(student).course(course)
                .completedYear(year).completedSemester(semester)
                .build();
    }

    private Course findCourse(String code) {
        return courseRepository.findAll().stream()
                .filter(c -> c.getCourseCode().equals(code))
                .findFirst().orElse(null);
    }

    private void review(Student student, Course course, int rating, String comment) {
        reviewRepository.save(CourseReview.builder()
                .student(student).course(course).rating(rating).comment(comment).build());
        Double avg = reviewRepository.averageRating(course);
        course.updateAvgRating(avg == null ? 0.0 : avg);
        courseRepository.save(course);
    }

    private Course course(String code, String name, String prof, int credit, Category category,
                          String dept, int capacity, String day, int start, int end,
                          String room, double rating) {
        return Course.builder()
                .courseCode(code).name(name).professor(prof).credit(credit).category(category)
                .department(dept).capacity(capacity).dayOfWeek(day).startPeriod(start).endPeriod(end)
                .classroom(room).avgRating(rating)
                .build();
    }
}
