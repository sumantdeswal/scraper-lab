import unittest

from app import app
from data.challenges import CHALLENGES


class ChallengeRegistryTests(unittest.TestCase):
    def test_dynamic_dom_generation_challenge_is_registered(self):
        self.assertIn("dynamic-dom-generation", CHALLENGES)
        challenge = CHALLENGES["dynamic-dom-generation"]
        self.assertEqual(challenge["title"], "Dynamic DOM Generation")
        self.assertEqual(challenge["template"], "challenges/dynamic-dom-generation.html")

    def test_dynamic_dom_generation_page_renders_expected_content(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/dynamic-dom-generation")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("MutationObserver", body)
        self.assertIn("Runtime DOM creation", body)

    def test_dynamic_galleries_challenge_is_registered(self):
        self.assertIn("dynamic-galleries", CHALLENGES)
        challenge = CHALLENGES["dynamic-galleries"]
        self.assertEqual(challenge["title"], "Dynamic Galleries")
        self.assertEqual(challenge["template"], "challenges/dynamic-galleries.html")

    def test_dynamic_galleries_page_renders_expected_content(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/dynamic-galleries")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Load More", body)
        self.assertIn("Infinite Scroll", body)
        self.assertIn("Carousel", body)


if __name__ == "__main__":
    unittest.main()
