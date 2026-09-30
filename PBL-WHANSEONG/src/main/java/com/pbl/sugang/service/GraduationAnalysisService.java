package com.pbl.sugang.service;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.CompletedCourse;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.GraduationRequirement;
import com.pbl.sugang.domain.RequiredCourse;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.repository.CompletedCourseRepository;
import com.pbl.sugang.repository.GraduationRequirementRepository;
import com.pbl.sugang.repository.RequiredCourseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class GraduationAnalysisService {

    private final GraduationRequirementRepository requirementRepository;
    private final RequiredCourseRepository requiredCourseRepository;
    private final CompletedCourseRepository completedCourseRepository;

    /** 학생의 학과 졸업요건 대비 이수 현황 및 미이수 필수과목 분석 */
    @Transactional(readOnly = true)
    public GraduationAnalysisResult analyze(Student student) {
        List<CompletedCourse> completed = completedCourseRepository.findByStudent(student);

        Map<Category, Integer> completedCreditsByCategory = completed.stream()
                .collect(Collectors.groupingBy(
                        c -> c.getCourse().getCategory(),
                        Collectors.summingInt(c -> c.getCourse().getCredit())));

        // admissionYear 이하 요건을 최신순으로 가져와 카테고리별 첫 번째(가장 가까운) 것만 사용
        Map<Category, GraduationRequirement> latestRequirementByCategory = new LinkedHashMap<>();
        for (GraduationRequirement r : requirementRepository.findByDepartment(student.getDepartment(), student.getAdmissionYear())) {
            latestRequirementByCategory.putIfAbsent(r.getCategory(), r);
        }

        List<GraduationProgress> progressList = latestRequirementByCategory.values()
                .stream()
                .map(r -> GraduationProgress.builder()
                        .category(r.getCategory())
                        .completedCredits(completedCreditsByCategory.getOrDefault(r.getCategory(), 0))
                        .requiredCredits(r.getRequiredCredits())
                        .build())
                .collect(Collectors.toList());

        Set<Long> completedCourseIds = completed.stream()
                .map(c -> c.getCourse().getId())
                .collect(Collectors.toSet());

        List<Course> missingRequiredCourses = requiredCourseRepository.findByDepartment(student.getDepartment())
                .stream()
                .map(RequiredCourse::getCourse)
                .filter(c -> !completedCourseIds.contains(c.getId()))
                .collect(Collectors.toList());

        int totalCompleted = progressList.stream().mapToInt(GraduationProgress::getCompletedCredits).sum();
        int totalRequired = progressList.stream().mapToInt(GraduationProgress::getRequiredCredits).sum();

        return GraduationAnalysisResult.builder()
                .progressList(progressList)
                .missingRequiredCourses(missingRequiredCourses)
                .completedCourses(completed)
                .totalCompletedCredits(totalCompleted)
                .totalRequiredCredits(totalRequired)
                .hasRequirementData(!progressList.isEmpty())
                .build();
    }
}
