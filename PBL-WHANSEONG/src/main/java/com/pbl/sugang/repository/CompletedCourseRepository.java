package com.pbl.sugang.repository;

import com.pbl.sugang.domain.CompletedCourse;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface CompletedCourseRepository extends JpaRepository<CompletedCourse, Long> {

    /** 강의(course)를 함께 로딩해 뷰에서의 LazyInitializationException 방지 */
    @Query("select c from CompletedCourse c join fetch c.course where c.student = :student")
    List<CompletedCourse> findByStudent(@Param("student") Student student);

    boolean existsByStudentAndCourse(Student student, Course course);

    Optional<CompletedCourse> findByStudentAndCourse(Student student, Course course);
}
