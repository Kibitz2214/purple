package com.pbl.sugang.service;

import com.pbl.sugang.domain.Student;
import com.pbl.sugang.repository.StudentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class StudentService {

    private final StudentRepository studentRepository;

    /** 학번으로 로그인 (없으면 예외) */
    @Transactional(readOnly = true)
    public Student login(String studentNo) {
        return studentRepository.findByStudentNo(studentNo)
                .orElseThrow(() -> new EnrollmentException("등록되지 않은 학번입니다: " + studentNo));
    }

    /** 회원가입 (학번 중복 검사) */
    @Transactional
    public Student register(String studentNo, String name, String department, int grade, int admissionYear) {
        if (studentRepository.existsByStudentNo(studentNo)) {
            throw new EnrollmentException("이미 등록된 학번입니다.");
        }
        return studentRepository.save(Student.builder()
                .studentNo(studentNo)
                .name(name)
                .department(department)
                .grade(grade)
                .admissionYear(admissionYear)
                .build());
    }
}
