package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.EnrollmentException;
import com.pbl.sugang.service.EnrollmentService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequiredArgsConstructor
public class EnrollmentController {

    private final EnrollmentService enrollmentService;
    private final CurrentStudentResolver currentStudentResolver;

    @PostMapping("/enroll")
    public String enroll(@RequestParam Long courseId,
                         @RequestParam(required = false) String redirect,
                         HttpSession session,
                         RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            enrollmentService.enroll(student, courseId);
            ra.addFlashAttribute("message", "수강신청이 완료되었습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:" + targetOf(redirect);
    }

    @PostMapping("/cancel")
    public String cancel(@RequestParam Long courseId,
                         @RequestParam(required = false) String redirect,
                         HttpSession session,
                         RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            enrollmentService.cancel(student, courseId);
            ra.addFlashAttribute("message", "수강신청이 취소되었습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:" + targetOf(redirect);
    }

    @PostMapping("/confirm")
    public String confirm(@RequestParam Long courseId, HttpSession session, RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            enrollmentService.confirm(student, courseId);
            ra.addFlashAttribute("message", "신청이 확정되었습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/my";
    }

    @PostMapping("/unconfirm")
    public String unconfirm(@RequestParam Long courseId, HttpSession session, RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            enrollmentService.unconfirm(student, courseId);
            ra.addFlashAttribute("message", "확정이 해제되어 다시 수정할 수 있습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/my";
    }

    @PostMapping("/complete-confirmed")
    public String completeConfirmed(@RequestParam(defaultValue = "2026") int year,
                                    @RequestParam(defaultValue = "1") int semester,
                                    HttpSession session,
                                    RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        int count = enrollmentService.completeConfirmed(student, year, semester);
        if (count > 0) {
            ra.addFlashAttribute("message", count + "개 과목이 이수 완료 처리되었습니다.");
        } else {
            ra.addFlashAttribute("error", "확정된 신청이 없습니다.");
        }
        return "redirect:/my";
    }

    @PostMapping("/uncomplete")
    public String uncomplete(@RequestParam Long courseId, HttpSession session, RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            enrollmentService.uncomplete(student, courseId);
            ra.addFlashAttribute("message", "이수 완료 처리가 취소되어 다시 신청 내역으로 돌아갔습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:/my";
    }

    private String targetOf(String redirect) {
        return "my".equals(redirect) ? "/my" : "/courses";
    }
}
