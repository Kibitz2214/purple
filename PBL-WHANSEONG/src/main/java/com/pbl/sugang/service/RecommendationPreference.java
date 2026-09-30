package com.pbl.sugang.service;

import lombok.Builder;
import lombok.Getter;

import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/** 학생이 지정한 추천 시간표 편성 조건 */
@Getter
@Builder
public class RecommendationPreference {

    public static final int MIN_CREDITS = 3;
    public static final int MAX_CREDITS = 24;
    public static final int DEFAULT_CREDITS = 18;

    /** 목표 학점 */
    private final int targetCredits;

    /** 원하는 시간대 (오전 / 오후 / 무관) */
    private final TimeSlot timeSlot;

    /**
     * 전공 과목을 고를 학과. 비어 있으면 학과를 가리지 않는다.
     * 교양 과목은 어느 학과 학생이든 이수해야 하므로 이 조건과 무관하게 항상 후보에 남는다.
     */
    private final String department;

    /** 강의를 들을 수 없는 요일 (공강으로 비워 둔다) */
    private final Set<String> excludedDays;

    /**
     * 재생성 횟수. 0이면 최적안, 1 이상이면 같은 조건에서 후보 순서를 회전시켜 다른 조합을 만든다.
     * 같은 값이면 항상 같은 결과가 나오므로 새로고침해도 시간표가 흔들리지 않는다.
     */
    private final int variation;

    /** 조건 미지정 시 기본값 (학과 제한 없음) */
    public static RecommendationPreference defaults() {
        return defaults(null);
    }

    /** 처음 조건 화면을 열 때의 기본값. 보통 학생 본인의 학과를 넣어 준다. */
    public static RecommendationPreference defaults(String department) {
        return RecommendationPreference.builder()
                .targetCredits(DEFAULT_CREDITS)
                .timeSlot(TimeSlot.ANY)
                .department(normalize(department))
                .excludedDays(Set.of())
                .variation(0)
                .build();
    }

    /** 사용자 입력을 허용 범위로 보정해서 생성 */
    public static RecommendationPreference of(Integer targetCredits, TimeSlot timeSlot, String department,
                                              List<String> excludedDays, Integer variation) {
        int credits = clamp(targetCredits == null ? DEFAULT_CREDITS : targetCredits, MIN_CREDITS, MAX_CREDITS);

        // 알 수 없는 요일 값이 넘어와도 무시하고, 화면에 다시 표시할 수 있도록 입력 순서는 유지한다.
        Set<String> days = new LinkedHashSet<>();
        if (excludedDays != null) {
            excludedDays.stream()
                    .filter(EnrollmentService.TIMETABLE_DAYS::contains)
                    .forEach(days::add);
        }

        return RecommendationPreference.builder()
                .targetCredits(credits)
                .timeSlot(timeSlot == null ? TimeSlot.ANY : timeSlot)
                .department(normalize(department))
                .excludedDays(days)
                .variation(variation == null || variation < 0 ? 0 : variation)
                .build();
    }

    private static int clamp(int value, int min, int max) {
        return Math.min(Math.max(value, min), max);
    }

    /** 빈 문자열은 "학과 무관"과 같게 다룬다 */
    private static String normalize(String department) {
        return (department == null || department.isBlank()) ? null : department.trim();
    }

    public boolean hasDepartment() {
        return department != null;
    }

    /** 다른 조합을 찾아보려고 회전 횟수만 바꾼 사본 */
    public RecommendationPreference withVariation(int newVariation) {
        return RecommendationPreference.builder()
                .targetCredits(targetCredits)
                .timeSlot(timeSlot)
                .department(department)
                .excludedDays(excludedDays)
                .variation(Math.max(0, newVariation))
                .build();
    }

    /** 모든 요일을 공강으로 지정해 버려 추천이 불가능한 상태인지 */
    public boolean excludesEveryDay() {
        return excludedDays.containsAll(EnrollmentService.TIMETABLE_DAYS);
    }

    /** 화면에 조건을 한 줄로 요약해서 보여 준다 */
    public String getSummary() {
        StringBuilder sb = new StringBuilder();
        sb.append(targetCredits).append("학점");
        sb.append(" · ").append(hasDepartment() ? department : "전체 학과");
        sb.append(" · ").append(timeSlot.getLabel());
        if (timeSlot != TimeSlot.ANY) {
            sb.append("(").append(timeSlot.getPeriodRange()).append(")");
        }
        if (!excludedDays.isEmpty()) {
            sb.append(" · 공강 ").append(String.join("/", excludedDays));
        }
        return sb.toString();
    }
}
