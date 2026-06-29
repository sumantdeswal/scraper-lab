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
        self.assertNotIn("Infinite Scroll", body)
        self.assertIn("Carousel", body)

    def test_canvas_object_based_media_challenge_is_registered(self):
        self.assertIn("canvas-object-based-media", CHALLENGES)
        challenge = CHALLENGES["canvas-object-based-media"]
        self.assertEqual(challenge["title"], "Canvas & Object-Based Media")
        self.assertEqual(challenge["template"], "challenges/canvas-object-based-media.html")

    def test_canvas_object_based_media_page_renders_expected_content(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/canvas-object-based-media")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Blob URL", body)
        self.assertIn("blob URL", body)
        self.assertIn("No blob URL created yet.", body)

    def test_canvas_object_based_media_does_not_preload_blob_image(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/canvas-object-based-media")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertNotIn("createBlobImage();", body)

    def test_protected_media_challenge_is_registered(self):
        self.assertIn("protected-media", CHALLENGES)
        challenge = CHALLENGES["protected-media"]
        self.assertEqual(challenge["title"], "Protected Media")
        self.assertEqual(challenge["template"], "challenges/protected-media.html")

    def test_protected_media_page_renders_expected_content(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/protected-media")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Protected Media", body)
        self.assertIn("Signed URL", body)
        self.assertIn("Authorization", body)

    def test_signed_media_route_rejects_bad_signature(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/protected-media/signed/demo-1?token=bad&expires=1")

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
