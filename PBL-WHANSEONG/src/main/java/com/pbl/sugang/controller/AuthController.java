package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Staff;
import com.pbl.sugang.domain.StaffRole;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.service.DepartmentService;
import com.pbl.sugang.service.EnrollmentException;
import com.pbl.sugang.service.StaffService;
import com.pbl.sugang.service.StudentService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
@RequiredArgsConstructor
public class AuthController {

    private final StudentService studentService;
    private final StaffService staffService;
    private final DepartmentService departmentService;

    @GetMapping("/login")
    public String loginForm(Model model) {
        model.addAttribute("staffRoles", StaffRole.values());
        return "login";
    }

    /** 학생 로그인 — 학번만 입력받는다 */
    @PostMapping("/login")
    public String login(@RequestParam String studentNo, HttpSession session, Model model) {
        try {
            Student student = studentService.login(studentNo.trim());
            session.setAttribute(SessionConst.LOGIN_STUDENT_NO, student.getStudentNo());
            session.removeAttribute(SessionConst.LOGIN_STAFF_ID);
            return "redirect:/courses";
        } catch (EnrollmentException e) {
            model.addAttribute("error", e.getMessage());
            model.addAttribute("staffRoles", StaffRole.values());
            return "login";
        }
    }

    /** 교수·조교 로그인 — 학생 세션과 별도 키를 쓰고, 교수 전용 화면으로 보낸다 */
    @PostMapping("/login/professor")
    public String professorLogin(@RequestParam String loginId, HttpSession session, Model model) {
        try {
            Staff staff = staffService.login(loginId.trim());
            session.setAttribute(SessionConst.LOGIN_STAFF_ID, staff.getLoginId());
            session.removeAttribute(SessionConst.LOGIN_STUDENT_NO);
            return "redirect:/professor";
        } catch (EnrollmentException e) {
            model.addAttribute("staffError", e.getMessage());
            model.addAttribute("staffRoles", StaffRole.values());
            return "login";
        }
    }

    @GetMapping("/register")
    public String registerForm(Model model) {
        model.addAttribute("departments", departmentService.findDegreePrograms());
        return "register";
    }

    @PostMapping("/register")
    public String register(@RequestParam String studentNo,
                           @RequestParam String name,
                           @RequestParam String department,
                           @RequestParam int grade,
                           @RequestParam int admissionYear,
                           HttpSession session,
                           Model model) {
        try {
            Student student = studentService.register(
                    studentNo.trim(), name.trim(), department.trim(), grade, admissionYear);
            session.setAttribute(SessionConst.LOGIN_STUDENT_NO, student.getStudentNo());
            session.removeAttribute(SessionConst.LOGIN_STAFF_ID);
            return "redirect:/courses";
        } catch (EnrollmentException e) {
            model.addAttribute("error", e.getMessage());
            model.addAttribute("departments", departmentService.findDegreePrograms());
            return "register";
        }
    }

    @GetMapping("/register/professor")
    public String professorRegisterForm(Model model) {
        model.addAttribute("staffRoles", StaffRole.values());
        model.addAttribute("departments", departmentService.findAllNames());
        return "register-professor";
    }

    /**
     * 교수·조교 등록.
     * 교수의 이름은 강의의 교수명과 같아야 담당 강의가 연결되므로, 화면에서도 이 점을 안내한다.
     */
    @PostMapping("/register/professor")
    public String professorRegister(@RequestParam String loginId,
                                    @RequestParam String name,
                                    @RequestParam String department,
                                    @RequestParam(required = false) StaffRole role,
                                    HttpSession session,
                                    Model model) {
        try {
            Staff staff = staffService.register(
                    loginId.trim(), name.trim(), department.trim(), role);
            session.setAttribute(SessionConst.LOGIN_STAFF_ID, staff.getLoginId());
            session.removeAttribute(SessionConst.LOGIN_STUDENT_NO);
            return "redirect:/professor";
        } catch (EnrollmentException e) {
            model.addAttribute("error", e.getMessage());
            model.addAttribute("staffRoles", StaffRole.values());
            model.addAttribute("departments", departmentService.findAllNames());
            return "register-professor";
        }
    }

    @GetMapping("/logout")
    public String logout(HttpSession session) {
        session.invalidate();
        return "redirect:/login";
    }
}
