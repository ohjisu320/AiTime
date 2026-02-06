package com.ssafy.aitime.infra.rabbitmq.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;

import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;



@Configuration
public class RabbitMQConfig {

    // 요청 큐 4개
    @Bean
    public Queue task1Queue() {
        return new Queue("analysis.req.task1", true); // durable=true
    }

    @Bean
    public Queue task2Queue() {
        return new Queue("analysis.req.task2", true);
    }

    @Bean
    public Queue task3Queue() {
        return new Queue("analysis.req.task3", true);
    }

    @Bean
    public Queue task4Queue() {
        return new Queue("analysis.req.task4", true);
    }

    // 결과 큐 1개
    @Bean
    public Queue resultQueue() {
        return new Queue("analysis.resp", true);
    }

    // RabbitMQ 전용 ObjectMapper
    @Bean(name = "rabbitObjectMapper")
    public ObjectMapper rabbitObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }

    // MessageConverter 없이 기본 RabbitTemplate만 사용
    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        return new RabbitTemplate(connectionFactory);
    }
}
