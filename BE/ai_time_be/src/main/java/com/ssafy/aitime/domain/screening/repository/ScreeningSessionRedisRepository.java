package com.ssafy.aitime.domain.screening.repository;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.ssafy.aitime.domain.screening.service.dto.ScreeningSessionDTO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;

@Slf4j
@Repository
@RequiredArgsConstructor
public class ScreeningSessionRedisRepository {
    private final RedisTemplate<String, String> redisTemplate;
    private final ObjectMapper objectMapper = new ObjectMapper().registerModule(new JavaTimeModule());

    private static final long SESSION_TIMEOUT_HOURS = 1; // 1시간 TTL

    /**
     * 세션 저장 (by roomName)
     */
    public void save(ScreeningSessionDTO session) {
        try {
            String key = ScreeningSessionDTO.getRedisKey(session.roomName());
            String value = objectMapper.writeValueAsString(session);

            redisTemplate.opsForValue().set(key, value, SESSION_TIMEOUT_HOURS, TimeUnit.HOURS);

            // userId로도 조회 가능하도록 매핑 저장
            String userKey = ScreeningSessionDTO.getUserSessionKey(session.userId());
            redisTemplate.opsForValue().set(userKey, session.roomName(), SESSION_TIMEOUT_HOURS, TimeUnit.HOURS);

            log.info("Saved screening session to Redis: {}", session.roomName());

        } catch (JsonProcessingException e) {
            log.error("Failed to serialize session", e);
            throw new RuntimeException("세션 저장에 실패했습니다.", e);
        }
    }

    /**
     * roomName으로 세션 조회
     */
    public Optional<ScreeningSessionDTO> findByRoomName(String roomName) {
        try {
            String key = ScreeningSessionDTO.getRedisKey(roomName);
            String value = redisTemplate.opsForValue().get(key);

            if (value == null) {
                return Optional.empty();
            }

            ScreeningSessionDTO session = objectMapper.readValue(value, ScreeningSessionDTO.class);
            return Optional.of(session);

        } catch (JsonProcessingException e) {
            log.error("Failed to deserialize session", e);
            return Optional.empty();
        }
    }

    /**
     * userId로 진행 중인 세션 조회
     */
    public Optional<ScreeningSessionDTO> findByUserId(UUID userId) {
        String userKey = ScreeningSessionDTO.getUserSessionKey(userId);
        String roomName = redisTemplate.opsForValue().get(userKey);

        if (roomName == null) {
            return Optional.empty();
        }

        return findByRoomName(roomName);
    }

    /**
     * 세션 삭제
     */
    public void delete(String roomName) {
        String key = ScreeningSessionDTO.getRedisKey(roomName);
        redisTemplate.delete(key);
        log.info("Deleted screening session from Redis: {}", roomName);
    }

    /**
     * userId 매핑도 함께 삭제
     */
    public void deleteWithUserMapping(String roomName, UUID userId) {
        delete(roomName);

        String userKey = ScreeningSessionDTO.getUserSessionKey(userId);
        redisTemplate.delete(userKey);
    }
}
