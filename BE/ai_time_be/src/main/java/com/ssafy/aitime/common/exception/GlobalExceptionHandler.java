package com.ssafy.aitime.common.exception;

import com.ssafy.aitime.common.exception.commonExceptions.DeleteFailedException;
import com.ssafy.aitime.common.exception.commonExceptions.InsertFailedException;
import com.ssafy.aitime.common.exception.commonExceptions.UpdateFailedException;
import com.ssafy.aitime.common.response.ApiResponse;
import com.ssafy.aitime.domain.child.exception.ChildAccessDeniedException;
import com.ssafy.aitime.domain.child.exception.ChildNotFoundException;
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
import com.fasterxml.jackson.databind.exc.MismatchedInputException;


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

}
