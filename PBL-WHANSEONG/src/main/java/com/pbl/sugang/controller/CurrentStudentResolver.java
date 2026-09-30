package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.StudentService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/** 세션에서 로그인된 학생을 조회하는 헬퍼 */
@Component
@RequiredArgsConstructor
public class CurrentStudentResolver {

    private final StudentService studentService;

    /** 로그인 상태가 아니면 null 반환 */
    public Student resolve(HttpSession session) {
        Object studentNo = session.getAttribute(SessionConst.LOGIN_STUDENT_NO);
        if (studentNo == null) {
            return null;
        }
        try {
            return studentService.login((String) studentNo);
        } catch (RuntimeException e) {
            session.invalidate();
            return null;
        }
    }
}
