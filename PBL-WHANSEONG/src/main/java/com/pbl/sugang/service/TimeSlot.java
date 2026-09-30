package com.pbl.sugang.service;

/** 추천 시간표에서 학생이 선택할 수 있는 시간대 */
public enum TimeSlot {

    ANY("무관", 1, EnrollmentService.TIMETABLE_MAX_PERIOD),
    MORNING("오전", 1, 4),
    AFTERNOON("오후", 5, EnrollmentService.TIMETABLE_MAX_PERIOD);

    private final String label;
    private final int startPeriod;
    private final int endPeriod;

    TimeSlot(String label, int startPeriod, int endPeriod) {
        this.label = label;
        this.startPeriod = startPeriod;
        this.endPeriod = endPeriod;
    }

    public String getLabel() {
        return label;
    }

    public int getStartPeriod() {
        return startPeriod;
    }

    public int getEndPeriod() {
        return endPeriod;
    }

    /** 화면에 안내할 교시 범위 (예: "1-4교시") */
    public String getPeriodRange() {
        return startPeriod + "-" + endPeriod + "교시";
    }
}
