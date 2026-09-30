package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 학과 목록.
 * 강의나 학생이 아직 없는 학과에도 졸업요건을 먼저 등록할 수 있어야 하므로,
 * 강의·학생 데이터에서 학과명을 추려 쓰지 않고 별도로 관리한다.
 */
@Entity
@Table(name = "department",
        uniqueConstraints = @UniqueConstraint(name = "uk_department_name", columnNames = "name"))
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Department {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String name;

    @Builder
    public Department(String name) {
        this.name = name;
    }
}
