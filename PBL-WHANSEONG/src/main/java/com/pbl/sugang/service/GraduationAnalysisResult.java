package com.pbl.sugang.service;

import com.pbl.sugang.domain.CompletedCourse;
import com.pbl.sugang.domain.Course;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

/** 한 학생에 대한 졸업요건 분석 결과 */
@Getter
@Builder
public class GraduationAnalysisResult {

    private final List<GraduationProgress> progressList;
    private final List<Course> missingRequiredCourses;
    private final List<CompletedCourse> completedCourses;
    private final int totalCompletedCredits;
    private final int totalRequiredCredits;
    /** 해당 학과의 졸업요건 데이터가 하나라도 등록되어 있는지 여부 */
    private final boolean hasRequirementData;

    public int getTotalShortfall() {
        return Math.max(totalRequiredCredits - totalCompletedCredits, 0);
    }
}
