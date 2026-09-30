package com.pbl.sugang.controller;

import com.pbl.sugang.domain.ClassPeriod;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.CourseService;
import com.pbl.sugang.service.EnrollmentException;
import com.pbl.sugang.service.EnrollmentService;
import com.pbl.sugang.service.GraduationAnalysisService;
import com.pbl.sugang.service.RecommendationPreference;
import com.pbl.sugang.service.RecommendedCourse;
import com.pbl.sugang.service.TimeSlot;
import com.pbl.sugang.service.TimetableRecommendationService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.util.ArrayList;
import java.util.List;

@Controller
@RequiredArgsConstructor
public class RecommendationController {

    private final TimetableRecommendationService recommendationService;
    private final EnrollmentService enrollmentService;
    private final GraduationAnalysisService graduationAnalysisService;
    private final CourseService courseService;
    private final CurrentStudentResolver currentStudentResolver;

    /** 조건 입력 화면 — 편성 버튼을 누르기 전에는 추천 결과를 만들지 않는다 */
    @GetMapping("/recommend")
    public String form(HttpSession session, Model model) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }

        // 처음 열 때는 본인 학과가 골라져 있게 한다 (대부분 자기 학과 전공을 채우려 들어오므로)
        addFormAttributes(model, student, RecommendationPreference.defaults(student.getDepartment()));
        model.addAttribute("generated", false);
        return "recommend";
    }

    /** 입력한 조건으로 추천 시간표 편성. variation을 올리면 같은 조건에서 다른 조합을 만든다. */
    @PostMapping("/recommend")
    public String generate(@RequestParam(required = false) Integer targetCredits,
                           @RequestParam(required = false) TimeSlot timeSlot,
                           @RequestParam(required = false) String department,
                           @RequestParam(required = false) List<String> excludedDays,
                           @RequestParam(required = false, defaultValue = "0") Integer variation,
                           @RequestParam(required = false) List<Long> previousIds,
                           HttpSession session,
                           Model model) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }

        RecommendationPreference pref =
                RecommendationPreference.of(targetCredits, timeSlot, department, excludedDays, variation);
        // "다시 만들기"로 들어오면 직전 결과가 함께 넘어온다. 그때는 같은 조합이 다시 나오지 않게 한다.
        List<RecommendedCourse> recommended =
                recommendationService.recommendDifferentFrom(student, pref, previousIds);

        addFormAttributes(model, student, pref);
        model.addAttribute("generated", true);
        model.addAttribute("recommended", recommended);
        // 어떤 이수구분이 부족해서 이렇게 짰는지 화면에서 보여 주기 위한 근거
        model.addAttribute("analysis", graduationAnalysisService.analyze(student));
        model.addAttribute("totalCredits",
                recommended.stream().mapToInt(r -> r.getCourse().getCredit()).sum());
        if (pref.excludesEveryDay()) {
            model.addAttribute("error", "모든 요일을 공강으로 지정하면 추천할 수 있는 과목이 없습니다.");
        }
        return "recommend";
    }

    /** 추천 시간표에서 학생이 선택한 과목만 실제로 수강신청 */
    @PostMapping("/recommend/apply")
    public String apply(@RequestParam(required = false) List<Long> courseIds,
                        HttpSession session,
                        RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        if (courseIds == null || courseIds.isEmpty()) {
            ra.addFlashAttribute("error", "신청할 과목을 하나 이상 선택하세요.");
            return "redirect:/recommend";
        }

        int success = 0;
        List<String> failures = new ArrayList<>();
        for (Long courseId : courseIds) {
            try {
                enrollmentService.enroll(student, courseId);
                success++;
            } catch (EnrollmentException e) {
                failures.add(e.getMessage());
            }
        }

        if (success > 0) {
            ra.addFlashAttribute("message", success + "개 과목 수강신청이 완료되었습니다.");
        }
        if (!failures.isEmpty()) {
            ra.addFlashAttribute("error", String.join(" / ", failures));
        }
        return "redirect:/my";
    }

    /** 조건 폼을 다시 그리는 데 필요한 값 (편성 후에도 입력값이 남아 있어야 한다) */
    private void addFormAttributes(Model model, Student student, RecommendationPreference pref) {
        model.addAttribute("student", student);
        model.addAttribute("pref", pref);
        model.addAttribute("timeSlots", TimeSlot.values());
        model.addAttribute("departments", courseService.findDepartmentsWithCourses());
        model.addAttribute("allDays", EnrollmentService.TIMETABLE_DAYS);
        model.addAttribute("timetableDays", EnrollmentService.TIMETABLE_DAYS);
        model.addAttribute("periods", ClassPeriod.all());
        model.addAttribute("minCredits", RecommendationPreference.MIN_CREDITS);
        model.addAttribute("maxCredits", RecommendationPreference.MAX_CREDITS);
    }
}
