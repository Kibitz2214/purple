package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 학과별 필수 지정 과목 (졸업요건) */
@Entity
@Table(name = "required_course")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class RequiredCourse {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String department;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "course_id")
    private Course course;

    @Builder
    public RequiredCourse(String department, Course course) {
        this.department = department;
        this.course = course;
    }
}
