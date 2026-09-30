package com.pbl.sugang.domain;

import lombok.Getter;

import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.IntStream;

/**
 * 교시별 실제 강의 시각.
 *
 * <p>1교시는 09:00에 시작해 50분 수업하고, 쉬는 시간 10분을 두고 다음 교시가 시작한다.
 * 결과적으로 매 교시가 정각에 시작해 50분에 끝난다 (1교시 09:00~09:50, 2교시 10:00~10:50 …).
 */
@Getter
public class ClassPeriod {

    /** 1교시 시작 시각 */
    public static final LocalTime FIRST_START = LocalTime.of(9, 0);

    /** 한 교시 수업 시간(분) */
    public static final int CLASS_MINUTES = 50;

    /** 교시 사이 쉬는 시간(분) */
    public static final int BREAK_MINUTES = 10;

    /** 하루에 편성할 수 있는 마지막 교시 */
    public static final int MAX_PERIOD = 9;

    private static final DateTimeFormatter HHMM = DateTimeFormatter.ofPattern("HH:mm");

    private final int period;
    private final String start;
    private final String end;

    private ClassPeriod(int period) {
        this.period = period;
        this.start = HHMM.format(startTimeOf(period));
        this.end = HHMM.format(endTimeOf(period));
    }

    public static LocalTime startTimeOf(int period) {
        return FIRST_START.plusMinutes((long) (period - 1) * (CLASS_MINUTES + BREAK_MINUTES));
    }

    public static LocalTime endTimeOf(int period) {
        return startTimeOf(period).plusMinutes(CLASS_MINUTES);
    }

    /** "09:00~09:50" */
    public String getRange() {
        return start + "~" + end;
    }

    /** 여러 교시에 걸친 수업의 전체 시각 — "09:00~11:50" */
    public static String rangeOf(int startPeriod, int endPeriod) {
        return HHMM.format(startTimeOf(startPeriod)) + "~" + HHMM.format(endTimeOf(endPeriod));
    }

    /** 시간표 머리글에 쓸 1~마지막 교시 목록 */
    public static List<ClassPeriod> all() {
        return IntStream.rangeClosed(1, MAX_PERIOD)
                .mapToObj(ClassPeriod::new)
                .toList();
    }
}
