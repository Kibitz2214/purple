package com.pbl.sugang.service;

import com.pbl.sugang.domain.Course;
import lombok.Builder;
import lombok.Getter;

/** 자동 시간표 추천에 포함된 과목 한 건 (추천 사유 포함) */
@Getter
@Builder
public class RecommendedCourse {

    private final Course course;

    /** 추천 사유: 전공 필수 미이수 / 이수구분 학점 보충 / 평점 우수 */
    private final String reason;
}
