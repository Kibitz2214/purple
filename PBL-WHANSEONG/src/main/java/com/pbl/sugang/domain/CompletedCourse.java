package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 학생의 수강 이력 (과거에 이수 완료한 과목) */
@Entity
@Table(name = "completed_course",
        uniqueConstraints = @UniqueConstraint(name = "uk_student_completed_course",
                columnNames = {"student_id", "course_id"}))
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class CompletedCourse {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "student_id")
    private Student student;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "course_id")
    private Course course;

    /** 이수년도 */
    @Column(name = "completed_year", nullable = false)
    private int completedYear;

    /** 이수학기 (1 또는 2) */
    @Column(name = "completed_semester", nullable = false)
    private int completedSemester;

    @Builder
    public CompletedCourse(Student student, Course course, int completedYear, int completedSemester) {
        this.student = student;
        this.course = course;
        this.completedYear = completedYear;
        this.completedSemester = completedSemester;
    }
}
