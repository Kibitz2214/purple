package com.pbl.sugang.service;

import lombok.Builder;
import lombok.Getter;

/** 시간표 그리드의 셀 하나 (요일 x 교시) */
@Getter
@Builder
public class TimetableCell {

    /** 이 교시에 시작하는 강의명, 없으면 null */
    private final String label;

    /** 강의가 차지하는 교시 수 (rowspan) */
    private final int rowSpan;

    /** false면 위 셀의 rowspan에 덮여 렌더링하지 않음 */
    private final boolean render;
}
