package com.pbl.sugang.controller;

import com.pbl.sugang.domain.ClassPeriod;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.EnrollmentService;
import com.pbl.sugang.service.GraduationAnalysisResult;
import com.pbl.sugang.service.GraduationAnalysisService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
@RequiredArgsConstructor
public class GraduationController {

    private final GraduationAnalysisService graduationAnalysisService;
    private final EnrollmentService enrollmentService;
    private final CurrentStudentResolver currentStudentResolver;

    /** 졸업요건 분석 (이수구분별 학점 현황 + 미이수 필수과목 + 현재 학기 시간표) */
    @GetMapping("/graduation")
    public String graduation(HttpSession session, Model model) {
        Student student = currentStudentResolver.resolve(session);
        if (student == null) {
            return "redirect:/login";
        }

        GraduationAnalysisResult result = graduationAnalysisService.analyze(student);

        model.addAttribute("student", student);
        model.addAttribute("result", result);
        model.addAttribute("timetableDays", EnrollmentService.TIMETABLE_DAYS);
        model.addAttribute("periods", ClassPeriod.all());
        model.addAttribute("timetableGrid", enrollmentService.weeklyGrid(student));
        return "graduation";
    }
}
