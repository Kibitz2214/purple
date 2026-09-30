package com.pbl.sugang.domain;

/** 교직원 구분 */
public enum StaffRole {
    PROFESSOR("교수"),
    ASSISTANT("조교");

    private final String label;

    StaffRole(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }
}
