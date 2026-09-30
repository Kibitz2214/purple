package com.pbl.sugang.domain;

/** 이수구분 */
public enum Category {
    MAJOR_REQUIRED("전공필수"),
    MAJOR_ELECTIVE("전공선택"),
    GENERAL_REQUIRED("교양필수"),
    GENERAL_ELECTIVE("교양선택");

    private final String label;

    Category(String label) {
        this.label = label;
    }

    public String getLabel() {
        return label;
    }
}
