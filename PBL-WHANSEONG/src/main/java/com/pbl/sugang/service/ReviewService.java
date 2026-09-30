package com.pbl.sugang.service;

import com.pbl.sugang.domain.Course;
import com.pbl.sugang.domain.CourseReview;
import com.pbl.sugang.domain.Student;
import com.pbl.sugang.repository.CourseRepository;
import com.pbl.sugang.repository.CourseReviewRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ReviewService {

    private final CourseReviewRepository reviewRepository;
    private final CourseRepository courseRepository;

    @Transactional(readOnly = true)
    public List<CourseReview> reviewsOf(Course course) {
        return reviewRepository.findByCourseWithStudent(course);
    }

    @Transactional(readOnly = true)
    public long countOf(Course course) {
        return reviewRepository.countByCourse(course);
    }

    @Transactional(readOnly = true)
    public Optional<CourseReview> myReview(Student student, Course course) {
        return reviewRepository.findByStudentAndCourse(student, course);
    }

    /** 강의 id → 내가 준 평점. 내 신청내역에서 강의별 별점을 표시할 때 사용한다. */
    @Transactional(readOnly = true)
    public Map<Long, Integer> myRatingsByCourseId(Student student) {
        return reviewRepository.findByStudentWithCourse(student).stream()
                .collect(Collectors.toMap(r -> r.getCourse().getId(), CourseReview::getRating));
    }

    /** 평가 작성 또는 수정 (학생당 강의별 1건) */
    @Transactional
    public void writeOrUpdate(Student student, Long courseId, int rating, String comment) {
        if (rating < 1 || rating > 5) {
            throw new EnrollmentException("평점은 1점에서 5점 사이여야 합니다.");
        }
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));

        String trimmed = comment == null ? null : comment.trim();

        reviewRepository.findByStudentAndCourse(student, course)
                .ifPresentOrElse(
                        review -> review.update(rating, trimmed),
                        () -> reviewRepository.save(CourseReview.builder()
                                .course(course)
                                .student(student)
                                .rating(rating)
                                .comment(trimmed)
                                .build()));

        recalcAvg(course);
    }

    /** 본인 평가 삭제 */
    @Transactional
    public void delete(Student student, Long courseId) {
        Course course = courseRepository.findById(courseId)
                .orElseThrow(() -> new EnrollmentException("존재하지 않는 강의입니다."));
        CourseReview review = reviewRepository.findByStudentAndCourse(student, course)
                .orElseThrow(() -> new EnrollmentException("작성한 평가가 없습니다."));
        reviewRepository.delete(review);
        recalcAvg(course);
    }

    /**
     * 강의의 평균 평점 재계산 후 course.avgRating 갱신.
     * 마지막 평가까지 삭제되면 0점짜리 강의가 아니라 "평가 없음" 상태로 되돌린다.
     */
    private void recalcAvg(Course course) {
        Double avg = reviewRepository.averageRating(course);
        if (avg == null) {
            course.clearRating();
        } else {
            course.updateAvgRating(avg);
        }
    }
}
