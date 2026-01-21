package com.ssafy.aitime.common.exception;

import com.ssafy.aitime.common.exception.commonExceptions.DeleteFailedException;
import com.ssafy.aitime.common.exception.commonExceptions.InsertFailedException;
import com.ssafy.aitime.common.exception.commonExceptions.UpdateFailedException;
import com.ssafy.aitime.common.response.ApiResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
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
}
