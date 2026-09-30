package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 교직원 (교수 / 조교) — 졸업요건을 등록하는 관리자 계정.
 * 교수는 name이 Course.professor와 같은 값이며, 이 이름으로 담당 강의를 찾는다.
 */
@Entity
@Table(name = "staff",
        uniqueConstraints = @UniqueConstraint(name = "uk_staff_login_id", columnNames = "login_id"))
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Staff {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 로그인 ID */
    @Column(name = "login_id", nullable = false, length = 30)
    private String loginId;

    /** 이름 — 교수의 경우 Course.professor와 일치해야 담당 강의가 연결된다 */
    @Column(nullable = false, length = 30)
    private String name;

    /** 소속 학과 */
    @Column(nullable = false, length = 50)
    private String department;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private StaffRole role;

    @Builder
    public Staff(String loginId, String name, String department, StaffRole role) {
        this.loginId = loginId;
        this.name = name;
        this.department = department;
        this.role = role;
    }

    public boolean isProfessor() {
        return role == StaffRole.PROFESSOR;
    }
}
