package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.ClassPeriod;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.CourseReview;
import com.pbl.sugang.domain.Staff;
import com.pbl.sugang.repository.CourseRepository;
import com.pbl.sugang.repository.CourseReviewRepository;
import com.pbl.sugang.service.EnrollmentException;
import com.pbl.sugang.service.EnrollmentService;
import com.pbl.sugang.service.GraduationRequirementService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * 교수·조교 전용 화면.
 * 학생용 수강신청 페이지와 완전히 분리되어 있으며, 로그인하면 여기(/professor)로 들어온다.
 */
@Controller
@RequiredArgsConstructor
public class ProfessorController {

    private final CurrentStaffResolver currentStaffResolver;
    private final GraduationRequirementService requirementService;
    private final CourseRepository courseRepository;
    private final CourseReviewRepository reviewRepository;
    private final EnrollmentService enrollmentService;

    /** 담당 강의 + 평점 요약 대시보드 */
    @GetMapping("/professor")
    public String dashboard(HttpSession session, Model model) {
        Staff staff = currentStaffResolver.resolve(session);
        if (staff == null) {
            return "redirect:/login";
        }

        List<Course> myCourses = myCourses(staff);
        model.addAttribute("staff", staff);
        model.addAttribute("myCourses", myCourses);
        model.addAttribute("totalStudents", myCourses.stream().mapToInt(Course::getEnrolledCount).sum());
        model.addAttribute("avgRating", averageRating(myCourses));
        model.addAttribute("reviewCount", myCourses.isEmpty() ? 0
                : reviewRepository.findByCoursesWithStudent(myCourses).size());
        model.addAttribute("requirementCount", requirementService.findRequirements(staff.getDepartment()).size());
        return "professor/dashboard";
    }

    /** 담당 강의 목록 */
    @GetMapping("/professor/courses")
    public String courses(HttpSession session, Model model) {
        Staff staff = currentStaffResolver.resolve(session);
        if (staff == null) {
            return "redirect:/login";
        }

        model.addAttribute("staff", staff);
        model.addAttribute("myCourses", myCourses(staff));
        return "professor/courses";
    }

    /** 담당 강의의 강의평가(평점·후기) 모아보기 */
    @GetMapping("/professor/reviews")
    public String reviews(HttpSession session, Model model) {
        Staff staff = currentStaffResolver.resolve(session);
        if (staff == null) {
            return "redirect:/login";
        }

        List<Course> myCourses = myCourses(staff);
        List<CourseReview> reviews = myCourses.isEmpty()
                ? List.of()
                : reviewRepository.findByCoursesWithStudent(myCourses);

        model.addAttribute("staff", staff);
        model.addAttribute("myCourses", myCourses);
        model.addAttribute("reviews", reviews);
        model.addAttribute("avgRating", averageRating(myCourses));
        return "professor/reviews";
    }

    /** 담당 강의 주간 시간표 */
    @GetMapping("/professor/timetable")
    public String timetable(HttpSession session, Model model) {
        Staff staff = currentStaffResolver.resolve(session);
        if (staff == null) {
            return "redirect:/login";
        }

        List<Course> myCourses = myCourses(staff);
        model.addAttribute("staff", staff);
        model.addAttribute("myCourses", myCourses);
        model.addAttribute("timetableDays", EnrollmentService.TIMETABLE_DAYS);
        model.addAttribute("periods", ClassPeriod.all());
        model.addAttribute("timetableGrid", enrollmentService.gridOf(myCourses));
        return "professor/timetable";
    }

