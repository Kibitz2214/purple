package com.pbl.sugang.service;

import com.pbl.sugang.domain.ClassPeriod;
import com.pbl.sugang.domain.CompletedCourse;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.Enrollment;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.repository.CompletedCourseRepository;
import com.pbl.sugang.repository.CourseRepository;
import com.pbl.sugang.repository.EnrollmentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class EnrollmentService {

    public static final List<String> TIMETABLE_DAYS = List.of("월", "화", "수", "목", "금");
    public static final int TIMETABLE_MAX_PERIOD = ClassPeriod.MAX_PERIOD;

    private final EnrollmentRepository enrollmentRepository;
    private final CourseRepository courseRepository;
    private final CompletedCourseRepository completedCourseRepository;

    @Transactional(readOnly = true)
    public List<Enrollment> findByStudent(Student student) {
        return enrollmentRepository.findByStudent(student);
    }

    @Transactional(readOnly = true)
    public int totalCredits(Student student) {
        return enrollmentRepository.findByStudent(student).stream()
                .mapToInt(e -> e.getCourse().getCredit())
                .sum();
    }

    /** 수강신청: 중복/정원/시간표 충돌 검증 후 등록 */
    @Transactional
    public void enroll(Student student, Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));

        if (enrollmentRepository.existsByStudentAndCourse(student, course)) {
            throw new EnrollmentException("이미 신청한 강의입니다.");
        }
        if (course.isFull()) {
            throw new EnrollmentException("정원이 초과되어 신청할 수 없습니다.");
        }

        List<Enrollment> current = enrollmentRepository.findByStudent(student);
        for (Enrollment e : current) {
            if (e.getCourse().conflictsWith(course)) {
                throw new EnrollmentException(
                        "시간표가 겹칩니다: '" + e.getCourse().getName() + "' 과(와) 충돌합니다.");
            }
        }

        course.increaseEnrolled();
        enrollmentRepository.save(Enrollment.builder()
                .student(student)
                .course(course)
                .build());
    }

    /** 신청 확정: 확정되면 취소 대신 수정(확정 해제)만 가능해진다 */
    @Transactional
    public void confirm(Student student, Long courseId) {
        findEnrollment(student, courseId).confirm();
    }

    /** 확정 해제: 다시 취소 가능한 상태로 되돌린다 */
    @Transactional
    public void unconfirm(Student student, Long courseId) {
        findEnrollment(student, courseId).unconfirm();
    }

    private Enrollment findEnrollment(Student student, Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));
        return enrollmentRepository.findByStudentAndCourse(student, course)
                .orElseThrow(() -> new EnrollmentException("신청하지 않은 강의입니다."));
    }

    /** 요일 x 교시 시간표 그리드 (rowspan 적용을 위해 covered 셀은 render=false로 표시) */
    @Transactional(readOnly = true)
    public List<List<TimetableCell>> weeklyGrid(Student student) {
        List<Course> courses = findByStudent(student).stream()
                .map(Enrollment::getCourse)
                .toList();
        return gridOf(courses);
    }

    /** 임의의 과목 목록으로 요일 x 교시 시간표 그리드 생성 (추천 시간표 미리보기 등에 재사용) */
    public List<List<TimetableCell>> gridOf(List<Course> courses) {
        Course[][] startingCourse = new Course[TIMETABLE_MAX_PERIOD + 1][TIMETABLE_DAYS.size()];
        boolean[][] covered = new boolean[TIMETABLE_MAX_PERIOD + 1][TIMETABLE_DAYS.size()];

        for (Course course : courses) {
            int dayIdx = TIMETABLE_DAYS.indexOf(course.getDayOfWeek());
            if (dayIdx < 0) {
                continue;
            }
            startingCourse[course.getStartPeriod()][dayIdx] = course;
            for (int p = course.getStartPeriod(); p <= course.getEndPeriod() && p <= TIMETABLE_MAX_PERIOD; p++) {
                covered[p][dayIdx] = true;
            }
        }

        List<List<TimetableCell>> grid = new ArrayList<>();
        for (int period = 1; period <= TIMETABLE_MAX_PERIOD; period++) {
            List<TimetableCell> row = new ArrayList<>();
            for (int dayIdx = 0; dayIdx < TIMETABLE_DAYS.size(); dayIdx++) {
                Course starting = startingCourse[period][dayIdx];
                if (starting != null) {
                    row.add(TimetableCell.builder()
                            .label(starting.getName())
                            .rowSpan(starting.getEndPeriod() - starting.getStartPeriod() + 1)
                            .render(true)
                            .build());
                } else if (covered[period][dayIdx]) {
                    row.add(TimetableCell.builder().render(false).build());
                } else {
                    row.add(TimetableCell.builder().rowSpan(1).render(true).build());
                }
            }
            grid.add(row);
        }
        return grid;
    }

    /** 수강신청 취소 */
    @Transactional
    public void cancel(Student student, Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));

        Enrollment enrollment = enrollmentRepository.findByStudentAndCourse(student, course)
                .orElseThrow(() -> new EnrollmentException("신청하지 않은 강의입니다."));

        course.decreaseEnrolled();
        enrollmentRepository.delete(enrollment);
    }

    /**
     * 확정된 신청 전체를 이수 완료 처리(CompletedCourse로 전환)하고 해당 신청은 삭제한다.
     * 이미 같은 과목의 CompletedCourse가 있으면 새로 만들지 않고 건너뛰되(중복 방지), 신청 내역에서는 제거한다.
     * @return 이수 완료 처리된(신청 내역에서 제거된) 확정 과목 수
     */
    @Transactional
    public int completeConfirmed(Student student, int completedYear, int completedSemester) {
        List<Enrollment> confirmed = enrollmentRepository.findByStudent(student).stream()
                .filter(Enrollment::isConfirmed)
                .toList();

        for (Enrollment enrollment : confirmed) {
            Course course = enrollment.getCourse();
            if (!completedCourseRepository.existsByStudentAndCourse(student, course)) {
                completedCourseRepository.save(CompletedCourse.builder()
                        .student(student)
                        .course(course)
                        .completedYear(completedYear)
                        .completedSemester(completedSemester)
                        .build());
            }
            course.decreaseEnrolled();
            enrollmentRepository.delete(enrollment);
        }
        return confirmed.size();
    }

    /** 이수 완료 처리를 되돌린다: CompletedCourse를 지우고 다시 신청내역(미확정)으로 되돌린다 */
    @Transactional
    public void uncomplete(Student student, Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));
        CompletedCourse completedCourse = completedCourseRepository.findByStudentAndCourse(student, course)
                .orElseThrow(() -> new EnrollmentException("이수 완료된 과목이 아닙니다."));

        completedCourseRepository.delete(completedCourse);
        if (!enrollmentRepository.existsByStudentAndCourse(student, course)) {
            course.increaseEnrolled();
            enrollmentRepository.save(Enrollment.builder()
                    .student(student)
                    .course(course)
                    .build());
        }
    }
}
