package com.pbl.sugang.repository;

import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.CourseReview;
import com.pbl.sugang.domain.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface CourseReviewRepository extends JpaRepository<CourseReview, Long> {

    /** 강의의 평가 목록 (작성자 함께 로딩, 최신순) */
    @Query("select r from CourseReview r join fetch r.student where r.course = :course order by r.id desc")
    List<CourseReview> findByCourseWithStudent(@Param("course") Course course);

    /** 여러 강의의 평가를 한 번에 조회 (교수 대시보드에서 담당 강의 후기 모아보기) */
    @Query("select r from CourseReview r join fetch r.student join fetch r.course "
            + "where r.course in :courses order by r.id desc")
    List<CourseReview> findByCoursesWithStudent(@Param("courses") List<Course> courses);

    /** 학생이 남긴 모든 평가 (내 신청내역에서 강의별 내 평점을 한 번에 표시하기 위한 조회) */
    @Query("select r from CourseReview r join fetch r.course where r.student = :student")
    List<CourseReview> findByStudentWithCourse(@Param("student") Student student);

    Optional<CourseReview> findByStudentAndCourse(Student student, Course course);

    @Query("select avg(r.rating) from CourseReview r where r.course = :course")
    Double averageRating(@Param("course") Course course);

    long countByCourse(Course course);
}
