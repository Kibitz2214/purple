package com.pbl.sugang.controller;

import com.pbl.sugang.domain.Staff;
import com.pbl.sugang.service.StaffService;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

/** 세션에서 로그인된 교직원을 조회하는 헬퍼 */
@Component
@RequiredArgsConstructor
public class CurrentStaffResolver {

    private final StaffService staffService;

    /** 로그인 상태가 아니면 null 반환 */
    public Staff resolve(HttpSession session) {
        Object loginId = session.getAttribute(SessionConst.LOGIN_STAFF_ID);
        if (loginId == null) {
            return null;
        }
        try {
            return staffService.login((String) loginId);
        } catch (RuntimeException e) {
            session.invalidate();
            return null;
        }
    }
}
