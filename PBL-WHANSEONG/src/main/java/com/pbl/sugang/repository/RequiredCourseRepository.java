package com.pbl.sugang.repository;

import com.pbl.sugang.domain.RequiredCourse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface RequiredCourseRepository extends JpaRepository<RequiredCourse, Long> {

    /** 강의(course)를 함께 로딩해 뷰에서의 LazyInitializationException 방지 */
    @Query("select r from RequiredCourse r join fetch r.course where r.department = :department")
    List<RequiredCourse> findByDepartment(@Param("department") String department);
}
