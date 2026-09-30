package com.pbl.sugang.service;

import com.pbl.sugang.domain.Staff;
import com.pbl.sugang.domain.StaffRole;
import com.pbl.sugang.repository.StaffRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class StaffService {

    private final StaffRepository staffRepository;

    /** 교직원 ID로 로그인 (없으면 예외) */
    @Transactional(readOnly = true)
    public Staff login(String loginId) {
        return staffRepository.findByLoginId(loginId)
                .orElseThrow(() -> new EnrollmentException("등록되지 않은 교수/조교 ID입니다: " + loginId));
    }

    /** 교수·조교 등록 (ID 중복 검사) */
    @Transactional
    public Staff register(String loginId, String name, String department, StaffRole role) {
        if (staffRepository.existsByLoginId(loginId)) {
            throw new EnrollmentException("이미 등록된 ID입니다.");
        }
        return staffRepository.save(Staff.builder()
                .loginId(loginId)
                .name(name)
                .department(department)
                .role(role == null ? StaffRole.PROFESSOR : role)
                .build());
    }
}
