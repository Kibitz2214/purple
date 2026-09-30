package com.pbl.sugang.repository;

import com.pbl.sugang.domain.Staff;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface StaffRepository extends JpaRepository<Staff, Long> {
    Optional<Staff> findByLoginId(String loginId);
    boolean existsByLoginId(String loginId);
}
