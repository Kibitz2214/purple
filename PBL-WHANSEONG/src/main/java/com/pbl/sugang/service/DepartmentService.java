package com.pbl.sugang.service;

import com.pbl.sugang.domain.Department;
import com.pbl.sugang.repository.DepartmentRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class DepartmentService {

    /**
     * 이수구분을 담기 위한 이름일 뿐 학위 과정이 아니라, 학생이 소속될 수 없는 학과.
     * (교양 강의는 이 이름으로 개설되므로 교수 등록에서는 고를 수 있어야 한다)
     */
    private static final String NON_DEGREE_DEPARTMENT = "교양";

    private final DepartmentRepository departmentRepository;

    /** 학과 이름 전체 (가나다순) — 교수·조교 등록용 */
    public List<String> findAllNames() {
        return departmentRepository.findAllByOrderByNameAsc().stream()
                .map(Department::getName)
                .toList();
    }

    /** 학생이 소속될 수 있는 학과만 — 학생 등록용 */
    public List<String> findDegreePrograms() {
        return findAllNames().stream()
                .filter(name -> !NON_DEGREE_DEPARTMENT.equals(name))
                .toList();
    }
}
