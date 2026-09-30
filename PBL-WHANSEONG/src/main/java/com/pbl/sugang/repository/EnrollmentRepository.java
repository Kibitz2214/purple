package com.pbl.sugang.repository;

import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.Enrollment;
import com.pbl.sugang.domain.Student;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface EnrollmentRepository extends JpaRepository<Enrollment, Long> {

    /** 강의(course)를 함께 로딩해 뷰에서의 LazyInitializationException 방지 */
    @Query("select e from Enrollment e join fetch e.course where e.student = :student order by e.id")
    List<Enrollment> findByStudent(@Param("student") Student student);

    boolean existsByStudentAndCourse(Student student, Course course);

    Optional<Enrollment> findByStudentAndCourse(Student student, Course course);

    long countByCourse(Course course);
}
