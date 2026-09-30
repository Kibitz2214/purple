package com.pbl.sugang.service;

import com.pbl.sugang.domain.Category;
import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.Enrollment;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.repository.CompletedCourseRepository;
import com.pbl.sugang.repository.CourseRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 학생별 맞춤 자동 추천 시간표 생성.
 *
 * <p>졸업요건을 채우는 방향으로 과목을 고른다. 핵심은 <b>이수구분별로 아직 필요한 학점을 계속 추적</b>하는 것이다.
 * 과목을 담을 때마다 해당 이수구분의 남은 학점을 깎고, 0이 되면 그 이수구분은 후보에서 제외한다.
 * 그래서 예컨대 교양필수를 이미 다 채운 학생에게는 평점이 아무리 높아도 교양필수를 다시 권하지 않고,
 * 아직 부족한 전공선택·교양선택 쪽으로 시간표를 채운다.
 *
 * <p>고르는 순서:
 * <ol>
 *   <li>졸업요건상 미이수 전공 필수 과목 — 대체 불가이므로 최우선</li>
 *   <li>남은 학점이 큰 이수구분부터 평점 높은 과목으로 보충</li>
 *   <li>모든 요건을 채우고도 목표 학점이 남으면 평점 상위 과목으로 채움</li>
 * </ol>
 *
 * <p>점심을 먹을 수 있도록 같은 요일에 4교시(12:00~12:50)와 5교시(13:00~13:50)가
 * 동시에 차지 않게 고른다. 다만 미이수 전공 필수는 대체할 과목이 없어 이 규칙에서 제외한다.
 * (필수 지정 과목 상당수가 3-5교시나 4-6교시에 걸쳐 있어, 예외를 두지 않으면 졸업이 불가능해진다)
 * 이미 신청/이수한 과목, 정원 마감 과목, 시간표가 겹치는 과목, 학생이 지정한 시간대 밖의 과목은 후보에서 제외한다.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TimetableRecommendationService {

    /** 추천 시간표가 채우려는 기본 목표 학점 (한 학기 권장 학점) */
    public static final int TARGET_CREDITS = RecommendationPreference.DEFAULT_CREDITS;

    /** 점심을 먹을 수 있도록 같은 날 4·5교시가 동시에 차지 않게 한다 */
    private static final int LUNCH_PERIOD_EARLY = 4;
    private static final int LUNCH_PERIOD_LATE = 5;

    /** "다시 만들기"에서 과목을 빼기 전에 회전만으로 다른 조합을 몇 번까지 찾아볼지 */
    private static final int MAX_RESHUFFLE_TRIES = 12;

    private final GraduationAnalysisService graduationAnalysisService;
    private final CourseRepository courseRepository;
    private final CompletedCourseRepository completedCourseRepository;
    private final EnrollmentService enrollmentService;

    public List<RecommendedCourse> recommend(Student student) {
        return recommend(student, RecommendationPreference.defaults());
    }

    public List<RecommendedCourse> recommend(Student student, RecommendationPreference pref) {
        return recommend(student, pref, Set.of());
    }

    /**
     * 직전 추천과 반드시 다른 조합을 만든다 ("다시 만들기"용).
     *
     * <p>회전만으로는 담기는 과목이 그대로이고 순서만 바뀌는 경우가 있다.
     * 그래서 회전을 더 돌려 보고, 그래도 같으면 직전 결과의 과목을 하나 빼고 다시 짠다.
     * 뺀 과목은 결과에 들어올 수 없으므로 조합이 반드시 달라진다.
     */
    public List<RecommendedCourse> recommendDifferentFrom(Student student, RecommendationPreference pref,
                                                          List<Long> previousCourseIds) {
        List<RecommendedCourse> result = recommend(student, pref, Set.of());
        if (previousCourseIds == null || previousCourseIds.isEmpty()
                || differsFrom(result, previousCourseIds)) {
            return result;
        }

        // ① 과목을 빼지 않고 회전만 더 돌려 본다 — 품질을 유지한 채 조합이 바뀌면 가장 좋다.
        for (int extra = 1; extra <= MAX_RESHUFFLE_TRIES; extra++) {
            List<RecommendedCourse> retry =
                    recommend(student, pref.withVariation(pref.getVariation() + extra), Set.of());
            if (differsFrom(retry, previousCourseIds)) {
                return retry;
            }
        }

        // ② 그래도 같으면 직전 결과에서 한 과목을 뺀다.
        //    뒤쪽(우선순위가 낮은 채움용 과목)부터 빼서 전공 필수를 최대한 지킨다.
        for (int i = previousCourseIds.size() - 1; i >= 0; i--) {
            List<RecommendedCourse> retry = recommend(student, pref, Set.of(previousCourseIds.get(i)));
            if (!retry.isEmpty()) {
                return retry;
            }
        }
        return result;
    }

    /** 담긴 과목이 직전과 다른지 (순서만 다른 것은 같은 것으로 본다) */
    private boolean differsFrom(List<RecommendedCourse> result, List<Long> previousCourseIds) {
        Set<Long> now = result.stream().map(r -> r.getCourse().getId()).collect(Collectors.toSet());
        return !now.equals(new HashSet<>(previousCourseIds));
    }

    /**
     * @param banned 이번 편성에서 제외할 강의. "다시 만들기"가 같은 시간표를 내놓지 않게 할 때 쓴다.
     */
    private List<RecommendedCourse> recommend(Student student, RecommendationPreference pref, Set<Long> banned) {
        if (pref.excludesEveryDay()) {
            return List.of();
        }

        GraduationAnalysisResult analysis = graduationAnalysisService.analyze(student);

        List<Course> alreadyEnrolled = enrollmentService.findByStudent(student).stream()
                .map(Enrollment::getCourse)
                .toList();

        Set<Long> excludedIds = new HashSet<>(banned);
        alreadyEnrolled.forEach(c -> excludedIds.add(c.getId()));
        completedCourseRepository.findByStudent(student).forEach(c -> excludedIds.add(c.getCourse().getId()));

        List<RecommendedCourse> picked = new ArrayList<>();
        // 이미 신청한 과목도 시간 충돌·학점 한도 계산에 포함하되, 추천 목록에는 새로 고른 과목만 담는다.
        List<Course> pickedCourses = new ArrayList<>(alreadyEnrolled);

        // 이수구분별로 아직 필요한 학점. 과목을 담을 때마다 줄여 가며 판단 기준으로 쓴다.
        Map<Category, Integer> needed = remainingCreditsByCategory(analysis, alreadyEnrolled);

        // ① 미이수 전공 필수 — 다른 과목으로 대체할 수 없으므로 먼저 확보한다.
        for (Course c : rotate(analysis.getMissingRequiredCourses(), pref.getVariation())) {
            if (isAddable(c, excludedIds, pickedCourses, pref, true)) {
                add(c, "전공 필수 미이수 — 반드시 들어야 함", excludedIds, pickedCourses, picked);
                deduct(needed, c);
            }
        }

        // ② 아직 부족한 이수구분을, 부족분이 큰 쪽부터 채운다.
        fillShortfalls(needed, excludedIds, pickedCourses, picked, pref);

        // ③ 요건을 다 채우고도 목표 학점이 남으면 평점 상위 과목으로 채운다.
        fillRemainingCredits(needed, excludedIds, pickedCourses, picked, pref);

        return picked;
    }

    /**
     * 이수구분별로 아직 필요한 학점.
     * 졸업요건 대비 부족분에서, 이번 학기에 이미 신청해 둔 과목의 학점을 미리 빼 둔다.
     * (신청한 과목은 이수할 예정이므로, 그만큼은 추천으로 다시 채울 필요가 없다)
     */
    private Map<Category, Integer> remainingCreditsByCategory(GraduationAnalysisResult analysis,
                                                              List<Course> alreadyEnrolled) {
        Map<Category, Integer> needed = new EnumMap<>(Category.class);
        for (GraduationProgress p : analysis.getProgressList()) {
            needed.put(p.getCategory(), p.getShortfall());
        }
        alreadyEnrolled.forEach(c -> deduct(needed, c));
        return needed;
    }

    /** 남은 학점이 가장 많은 이수구분부터 평점 높은 과목으로 채운다 */
    private void fillShortfalls(Map<Category, Integer> needed, Set<Long> excludedIds,
                                List<Course> pickedCourses, List<RecommendedCourse> picked,
                                RecommendationPreference pref) {
        // 조건에 맞는 후보가 더 없는 이수구분은 제외해 두어야 같은 구분을 무한히 다시 시도하지 않는다.
        Set<Category> exhausted = EnumSet.noneOf(Category.class);

        while (true) {
            Category target = neediestCategory(needed, exhausted);
            if (target == null) {
                return;
            }
            Course pick = bestCandidateOf(target, excludedIds, pickedCourses, pref);
            if (pick == null) {
                exhausted.add(target);
                continue;
            }
            add(pick, target.getLabel() + " " + needed.get(target) + "학점 부족 — 보충",
                    excludedIds, pickedCourses, picked);
            deduct(needed, pick);
        }
    }

    /**
     * 목표 학점이 남았을 때 채운다.
     * 아직 부족한 이수구분의 과목을 먼저 쓰고, 이미 충족한 이수구분은 마지막 수단으로만 쓴다.
     */
    private void fillRemainingCredits(Map<Category, Integer> needed, Set<Long> excludedIds,
                                      List<Course> pickedCourses, List<RecommendedCourse> picked,
                                      RecommendationPreference pref) {
        List<Course> byRating = rotate(courseRepository.findAllByOrderByAvgRatingDesc(), pref.getVariation());

        for (Course c : byRating) {
            if (isFull(pickedCourses, pref) ) {
                return;
            }
            if (stillNeeds(needed, c) && isAddable(c, excludedIds, pickedCourses, pref)) {
                add(c, c.getCategory().getLabel() + " 학점 추가 확보", excludedIds, pickedCourses, picked);
                deduct(needed, c);
            }
        }

        for (Course c : byRating) {
            if (isFull(pickedCourses, pref)) {
                return;
            }
            if (isAddable(c, excludedIds, pickedCourses, pref)) {
                add(c, c.getCategory().getLabel() + " 충족 — 평점 높아 추천", excludedIds, pickedCourses, picked);
            }
        }
    }

    /** 아직 학점이 부족한 이수구분 중 가장 많이 모자란 것 */
    private Category neediestCategory(Map<Category, Integer> needed, Set<Category> exhausted) {
        return needed.entrySet().stream()
                .filter(e -> e.getValue() > 0)
                .filter(e -> !exhausted.contains(e.getKey()))
                .max(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(null);
    }

    /** 해당 이수구분에서 지금 담을 수 있는 가장 평점 높은 과목 */
    private Course bestCandidateOf(Category category, Set<Long> excludedIds,
                                   List<Course> pickedCourses, RecommendationPreference pref) {
        List<Course> candidates = rotate(courseRepository.findByCategory(category).stream()
                .sorted(Comparator.comparingDouble(Course::getAvgRating).reversed())
                .toList(), pref.getVariation());

        return candidates.stream()
                .filter(c -> isAddable(c, excludedIds, pickedCourses, pref))
                .findFirst()
                .orElse(null);
    }

    private boolean stillNeeds(Map<Category, Integer> needed, Course c) {
        return needed.getOrDefault(c.getCategory(), 0) > 0;
    }

    /** 이수구분의 남은 학점을 과목 학점만큼 줄인다 (음수로 내려가지 않는다) */
    private void deduct(Map<Category, Integer> needed, Course c) {
        needed.computeIfPresent(c.getCategory(), (category, left) -> Math.max(0, left - c.getCredit()));
    }

    private boolean isFull(List<Course> pickedCourses, RecommendationPreference pref) {
        return totalCredits(pickedCourses) >= pref.getTargetCredits();
    }

    /**
     * 후보 목록을 variation 칸만큼 회전시킨다.
     * 평점순 정렬은 유지한 채 시작 지점만 옮기므로, "다시 만들기"를 눌렀을 때
     * 품질이 비슷하면서도 다른 조합이 나온다. 같은 variation이면 결과도 항상 같다.
     */
    private List<Course> rotate(List<Course> candidates, int variation) {
        if (variation <= 0 || candidates.size() < 2) {
            return candidates;
        }
        int offset = variation % candidates.size();
        if (offset == 0) {
            return candidates;
        }
        List<Course> rotated = new ArrayList<>(candidates.subList(offset, candidates.size()));
        rotated.addAll(candidates.subList(0, offset));
        return rotated;
    }

    private boolean isAddable(Course c, Set<Long> excludedIds, List<Course> pickedCourses,
                              RecommendationPreference pref) {
        return isAddable(c, excludedIds, pickedCourses, pref, false);
    }

    /**
     * @param mandatory 대체 불가능한 과목인지. 미이수 전공 필수가 여기 해당하며,
     *                  점심시간 규칙 때문에 졸업에 필요한 과목이 영영 빠지지 않도록 예외로 둔다.
     */
    private boolean isAddable(Course c, Set<Long> excludedIds, List<Course> pickedCourses,
                              RecommendationPreference pref, boolean mandatory) {
        if (excludedIds.contains(c.getId()) || c.isFull()) {
            return false;
        }
        if (!withinPreferredTime(c, pref) || !withinPreferredDepartment(c, pref)) {
            return false;
        }
        if (totalCredits(pickedCourses) + c.getCredit() > pref.getTargetCredits()) {
            return false;
        }
        if (!mandatory && !keepsLunchBreak(c, pickedCourses)) {
            return false;
        }
        return pickedCourses.stream().noneMatch(already -> already.conflictsWith(c));
    }

    /**
     * 이 과목을 담아도 그 요일에 4·5교시가 동시에 차지 않는지.
     * 이미 (필수 과목 때문에) 두 교시가 다 찬 요일이면 더 제한하지 않는다 —
     * 그날 점심시간은 이미 없어졌으므로 나머지 시간대까지 막을 이유가 없다.
     */
    private boolean keepsLunchBreak(Course candidate, List<Course> pickedCourses) {
        String day = candidate.getDayOfWeek();
        if (occupiesBothLunchPeriods(pickedCourses, day)) {
            return true;
        }
        List<Course> after = new ArrayList<>(pickedCourses);
        after.add(candidate);
        return !occupiesBothLunchPeriods(after, day);
    }

    private boolean occupiesBothLunchPeriods(List<Course> courses, String day) {
        boolean early = false;
        boolean late = false;
        for (Course c : courses) {
            if (!c.getDayOfWeek().equals(day)) {
                continue;
            }
            early |= covers(c, LUNCH_PERIOD_EARLY);
            late |= covers(c, LUNCH_PERIOD_LATE);
        }
        return early && late;
    }

    private boolean covers(Course c, int period) {
        return c.getStartPeriod() <= period && period <= c.getEndPeriod();
    }

    /** 학생이 지정한 공강 요일과 시간대(오전/오후) 안에 완전히 들어오는 과목만 통과시킨다 */
    private boolean withinPreferredTime(Course c, RecommendationPreference pref) {
        if (pref.getExcludedDays().contains(c.getDayOfWeek())) {
            return false;
        }
        TimeSlot slot = pref.getTimeSlot();
        return c.getStartPeriod() >= slot.getStartPeriod() && c.getEndPeriod() <= slot.getEndPeriod();
    }

    /**
     * 학생이 고른 학과의 전공 과목만 통과시킨다.
     * 교양 과목은 어느 학과 학생이든 이수해야 하므로 학과와 무관하게 통과시킨다.
     * (이 조건이 없으면 컴퓨터공학과 학생에게 간호학과 전공이 전공학점 보충용으로 추천된다)
     */
    private boolean withinPreferredDepartment(Course c, RecommendationPreference pref) {
        if (!pref.hasDepartment()) {
            return true;
        }
        if (c.getCategory() == Category.GENERAL_REQUIRED || c.getCategory() == Category.GENERAL_ELECTIVE) {
            return true;
        }
        return pref.getDepartment().equals(c.getDepartment());
    }

    private void add(Course c, String reason, Set<Long> excludedIds, List<Course> pickedCourses,
                      List<RecommendedCourse> picked) {
        pickedCourses.add(c);
        excludedIds.add(c.getId());
        picked.add(RecommendedCourse.builder().course(c).reason(reason).build());
    }

    private int totalCredits(List<Course> courses) {
        return courses.stream().mapToInt(Course::getCredit).sum();
    }
}
