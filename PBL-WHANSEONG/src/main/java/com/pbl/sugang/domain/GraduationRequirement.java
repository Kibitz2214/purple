package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 학과별 졸업요건 (이수구분별 최소 이수학점) */
@Entity
@Table(name = "graduation_requirement",
        uniqueConstraints = @UniqueConstraint(name = "uk_department_admissionyear_category",
                columnNames = {"department", "admission_year", "category"}))
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class GraduationRequirement {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String department;

    @Column(name = "admission_year", nullable = false)
    private int admissionYear;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Category category;

    @Column(name = "required_credits", nullable = false)
    private int requiredCredits;

    @Builder
    public GraduationRequirement(String department, int admissionYear, Category category, int requiredCredits) {
        this.department = department;
        this.admissionYear = admissionYear;
        this.category = category;
        this.requiredCredits = requiredCredits;
    }

    /** 교수·조교가 필요 학점을 수정할 때 사용 */
    public void updateRequiredCredits(int requiredCredits) {
        this.requiredCredits = requiredCredits;
    }
}
