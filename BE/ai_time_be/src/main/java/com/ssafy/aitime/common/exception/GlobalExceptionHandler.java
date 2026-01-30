package com.ssafy.aitime.common.exception;

import com.ssafy.aitime.common.exception.commonExceptions.DeleteFailedException;
import com.ssafy.aitime.common.exception.commonExceptions.InsertFailedException;
import com.ssafy.aitime.common.exception.commonExceptions.UpdateFailedException;
import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
import com.ssafy.aitime.domain.exam.exception.*;
import com.ssafy.aitime.domain.hospital.exception.*;
import com.ssafy.aitime.domain.invite.exception.AlreadyIssuedInviteCodeException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeAlreadyUsedException;
import com.ssafy.aitime.domain.invite.exception.InviteCodeNotFoundException;
import com.ssafy.aitime.domain.user.exception.*;
import com.ssafy.aitime.security.exception.RefreshTokenInvalidException;
import com.ssafy.aitime.security.exception.RefreshTokenMissingException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.validation.BindException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;
import tools.jackson.databind.exc.MismatchedInputException;

import java.util.Collections;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ExceptionHandler(BindException.class)
    protected ResponseEntity<ApiResponse<Object>> bindException(BindException e) {
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(
                        HttpStatus.BAD_REQUEST,
                        e.getBindingResult().getAllErrors().get(0).getDefaultMessage(),
                        Collections.emptyMap()
                ));

    }

    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ExceptionHandler(IllegalArgumentException.class)
    protected ResponseEntity<ApiResponse<Object>> illegalArgumentException(IllegalArgumentException e) {
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(
                        HttpStatus.BAD_REQUEST,
                        e.getMessage(),
                        Collections.emptyMap()
                ));

    }

    @ResponseStatus(HttpStatus.BAD_REQUEST)
    @ExceptionHandler(HandlerMethodValidationException.class)
    public ResponseEntity<ApiResponse<Object>> handleHandlerMethodValidationException(HandlerMethodValidationException e) {
        String message = e.getAllErrors().stream()
                .map(error -> error.getDefaultMessage())
                .collect(Collectors.joining(", "));

        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(
                        HttpStatus.BAD_REQUEST,
                        message,
                        Collections.emptyMap()
                ));

    }

    /********************************************************************************/
    /*                        Common CustomException                                    */
    /********************************************************************************/
    @ExceptionHandler({
            InsertFailedException.class,
            UpdateFailedException.class,
    })
    public ResponseEntity<ApiResponse<Object>> handleCommonBadRequestException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(HttpStatus.BAD_REQUEST, e.getMessage(), null));
    }
    @ExceptionHandler(MismatchedInputException.class)
    public ResponseEntity<ApiResponse<Object>> handleTypeMismatchException(MismatchedInputException e) {
        String errorMessage = "입력 값과 타입이 일치하지 않습니다.";
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(HttpStatus.BAD_REQUEST, errorMessage, null));
    }

    @ExceptionHandler({
            DeleteFailedException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleCommonInternalServerErrorException(RuntimeException e) {
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.of(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage(), null));
    }
    /********************************************************************************/
    /*                        User CustomException                                  */
    /********************************************************************************/

    @ExceptionHandler({
            InvalidUserRoleException.class,
            PhoneVerificationRequiredException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleUserBadRequestException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(HttpStatus.BAD_REQUEST, e.getMessage(), null));

    }

    @ExceptionHandler({
            UserAlreadyExistException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleUserConflictException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(ApiResponse.of(HttpStatus.CONFLICT, e.getMessage(), null));

    }

    @ExceptionHandler({
            InvalidPasswordException.class,
            BadCredentialsException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleUserUnauthorizedException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED).body(ApiResponse.of(HttpStatus.UNAUTHORIZED, e.getMessage(), null));
    }

    @ExceptionHandler({
            UserNotFoundException.class,
    })
    public ResponseEntity<ApiResponse<Object>> handleUserNotFoundException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND).body(ApiResponse.of(HttpStatus.NOT_FOUND, e.getMessage(), null));
    }

    /********************************************************************************/
    /*                        Child CustomException                                  */
    /********************************************************************************/

    @ExceptionHandler({
            ChildNotFoundException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleChildNotFoundException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND).body(ApiResponse.of(HttpStatus.NOT_FOUND, e.getMessage(), null));
    }

    @ExceptionHandler({
            ChildAccessDeniedException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleChildForbiddenException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.FORBIDDEN).body(ApiResponse.of(HttpStatus.FORBIDDEN, e.getMessage(), null));
    }



    /********************************************************************************/
    /*                        Security CustomException                              */
    /********************************************************************************/

    @ExceptionHandler({
            RefreshTokenMissingException.class,
            RefreshTokenInvalidException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleSecurityUnauthorizedException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED).body(ApiResponse.of(HttpStatus.UNAUTHORIZED, e.getMessage(), null));
    }


    /********************************************************************************/
    /*                        Hospital CustomException                              */
    /********************************************************************************/

    /**
     * 병원 관련 BAD_REQUEST (400)
     * - 이미 연동된 병원
     */
    @ExceptionHandler({
            HospitalAlreadyLinkedException.class,
            InvalidDoctorSelectionException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleHospitalBadRequestException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(HttpStatus.BAD_REQUEST, e.getMessage(), null));
    }

    /**
     * 병원 관련 NOT_FOUND (404)
     * - 의사를 찾을 수 없음
     * - 병원을 찾을 수 없음
     */
    @ExceptionHandler({
            DoctorNotFoundException.class,
            HospitalNotFoundException.class,
            HospitalStaffNotFoundException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleHospitalNotFoundException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.of(HttpStatus.NOT_FOUND, e.getMessage(), null));
    }

    @ExceptionHandler({
            HospitalStaffAccessDeniedException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleHospitalForbiddenException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.FORBIDDEN).body(ApiResponse.of(HttpStatus.FORBIDDEN, e.getMessage(), null));
    }
    /********************************************************************************/
    /*                        InviteCode CustomException                            */
    /********************************************************************************/

    /**
     * 초대코드 관련 BAD_REQUEST (400)
     * - 이미 사용된 초대 코드
     */
    @ExceptionHandler({
            InviteCodeAlreadyUsedException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleInviteCodeBadRequestException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(HttpStatus.BAD_REQUEST, e.getMessage(), null));
    }

    /**
     * 초대코드 관련 NOT_FOUND (404)
     * - 존재하지 않는 초대 코드
     */
    @ExceptionHandler({
            InviteCodeNotFoundException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleInviteCodeNotFoundException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.of(HttpStatus.NOT_FOUND, e.getMessage(), null));
    }

    @ExceptionHandler({
            AlreadyIssuedInviteCodeException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleInviteCodeConflictException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(ApiResponse.of(HttpStatus.CONFLICT, e.getMessage(), null));

    }

    /********************************************************************************/
    /*                        Exam CustomException                                  */
    /********************************************************************************/

    /**
     * 검사 관련 BAD_REQUEST (400)
     * - 잘못된 비디오 타입
     * - 잘못된 examId 형식
     */
    @ExceptionHandler({
            InvalidVideoTypeException.class,
            InvalidExamIdFormatException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleExamBadRequestException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(ApiResponse.of(HttpStatus.BAD_REQUEST, e.getMessage(), null));
    }

    /**
     * 검사 관련 NOT_FOUND (404)
     * - 검사를 찾을 수 없음
     * - 비디오를 찾을 수 없음
     */
    @ExceptionHandler({
            ExamNotFoundException.class,
            VideoNotFoundException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleExamNotFoundException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.NOT_FOUND)
                .body(ApiResponse.of(HttpStatus.NOT_FOUND, e.getMessage(), null));
    }

    /**
     * 검사 상태 CONFLICT (409)
     */
    @ExceptionHandler({
            ExamStatusNotAllowedException.class  // 추가
    })
    public ResponseEntity<ApiResponse<Object>> handleExamConflictException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.CONFLICT)
                .body(ApiResponse.of(HttpStatus.CONFLICT, e.getMessage(), null));
    }

    /**
     * S3 업로드 관련 INTERNAL_SERVER_ERROR (500)
     */
    @ExceptionHandler({
            S3UploadException.class
    })
    public ResponseEntity<ApiResponse<Object>> handleS3UploadException(RuntimeException e){
        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(ApiResponse.of(HttpStatus.INTERNAL_SERVER_ERROR, e.getMessage(), null));
    }
}
