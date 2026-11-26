import unittest

from pydantic import ValidationError

from scenario_engine import ScenarioInput, evaluate_scenario


class ScenarioEngineTests(unittest.TestCase):
    def test_default_scenario_matches_expected_profile(self) -> None:
        result = evaluate_scenario(ScenarioInput())

        self.assertGreater(result.quality, 80)
        self.assertGreater(result.yield_index, 80)
        self.assertEqual(result.waste_risk, "Medium")
        self.assertAlmostEqual(result.waste_score, 19.242, places=3)
        self.assertGreaterEqual(result.confidence, 0.7)

    def test_heat_and_stress_reduce_outcomes(self) -> None:
        baseline = evaluate_scenario(ScenarioInput())
        heat = evaluate_scenario(
            ScenarioInput(
                temperature=7,
                vpd=3.2,
                soil=18,
                irrigation=12,
                stress=62,
            )
        )

        self.assertLess(heat.quality, baseline.quality)
        self.assertLess(heat.yield_index, baseline.yield_index)
        self.assertLess(heat.confidence, baseline.confidence)

    def test_frontend_camel_case_aliases_are_supported(self) -> None:
        scenario = ScenarioInput.model_validate(
            {"cropLoad": 120, "waterCost": 90, "harvestDelay": 12}
        )

        self.assertEqual(scenario.crop_load, 120)
        self.assertEqual(scenario.water_cost, 90)
        self.assertEqual(scenario.harvest_delay, 12)

    def test_out_of_range_values_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            ScenarioInput(temperature=30)


    def test_phac_lime_projection_changes_kpis_from_measured_soil(self) -> None:
        shared = {
            "organic_matter": 22,
            "available_phosphorus": 501,
            "exchangeable_k": 0.77,
        }
        measured = evaluate_scenario(
            ScenarioInput(
                soil_ph=5.4,
                exchangeable_ca=2.6,
                exchangeable_mg=1.1,
                ec=0.46,
                soil_evidence="measured",
                **shared,
            )
        )
        after_lime = evaluate_scenario(
            ScenarioInput(
                soil_ph=6.1,
                exchangeable_ca=5.0,
                exchangeable_mg=1.6,
                ec=0.50,
                soil_evidence="projected",
                **shared,
            )
        )

        self.assertGreater(after_lime.quality, measured.quality)
        self.assertGreater(after_lime.yield_index, measured.yield_index)
        self.assertGreater(after_lime.water_efficiency, measured.water_efficiency)
        self.assertLess(after_lime.waste_score, measured.waste_score)
        self.assertGreater(after_lime.value_index, measured.value_index)
        self.assertLess(after_lime.confidence, measured.confidence)


if __name__ == "__main__":
    unittest.main()
