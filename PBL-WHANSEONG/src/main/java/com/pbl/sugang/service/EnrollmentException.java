package com.pbl.sugang.service;

/** 수강신청 처리 중 발생하는 업무 예외 */
public class EnrollmentException extends RuntimeException {
    public EnrollmentException(String message) {
        super(message);
    }
}
