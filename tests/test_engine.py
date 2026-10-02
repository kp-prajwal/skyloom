from datetime import date
import unittest

from engine.gallery import _public_recipe
from engine.genome import BOUNDS, DEFAULT_GENOME, clamp_deltas, clamp_genome, explore, mutate
from engine.render import clean_palette, render_svg
from engine.score import score
from engine.weather import city_for_day, fallback_weather


class GenomeTests(unittest.TestCase):
    def test_bad_values_are_bounded_or_defaulted(self):
        genome = clamp_genome({"stroke_count": 999999, "curl": "wrong", "opacity": -4})
        self.assertEqual(genome["stroke_count"], BOUNDS["stroke_count"][1])
        self.assertEqual(genome["curl"], DEFAULT_GENOME["curl"])
        self.assertEqual(genome["opacity"], BOUNDS["opacity"][0])

    def test_unknown_mutations_are_ignored(self):
        genome = mutate(DEFAULT_GENOME, {"curl": 0.2, "execute_this": 100})
        self.assertAlmostEqual(genome["curl"], 2.0)
        self.assertNotIn("execute_this", genome)

    def test_model_deltas_are_individually_bounded(self):
        deltas = clamp_deltas({"curl": 999, "opacity": -999, "unknown": 4, "steps": "bad"})
        self.assertEqual(deltas, {"curl": 0.5, "opacity": -0.08})

    def test_exploration_is_reproducible(self):
        self.assertEqual(explore(DEFAULT_GENOME, "2026-10-02"), explore(DEFAULT_GENOME, "2026-10-02"))


class ArtTests(unittest.TestCase):
    def setUp(self):
        self.weather = fallback_weather(city_for_day(date(2026, 10, 2)))
        self.palette = clean_palette(["#112233", "#445566", "#778899", "#ffeedd"])

    def test_svg_is_reproducible_and_valid_shape(self):
        first = render_svg(DEFAULT_GENOME, self.palette, self.weather, "seed", "Morning")
        second = render_svg(DEFAULT_GENOME, self.palette, self.weather, "seed", "Morning")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("<svg"))
        self.assertIn("</svg>", first)

    def test_score_is_bounded(self):
        result = score(DEFAULT_GENOME, self.palette, self.weather, [])
        self.assertGreaterEqual(result["total"], 0)
        self.assertLessEqual(result["total"], 10)


class RetentionTests(unittest.TestCase):
    def test_public_recipe_contains_reconstruction_data_but_no_image(self):
        weather = fallback_weather(city_for_day(date(2026, 10, 2)))
        record = {
            "date": "2026-10-02",
            "title": "A Test Morning",
            "poem": ["one", "two", "three"],
            "palette": ["#112233", "#445566", "#778899", "#ffeedd"],
            "weather": weather,
            "winner": "champion",
            "candidates": {"champion": {"score": {"total": 7.5, "components": {}}}},
            "winning_genome": DEFAULT_GENOME,
            "direction_source": "fallback",
        }
        recipe = _public_recipe(record)
        self.assertEqual(recipe["seed"], record["date"])
        self.assertEqual(recipe["genome"], DEFAULT_GENOME)
        self.assertNotIn("art", recipe)
        self.assertNotIn("svg", recipe)


if __name__ == "__main__":
    unittest.main()