    /** 졸업요건 등록 화면 — 여기서 저장한 값을 학생 졸업요건 분석이 그대로 사용한다 */
    @GetMapping("/professor/requirements")
    public String requirements(@RequestParam(required = false) String department,
                               HttpSession session, Model model) {
        Staff staff = currentStaffResolver.resolve(session);
        if (staff == null) {
            return "redirect:/login";
        }

        String target = (department == null || department.isBlank()) ? staff.getDepartment() : department.trim();

        // 선택지에 없는 학과를 보고 있더라도 드롭다운에서 현재 값이 사라지지 않게 합친다
        List<String> departments = new ArrayList<>(requirementService.findSelectableDepartments());
        if (!departments.contains(target)) {
            departments.add(target);
            departments.sort(Comparator.naturalOrder());
        }

        model.addAttribute("staff", staff);
        model.addAttribute("department", target);
        model.addAttribute("departments", departments);
        model.addAttribute("requirements", requirementService.findRequirements(target));
        model.addAttribute("requiredCourses", requirementService.findRequiredCourses(target));
        model.addAttribute("categories", Category.values());
        model.addAttribute("allCourses", courseRepository.findAll().stream()
                .sorted(Comparator.comparing(Course::getCourseCode))
                .toList());
        return "professor/requirements";
    }

    @PostMapping("/professor/requirements")
    public String saveRequirement(@RequestParam String department,
                                  @RequestParam int admissionYear,
                                  @RequestParam Category category,
                                  @RequestParam int requiredCredits,
                                  HttpSession session,
                                  RedirectAttributes ra) {
        if (currentStaffResolver.resolve(session) == null) {
            return "redirect:/login";
        }
        try {
            requirementService.saveRequirement(department, admissionYear, category, requiredCredits);
            ra.addFlashAttribute("message", "졸업요건을 저장했습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return redirectToRequirements(department);
    }

    @PostMapping("/professor/requirements/delete")
    public String deleteRequirement(@RequestParam Long id,
                                    @RequestParam String department,
                                    HttpSession session,
                                    RedirectAttributes ra) {
        if (currentStaffResolver.resolve(session) == null) {
            return "redirect:/login";
        }
        try {
            requirementService.deleteRequirement(id);
            ra.addFlashAttribute("message", "졸업요건을 삭제했습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return redirectToRequirements(department);
    }

    @PostMapping("/professor/requirements/courses")
    public String addRequiredCourse(@RequestParam String department,
                                    @RequestParam Long courseId,
                                    HttpSession session,
                                    RedirectAttributes ra) {
        if (currentStaffResolver.resolve(session) == null) {
            return "redirect:/login";
        }
        try {
            requirementService.addRequiredCourse(department, courseId);
            ra.addFlashAttribute("message", "필수 지정 과목을 추가했습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return redirectToRequirements(department);
    }

    @PostMapping("/professor/requirements/courses/delete")
    public String deleteRequiredCourse(@RequestParam Long id,
                                       @RequestParam String department,
                                       HttpSession session,
                                       RedirectAttributes ra) {
        if (currentStaffResolver.resolve(session) == null) {
            return "redirect:/login";
        }
        try {
            requirementService.deleteRequiredCourse(id);
            ra.addFlashAttribute("message", "필수 지정 과목을 해제했습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return redirectToRequirements(department);
    }

    /**
     * 교수는 본인 이름으로 개설된 강의를, 조교는 소속 학과 전체 강의를 담당 범위로 본다.
     * (Course에는 교수 이름만 문자열로 들어 있어 이름으로 매칭한다)
     */
    private List<Course> myCourses(Staff staff) {
        return staff.isProfessor()
                ? courseRepository.findByProfessorOrderByDayOfWeekAscStartPeriodAsc(staff.getName())
                : courseRepository.findByDepartmentOrderByDayOfWeekAscStartPeriodAsc(staff.getDepartment());
    }

    /** 담당 강의 평점의 단순 평균 (평가가 없는 강의는 avgRating이 0이므로 제외) */
    private double averageRating(List<Course> courses) {
        return courses.stream()
                .filter(c -> c.getAvgRating() > 0)
                .mapToDouble(Course::getAvgRating)
                .average()
                .orElse(0.0);
    }

    private String redirectToRequirements(String department) {
        String dept = department == null ? "" : department.trim();
        return "redirect:/professor/requirements?department="
                + java.net.URLEncoder.encode(dept, java.nio.charset.StandardCharsets.UTF_8);
    }
}
