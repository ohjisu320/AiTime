package com.ssafy.aitime.domain.exam.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UuidGenerator;
import java.util.UUID;

@Getter
@Entity
@Table(name = "ados")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Ados {

    @Id
    @GeneratedValue
    @UuidGenerator
    @Column(name = "ados_id", columnDefinition = "BINARY(16)")
    private UUID adosId;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(
            name = "exam_id",
            nullable = false,
            foreignKey = @ForeignKey(
                    name = "fk_ados_exam",
                    foreignKeyDefinition = "FOREIGN KEY (exam_id) REFERENCES exam(exam_id) ON DELETE CASCADE"
            )
    )
    private Exam exam;

    // A 섹션
    @Column(name = "a2")
    private Integer a2;

    @Column(name = "a3")
    private Integer a3;

    @Column(name = "a7")
    private Integer a7;

    @Column(name = "a8")
    private Integer a8;

    // B 섹션
    @Column(name = "b1")
    private Integer b1;

    @Column(name = "b4")
    private Integer b4;

    @Column(name = "b5")
    private Integer b5;

    @Column(name = "b6")
    private Integer b6;

    @Column(name = "b7")
    private Integer b7;

    @Column(name = "b8")
    private Integer b8;

    @Column(name = "b9")
    private Integer b9;

    @Column(name = "b12")
    private Integer b12;

    @Column(name = "b13")
    private Integer b13;

    @Column(name = "b14")
    private Integer b14;

    @Column(name = "b15")
    private Integer b15;

    @Column(name = "b16b")
    private Integer b16b;

    @Column(name = "b18")
    private Integer b18;

    @Column(name = "social_affect_total")
    private Integer socialAffectTotal;

    // D 섹션
    @Column(name = "d1")
    private Integer d1;

    @Column(name = "d2")
    private Integer d2;

    @Column(name = "d5")
    private Integer d5;

    @Column(name = "rrb_total")
    private Integer rrbTotal;

    @Column(name = "total")
    private Integer total;

    @Builder
    public Ados(Exam exam, Integer a2, Integer a3, Integer a7, Integer a8,
                Integer b1, Integer b4, Integer b5, Integer b6, Integer b7,
                Integer b8, Integer b9, Integer b12, Integer b13, Integer b14,
                Integer b15, Integer b16b, Integer b18,
                Integer socialAffectTotal,
                Integer d1, Integer d2, Integer d5,
                Integer rrbTotal, Integer total) {
        this.exam = exam;
        this.a2 = a2;
        this.a3 = a3;
        this.a7 = a7;
        this.a8 = a8;
        this.b1 = b1;
        this.b4 = b4;
        this.b5 = b5;
        this.b6 = b6;
        this.b7 = b7;
        this.b8 = b8;
        this.b9 = b9;
        this.b12 = b12;
        this.b13 = b13;
        this.b14 = b14;
        this.b15 = b15;
        this.b16b = b16b;
        this.b18 = b18;
        this.socialAffectTotal = socialAffectTotal;
        this.d1 = d1;
        this.d2 = d2;
        this.d5 = d5;
        this.rrbTotal = rrbTotal;
        this.total = total;
    }

    // 업데이트 메서드 (필요시 사용)
    public void updateScores(Integer a2, Integer a3, Integer a7, Integer a8,
                             Integer b1, Integer b4, Integer b5, Integer b6, Integer b7,
                             Integer b8, Integer b9, Integer b12, Integer b13, Integer b14,
                             Integer b15, Integer b16b, Integer b18,
                             Integer socialAffectTotal,
                             Integer d1, Integer d2, Integer d5,
                             Integer rrbTotal, Integer total) {
        this.a2 = a2;
        this.a3 = a3;
        this.a7 = a7;
        this.a8 = a8;
        this.b1 = b1;
        this.b4 = b4;
        this.b5 = b5;
        this.b6 = b6;
        this.b7 = b7;
        this.b8 = b8;
        this.b9 = b9;
        this.b12 = b12;
        this.b13 = b13;
        this.b14 = b14;
        this.b15 = b15;
        this.b16b = b16b;
        this.b18 = b18;
        this.socialAffectTotal = socialAffectTotal;
        this.d1 = d1;
        this.d2 = d2;
        this.d5 = d5;
        this.rrbTotal = rrbTotal;
        this.total = total;
    }
}
