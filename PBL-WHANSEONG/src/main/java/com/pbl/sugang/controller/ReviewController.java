package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.EnrollmentException;
import com.pbl.sugang.service.ReviewService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequiredArgsConstructor
public class ReviewController {

    private final ReviewService reviewService;
    private final CurrentStudentResolver currentStudentResolver;

    /**
     * 강의평가 작성/수정.
     * 내 신청내역에서 별점만 눌러 등록하는 경우가 있어 comment는 선택이며,
     * redirect=my로 들어오면 강의 상세가 아니라 신청내역으로 되돌린다.
     */
    @PostMapping("/reviews")
    public String write(@RequestParam Long courseId,
                        @RequestParam int rating,
                        @RequestParam(required = false) String comment,
                        @RequestParam(required = false) String redirect,
                        HttpSession session,
                        RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            reviewService.writeOrUpdate(student, courseId, rating, comment);
            ra.addFlashAttribute("message", "별점 " + rating + "점을 등록했습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:" + targetOf(redirect, courseId);
    }

    /** 강의평가 삭제 */
    @PostMapping("/reviews/delete")
    public String delete(@RequestParam Long courseId,
                         @RequestParam(required = false) String redirect,
                         HttpSession session,
                         RedirectAttributes ra) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }
        try {
            reviewService.delete(student, courseId);
            ra.addFlashAttribute("message", "별점을 취소했습니다.");
        } catch (EnrollmentException e) {
            ra.addFlashAttribute("error", e.getMessage());
        }
        return "redirect:" + targetOf(redirect, courseId);
    }

    /** 돌아갈 화면 결정 — 지정이 없으면 기존처럼 강의 상세로 보낸다 */
    private String targetOf(String redirect, Long courseId) {
        return "my".equals(redirect) ? "/my" : "/courses/" + courseId;
    }
}
