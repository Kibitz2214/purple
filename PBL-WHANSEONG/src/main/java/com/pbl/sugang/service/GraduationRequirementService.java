package com.pbl.sugang.service;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.GraduationRequirement;
import com.pbl.sugang.domain.RequiredCourse;
import com.pbl.sugang.repository.CourseRepository;
import com.pbl.sugang.repository.DepartmentRepository;
import com.pbl.sugang.repository.GraduationRequirementRepository;
import com.pbl.sugang.repository.RequiredCourseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;

/**
 * 교수·조교가 등록하는 졸업요건 관리.
 * 여기서 저장한 값을 학생 화면의 {@link GraduationAnalysisService}가 그대로 읽어 분석에 사용한다.
 */
@Service
@RequiredArgsConstructor
public class GraduationRequirementService {

    private final GraduationRequirementRepository requirementRepository;
    private final RequiredCourseRepository requiredCourseRepository;
    private final CourseRepository courseRepository;
    private final DepartmentRepository departmentRepository;

    /**
     * 졸업요건을 등록할 수 있는 학과 목록.
     * 등록된 학과에, 이미 강의나 졸업요건이 붙어 있는 학과명을 합쳐서 돌려준다.
     * (학과 목록에 없는 이름으로 예전에 등록해 둔 요건이 화면에서 사라지지 않게 하기 위함)
     */
    @Transactional(readOnly = true)
    public List<String> findSelectableDepartments() {
        Set<String> names = new TreeSet<>();
        departmentRepository.findAll().forEach(d -> names.add(d.getName()));
        courseRepository.findAll().forEach(c -> names.add(c.getDepartment()));
        requirementRepository.findAll().forEach(r -> names.add(r.getDepartment()));
        return new ArrayList<>(names);
    }

    /** 학과의 졸업요건 목록 (입학년도 최신순 → 이수구분 순) */
    @Transactional(readOnly = true)
    public List<GraduationRequirement> findRequirements(String department) {
        return requirementRepository.findByDepartment(department).stream()
                .sorted(Comparator.comparingInt(GraduationRequirement::getAdmissionYear).reversed()
                        .thenComparing(r -> r.getCategory().ordinal()))
                .toList();
    }

    /**
     * 졸업요건 등록/수정.
     * (학과, 입학년도, 이수구분)은 유니크 제약이 걸려 있으므로 이미 있으면 학점만 갱신한다.
     */
    @Transactional
    public void saveRequirement(String department, int admissionYear, Category category, int requiredCredits) {
        if (department == null || department.isBlank()) {
            throw new EnrollmentException("학과를 입력하세요.");
        }
        if (category == null) {
            throw new EnrollmentException("이수구분을 선택하세요.");
        }
        if (requiredCredits < 0) {
            throw new EnrollmentException("필요 학점은 0 이상이어야 합니다.");
        }

        String dept = department.trim();
        requirementRepository.findByDepartment(dept).stream()
                .filter(r -> r.getAdmissionYear() == admissionYear && r.getCategory() == category)
                .findFirst()
                .ifPresentOrElse(
                        existing -> existing.updateRequiredCredits(requiredCredits),
                        () -> requirementRepository.save(GraduationRequirement.builder()
                                .department(dept)
                                .admissionYear(admissionYear)
                                .category(category)
                                .requiredCredits(requiredCredits)
                                .build()));
    }

    @Transactional
    public void deleteRequirement(Long id) {
        requirementRepository.findById(id)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 졸업요건입니다."));
        requirementRepository.deleteById(id);
    }

    /** 학과의 필수 지정 과목 목록 */
    @Transactional(readOnly = true)
    public List<RequiredCourse> findRequiredCourses(String department) {
        return requiredCourseRepository.findByDepartment(department);
    }

    /** 필수 지정 과목 추가 (같은 학과에 이미 지정된 과목이면 중복 등록하지 않는다) */
    @Transactional
    public void addRequiredCourse(String department, Long courseId) {
        String dept = department == null ? "" : department.trim();
        if (dept.isBlank()) {
            throw new EnrollmentException("학과를 입력하세요.");
        }
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));

        boolean already = requiredCourseRepository.findByDepartment(dept).stream()
                .anyMatch(rc -> rc.getCourse().getId().equals(courseId));
        if (already) {
            throw new EnrollmentException("이미 필수 과목으로 지정된 강의입니다: " + course.getName());
        }

        requiredCourseRepository.save(RequiredCourse.builder()
                .department(dept)
                .course(course)
                .build());
    }

    @Transactional
    public void deleteRequiredCourse(Long id) {
        requiredCourseRepository.findById(id)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 필수 과목 지정입니다."));
        requiredCourseRepository.deleteById(id);
    }
}
