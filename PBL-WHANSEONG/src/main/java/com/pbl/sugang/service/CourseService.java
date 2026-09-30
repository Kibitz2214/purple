package com.pbl.sugang.service;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.repository.CourseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CourseService {

    private final CourseRepository courseRepository;

    /** 검색어/학과/이수구분 필터 + 평점순 정렬로 강의 목록 조회 */
    public List<Course> search(String keyword, String department, Category category, boolean sortByRating) {
        List<Course> result;
        if (StringUtils.hasText(keyword)) {
            result = courseRepository
                    .findByNameContainingIgnoreCaseOrProfessorContainingIgnoreCase(keyword, keyword);
        } else if (StringUtils.hasText(department)) {
            result = courseRepository.findByDepartment(department);
        } else if (category != null) {
            result = courseRepository.findByCategory(category);
        } else {
            result = courseRepository.findAll();
        }

        if (StringUtils.hasText(department)) {
            result = result.stream().filter(c -> department.equals(c.getDepartment())).toList();
        }
        if (category != null) {
            result = result.stream().filter(c -> c.getCategory() == category).toList();
        }
        if (sortByRating) {
            result = result.stream()
                    .sorted((a, b) -> Double.compare(b.getAvgRating(), a.getAvgRating()))
                    .toList();
        }
        return result;
    }

    /** 강의가 개설된 학과 목록 (강의 목록 화면의 학과 필터 선택지) */
    public List<String> findDepartmentsWithCourses() {
        return courseRepository.findAll().stream()
                .map(Course::getDepartment)
                .distinct()
                .sorted()
                .toList();
    }

    /**
     * 검색 결과를 한 페이지 분량만 잘라서 반환한다.
     * 검색·필터가 메모리에서 이뤄지므로 페이지도 같은 자리에서 자른다.
     * 요청한 페이지가 마지막 페이지를 넘으면 마지막 페이지로 보정해, 빈 화면 대신 결과가 보이도록 한다.
     *
     * @param page 0부터 시작하는 페이지 번호
     */
    public Page<Course> search(String keyword, String department, Category category, boolean sortByRating,
                               int page, int size) {
        List<Course> all = search(keyword, department, category, sortByRating);

        int totalPages = (int) Math.ceil((double) all.size() / size);
        int safePage = Math.min(Math.max(page, 0), Math.max(totalPages - 1, 0));

        int from = Math.min(safePage * size, all.size());
        int to = Math.min(from + size, all.size());

        return new PageImpl<>(all.subList(from, to), PageRequest.of(safePage, size), all.size());
    }

    public Course findById(Long id) {
        return courseRepository.findById(id)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));
    }
}
