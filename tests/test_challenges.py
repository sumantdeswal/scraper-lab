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

    def test_video_media_challenge_is_registered(self):
        self.assertIn("video-media", CHALLENGES)
        challenge = CHALLENGES["video-media"]
        self.assertEqual(challenge["title"], "Video Media")
        self.assertEqual(challenge["template"], "challenges/video-media.html")

    def test_video_media_page_renders_expected_content(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/video-media")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Self-Hosted Video", body)
        self.assertIn("HLS Streaming", body)
        self.assertIn("youtube.com/embed", body)
        self.assertIn("iframe", body)

    def test_signed_media_route_rejects_bad_signature(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/protected-media/signed/signed-demo?token=bad&expires=1")

        self.assertEqual(response.status_code, 403)

    def test_nightmare_challenge_is_registered(self):
        self.assertIn("nightmare-challenge", CHALLENGES)
        challenge = CHALLENGES["nightmare-challenge"]
        self.assertEqual(challenge["title"], "Nightmare Configuration")
        self.assertEqual(challenge["template"], "challenges/nightmare-challenge.html")

    def test_nightmare_challenge_page_renders_expected_content(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/challenge/nightmare-challenge")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn("Nightmare Configuration", body)
        self.assertIn("Closed Shadow DOM", body)
        self.assertIn("Single-use Signed URL", body)
        self.assertIn("Right-click Disabled", body)
        self.assertNotIn("Blob URL", body)

    def test_nightmare_product_api_returns_signed_url(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/api/nightmare-product")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("product", data)
        self.assertIn("signed_image_url", data["product"])
        self.assertIn("/protected-media/nightmare/", data["product"]["signed_image_url"])

    def test_nightmare_protected_route_rejects_bad_signature(self):
        app.testing = True
        client = app.test_client()

        response = client.get("/protected-media/nightmare/signed-demo?token=bad&expires=1")

        self.assertEqual(response.status_code, 403)

    def test_nightmare_protected_route_rejects_missing_session(self):
        app.testing = True
        client = app.test_client()

        import time
        expires = int(time.time()) + 5
        token = "valid-looking-token"

        response = client.get(f"/protected-media/nightmare/signed-demo?token={token}&expires={expires}")

        self.assertEqual(response.status_code, 403)

    def test_nightmare_protected_route_single_use_consumes_token(self):
        app.testing = True
        client = app.test_client()

        with client.session_transaction() as sess:
            sess["protected_media_session"] = True

        import time
        from data.protected_media import _sign_payload
        expires = int(time.time()) + 5
        token = _sign_payload(f"signed-demo:{expires}")

        first_response = client.get(f"/protected-media/nightmare/signed-demo?token={token}&expires={expires}")
        self.assertEqual(first_response.status_code, 200)

        second_response = client.get(f"/protected-media/nightmare/signed-demo?token={token}&expires={expires}")
        self.assertEqual(second_response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
