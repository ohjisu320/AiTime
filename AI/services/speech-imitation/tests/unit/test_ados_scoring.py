import unittest

from app.pipeline.context import PipelineContext, RepResult, TrialResult


class TestADOSScoring(unittest.TestCase):
    def setUp(self) -> None:
        self.context = PipelineContext(request_id="test_req", age_months=18)

    def _create_reps(
        self, count: int, detected: bool, success: bool, reason: str | None
    ) -> list[RepResult]:
        return [
            RepResult(
                rep_index=i,
                response_detected=detected,
                latency_s=0.5 if detected else None,
                success=success,
                failure_reason=reason if not success else None,
                similarity=0.9 if success else 0.1,
                child_mean_f0=None,
            )
            for i in range(count)
        ]

    def test_no_response(self) -> None:
        """반응 없음: A3=8, B18=False (성공 0회)"""
        # 3회 시도, 모두 감지 안됨
        reps = self._create_reps(3, detected=False, success=False, reason="NO_RESPONSE")
        self.context.trial_results = [TrialResult(0, "s1", "mama", reps)]

        res = self.context.to_result()
        ados = res["metrics"]["ADOS"]

        self.assertEqual(ados["A3"], 8)
        self.assertFalse(ados["B18"])

    def test_all_success(self) -> None:
        """모두 성공: A3=0, B18=True"""
        reps = self._create_reps(3, detected=True, success=True, reason=None)
        self.context.trial_results = [TrialResult(0, "s1", "mama", reps)]

        res = self.context.to_result()
        ados = res["metrics"]["ADOS"]

        self.assertEqual(ados["A3"], 0)
        self.assertTrue(ados["B18"])

    def test_partial_bad_prosody_level_1(self) -> None:
        """A3 Level 1: 1~20% BAD_PROSODY"""
        # 10회 시행: 1회 BAD_PROSODY, 9회 성공
        # Ratio = 1/10 = 0.1 (10%) -> Score 1
        bad_reps = self._create_reps(
            1, detected=True, success=False, reason="BAD_PROSODY"
        )
        good_reps = self._create_reps(9, detected=True, success=True, reason=None)

        self.context.trial_results = [
            TrialResult(0, "s1", "mama", bad_reps + good_reps)
        ]

        res = self.context.to_result()
        ados = res["metrics"]["ADOS"]

        self.assertEqual(ados["A3"], 1)
        self.assertTrue(ados["B18"])

    def test_partial_bad_prosody_level_2(self) -> None:
        """A3 Level 2: 21~79% BAD_PROSODY"""
        # 10회 시행: 3회 BAD_PROSODY, 7회 성공
        # Ratio = 3/10 = 0.3 (30%) -> Score 2
        bad_reps = self._create_reps(
            3, detected=True, success=False, reason="BAD_PROSODY"
        )
        good_reps = self._create_reps(7, detected=True, success=True, reason=None)

        self.context.trial_results = [
            TrialResult(0, "s1", "mama", bad_reps + good_reps)
        ]

        res = self.context.to_result()
        ados = res["metrics"]["ADOS"]

        self.assertEqual(ados["A3"], 2)
        self.assertTrue(ados["B18"])

    def test_high_bad_prosody_level_3(self) -> None:
        """A3 Level 3: >= 80% BAD_PROSODY"""
        # 10회 시행: 9회 BAD_PROSODY, 1회 성공
        # Ratio = 9/10 = 0.9 (90%) -> Score 3
        bad_reps = self._create_reps(
            9, detected=True, success=False, reason="BAD_PROSODY"
        )
        good_reps = self._create_reps(1, detected=True, success=True, reason=None)

        self.context.trial_results = [
            TrialResult(0, "s1", "mama", bad_reps + good_reps)
        ]

        res = self.context.to_result()
        ados = res["metrics"]["ADOS"]

        self.assertEqual(ados["A3"], 3)
        self.assertTrue(ados["B18"])

    def test_all_fail_no_success(self) -> None:
        """모든 시도 실패 (혼합 사유): B18=False"""
        # BAD_PROSODY 5회, LOW_SIMILARITY 5회
        # 성공 0회 -> B18=False
        # A3 Ratio = 5 BAD_PROSODY / 10 Detected = 0.5 (50%) -> Score 2

        bad_reps = self._create_reps(
            5, detected=True, success=False, reason="BAD_PROSODY"
        )
        low_sim_reps = self._create_reps(
            5, detected=True, success=False, reason="LOW_SIMILARITY"
        )

        self.context.trial_results = [
            TrialResult(0, "s1", "mama", bad_reps + low_sim_reps)
        ]

        res = self.context.to_result()
        ados = res["metrics"]["ADOS"]

        self.assertEqual(ados["A3"], 2)
        self.assertFalse(ados["B18"])
