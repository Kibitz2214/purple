package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.Enrollment;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.CourseService;
import com.pbl.sugang.service.EnrollmentService;
import com.pbl.sugang.service.GraduationAnalysisResult;
import com.pbl.sugang.service.GraduationAnalysisService;
import com.pbl.sugang.service.ReviewService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;
import java.util.stream.IntStream;

@Controller
@RequiredArgsConstructor
public class CourseController {

    private final CourseService courseService;
    private final EnrollmentService enrollmentService;
    private final ReviewService reviewService;
    private final GraduationAnalysisService graduationAnalysisService;
    private final CurrentStudentResolver currentStudentResolver;
    private final CurrentStaffResolver currentStaffResolver;

    /** 교수·조교로 로그인한 상태면 학생용 수강신청이 아니라 교수 전용 화면으로 보낸다 */
    @GetMapping("/")
    public String home(HttpSession session) {
        if (currentStaffResolver.resolve(session) != null) {
            return "redirect:/professor";
        }
        return "redirect:/courses";
    }

    /** 한 페이지에 보여 줄 강의 수 */
    private static final int PAGE_SIZE = 10;

    /** 페이지 버튼을 한 번에 최대 몇 개까지 노출할지 */
    private static final int PAGE_WINDOW = 5;

    /** 강의 목록 + 검색/필터 (10개씩 페이징) */
    @GetMapping("/courses")
    public String courses(@RequestParam(required = false) String keyword,
                          @RequestParam(required = false) String department,
                          @RequestParam(required = false) Category category,
                          @RequestParam(required = false, defaultValue = "false") boolean sortByRating,
                          @RequestParam(required = false, defaultValue = "1") int page,
                          HttpSession session,
                          Model model) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }

        // 화면에서는 1페이지부터 세고, 서비스에는 0부터 시작하는 번호를 넘긴다.
        Page<Course> coursePage =
                courseService.search(keyword, department, category, sortByRating, page - 1, PAGE_SIZE);
        List<Course> courses = coursePage.getContent();

        Set<Long> enrolledCourseIds = enrollmentService.findByStudent(student).stream()
                .map(e -> e.getCourse().getId())
                .collect(Collectors.toSet());
        Set<Long> completedCourseIds = graduationAnalysisService.analyze(student).getCompletedCourses().stream()
                .map(c -> c.getCourse().getId())
                .collect(Collectors.toSet());

        model.addAttribute("student", student);
        model.addAttribute("courses", courses);
        model.addAttribute("currentPage", coursePage.getNumber() + 1);
        model.addAttribute("totalPages", coursePage.getTotalPages());
        model.addAttribute("totalCourses", coursePage.getTotalElements());
        model.addAttribute("pageNumbers", pageNumbers(coursePage.getNumber() + 1, coursePage.getTotalPages()));
        model.addAttribute("firstItemNo", coursePage.getTotalElements() == 0 ? 0 : coursePage.getNumber() * PAGE_SIZE + 1);
        model.addAttribute("lastItemNo", coursePage.getNumber() * PAGE_SIZE + courses.size());
        model.addAttribute("enrolledCourseIds", enrolledCourseIds);
        model.addAttribute("completedCourseIds", completedCourseIds);
        model.addAttribute("categories", Category.values());
        model.addAttribute("departments", courseService.findDepartmentsWithCourses());
        model.addAttribute("keyword", keyword);
        model.addAttribute("selectedDepartment", department);
        model.addAttribute("selectedCategory", category);
        model.addAttribute("sortByRating", sortByRating);
        model.addAttribute("totalCredits", enrollmentService.totalCredits(student));
        return "courses";
    }

    /**
     * 현재 페이지 주변으로 보여 줄 페이지 번호 목록.
     * 강의가 많아져 페이지가 늘어나도 버튼이 끝없이 늘어나지 않도록 최대 PAGE_WINDOW개로 제한한다.
     */
    private List<Integer> pageNumbers(int currentPage, int totalPages) {
        if (totalPages <= 0) {
            return List.of();
        }
        int start = Math.max(1, currentPage - PAGE_WINDOW / 2);
        int end = Math.min(totalPages, start + PAGE_WINDOW - 1);
        // 마지막 구간에서는 창이 잘리지 않도록 시작점을 당겨 준다.
        start = Math.max(1, end - PAGE_WINDOW + 1);

        return IntStream.rangeClosed(start, end).boxed().toList();
    }

    /** 강의 상세 + 강의평가 목록/작성 */
    @GetMapping("/courses/{id}")
    public String courseDetail(@PathVariable Long id, HttpSession session, Model model) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }

        Course course = courseService.findById(id);
        boolean enrolled = enrollmentService.findByStudent(student).stream()
                .anyMatch(e -> e.getCourse().getId().equals(course.getId()));

        model.addAttribute("student", student);
        model.addAttribute("course", course);
        model.addAttribute("enrolled", enrolled);
        model.addAttribute("reviews", reviewService.reviewsOf(course));
        model.addAttribute("reviewCount", reviewService.countOf(course));
        model.addAttribute("myReview", reviewService.myReview(student, course).orElse(null));
        return "course-detail";
    }

    /** 내 수강신청 내역 (시간표) */
    @GetMapping("/my")
    public String myEnrollments(HttpSession session, Model model) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }

        List<Enrollment> enrollments = enrollmentService.findByStudent(student);
        boolean hasConfirmed = enrollments.stream().anyMatch(Enrollment::isConfirmed);
        GraduationAnalysisResult analysis = graduationAnalysisService.analyze(student);

        model.addAttribute("student", student);
        model.addAttribute("enrollments", enrollments);
        model.addAttribute("hasConfirmed", hasConfirmed);
        model.addAttribute("totalCredits", enrollmentService.totalCredits(student));
        model.addAttribute("analysis", analysis);
        // 확정한 강의에 별점을 매길 수 있도록, 이미 준 평점을 강의 id별로 넘긴다
        model.addAttribute("myRatings", reviewService.myRatingsByCourseId(student));
        return "my";
    }
}
