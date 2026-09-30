package com.pbl.sugang.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/** 개설 강의 */
@Entity
@Table(name = "course",
        uniqueConstraints = @UniqueConstraint(name = "uk_course_code", columnNames = "course_code"))
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Course {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** 과목코드 */
    @Column(name = "course_code", nullable = false, length = 20)
    private String courseCode;

    /** 과목명 */
    @Column(nullable = false, length = 100)
    private String name;

    /** 교수명 */
    @Column(nullable = false, length = 30)
    private String professor;

    /** 학점 */
    @Column(nullable = false)
    private int credit;

    /** 이수구분 */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Category category;

    /** 개설 학과 */
    @Column(nullable = false, length = 50)
    private String department;

    /** 정원 */
    @Column(nullable = false)
    private int capacity;

    /** 현재 신청 인원 */
    @Column(name = "enrolled_count", nullable = false)
    private int enrolledCount;

    /** 요일 (월~금) */
    @Column(name = "day_of_week", nullable = false, length = 5)
    private String dayOfWeek;

    /** 시작 교시 */
    @Column(name = "start_period", nullable = false)
    private int startPeriod;

    /** 종료 교시 */
    @Column(name = "end_period", nullable = false)
    private int endPeriod;

    /** 강의실 */
    @Column(length = 30)
    private String classroom;

    /** 강의평가 평균 평점 (0.0 ~ 5.0) */
    @Column(name = "avg_rating", nullable = false)
    private double avgRating;

    @Builder
    public Course(String courseCode, String name, String professor, int credit, Category category,
                  String department, int capacity, String dayOfWeek, int startPeriod, int endPeriod,
                  String classroom, double avgRating) {
        this.courseCode = courseCode;
        this.name = name;
        this.professor = professor;
        this.credit = credit;
        this.category = category;
        this.department = department;
        this.capacity = capacity;
        this.enrolledCount = 0;
        this.dayOfWeek = dayOfWeek;
        this.startPeriod = startPeriod;
        this.endPeriod = endPeriod;
        this.classroom = classroom;
        this.avgRating = avgRating;
    }

    /** 강의평가 평균 평점 갱신 (소수점 첫째 자리 반올림) */
    public void updateAvgRating(double avg) {
        this.avgRating = Math.round(avg * 10.0) / 10.0;
    }

    /** 강의평가가 모두 삭제되어 표시할 평점이 없어진 상태로 되돌린다 */
    public void clearRating() {
        this.avgRating = 0;
    }

    /**
     * 표시할 평점이 있는지 여부.
     * 평점은 1~5점만 입력할 수 있어 평균이 0이 될 수 없으므로, 0은 "평가 없음"을 뜻한다.
     * 이 구분이 없으면 평가가 하나도 없는 강의가 화면에서 0점짜리 강의처럼 보인다.
     */
    public boolean isRated() {
        return avgRating > 0;
    }

    public boolean isFull() {
        return enrolledCount >= capacity;
    }

    public void increaseEnrolled() {
        if (isFull()) {
            throw new IllegalStateException("정원이 초과되었습니다.");
        }
        this.enrolledCount++;
    }

    public void decreaseEnrolled() {
        if (this.enrolledCount > 0) {
            this.enrolledCount--;
        }
    }

    /** 실제 강의 시각 — "09:00~11:50" */
    public String getTimeRange() {
        return ClassPeriod.rangeOf(startPeriod, endPeriod);
    }

    /** 화면에 그대로 쓸 수 있는 요일·교시 표기 — "월 1-3교시" */
    public String getScheduleLabel() {
        return dayOfWeek + " " + startPeriod + "-" + endPeriod + "교시";
    }

    /** 시간표 충돌 여부 (같은 요일 + 교시 겹침) */
    public boolean conflictsWith(Course other) {
        if (!this.dayOfWeek.equals(other.dayOfWeek)) {
            return false;
        }
        return this.startPeriod <= other.endPeriod && other.startPeriod <= this.endPeriod;
    }
}
