package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 학생 (재학생) */
@Entity
@Table(name = "student",
        uniqueConstraints = @UniqueConstraint(name = "uk_student_no", columnNames = "student_no"))
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Student {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 학번 (로그인 ID) */
    @Column(name = "student_no", nullable = false, length = 20)
    private String studentNo;

    /** 이름 */
    @Column(nullable = false, length = 30)
    private String name;

    /** 학과 */
    @Column(nullable = false, length = 50)
    private String department;

    /** 학년 */
    @Column(nullable = false)
    private int grade;

    /** 입학년도 */
    @Column(name = "admission_year", nullable = false)
    private int admissionYear;

    @Builder
    public Student(String studentNo, String name, String department, int grade, int admissionYear) {
        this.studentNo = studentNo;
        this.name = name;
        this.department = department;
        this.grade = grade;
        this.admissionYear = admissionYear;
    }
}
