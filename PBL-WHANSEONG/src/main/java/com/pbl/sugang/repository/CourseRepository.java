package com.pbl.sugang.repository;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.Course;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CourseRepository extends JpaRepository<Course, Long> {

    boolean existsByCourseCode(String courseCode);

    List<Course> findByNameContainingIgnoreCaseOrProfessorContainingIgnoreCase(String name, String professor);

    List<Course> findByCategory(Category category);

    List<Course> findByDepartment(String department);

    List<Course> findAllByOrderByAvgRatingDesc();

    /** 교수 담당 강의 (Course.professor가 교수 이름과 같은 강의) */
    List<Course> findByProfessorOrderByDayOfWeekAscStartPeriodAsc(String professor);

    /** 조교용 — 학과 전체 강의 */
    List<Course> findByDepartmentOrderByDayOfWeekAscStartPeriodAsc(String department);
}
