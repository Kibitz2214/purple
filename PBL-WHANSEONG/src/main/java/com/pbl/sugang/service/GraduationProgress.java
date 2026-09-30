package com.pbl.sugang.service;

import com.pbl.sugang.domain.Category;
import lombok.Builder;
import lombok.Getter;

/** 이수구분 하나에 대한 졸업요건 이수 현황 */
@Getter
@Builder
public class GraduationProgress {

    private final Category category;
    private final int completedCredits;
    private final int requiredCredits;

    public int getShortfall() {
        return Math.max(requiredCredits - completedCredits, 0);
    }

    public boolean isSatisfied() {
        return completedCredits >= requiredCredits;
    }
}
