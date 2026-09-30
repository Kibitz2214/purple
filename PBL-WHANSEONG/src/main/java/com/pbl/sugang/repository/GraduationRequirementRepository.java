package com.pbl.sugang.repository;

import com.pbl.sugang.domain.GraduationRequirement;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface GraduationRequirementRepository extends JpaRepository<GraduationRequirement, Long> {

    List<GraduationRequirement> findByDepartment(String department);

    /**
     * 학과의 졸업요건 중 admissionYear가 학생의 입학년도 이하인 것을 최신순(admissionYear DESC)으로 조회한다.
     * 정확히 일치하는 입학년도의 요건이 있으면 그 값이 각 카테고리에서 가장 먼저 나오므로,
     * 카테고리별로 첫 번째 결과만 취하면(서비스단 처리) 정확 일치 우선 + 폴백 조회가 함께 처리된다.
     */
    @Query("SELECT r FROM GraduationRequirement r "
            + "WHERE r.department = :department AND r.admissionYear <= :admissionYear "
            + "ORDER BY r.admissionYear DESC")
    List<GraduationRequirement> findByDepartment(@Param("department") String department,
                                                  @Param("admissionYear") int admissionYear);
}
