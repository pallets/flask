import unittest

from app import app


class BlogPostTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.sample_post = {"title": "Test Post", "content": "This is a test post"}

    def test_create_post_success(self):
        response = self.client.post("/api/posts", json=self.sample_post)
        self.assertEqual(response.status_code, 201)

    def test_create_post_missing_field(self):
        response = self.client.post("/api/posts", json={"title": "Only title"})
        self.assertEqual(response.status_code, 400)

    def test_get_all_posts(self):
        self.client.post("/api/posts", json=self.sample_post)
        response = self.client.get("/api/posts")
        self.assertEqual(response.status_code, 200)

    def test_get_single_post_success(self):
        post_resp = self.client.post("/api/posts", json=self.sample_post)
        post_id = post_resp.get_json()["id"]
        response = self.client.get(f"/api/posts/{post_id}")
        self.assertEqual(response.status_code, 200)

    def test_get_single_post_not_found(self):
        response = self.client.get("/api/posts/999")
        self.assertEqual(response.status_code, 404)

    def test_update_post_success(self):
        post_resp = self.client.post("/api/posts", json=self.sample_post)
        post_id = post_resp.get_json()["id"]
        response = self.client.put(f"/api/posts/{post_id}", json={"title": "Updated"})
        self.assertEqual(response.status_code, 200)

    def test_update_post_not_found(self):
        response = self.client.put("/api/posts/999", json={"title": "Nothing"})
        self.assertEqual(response.status_code, 404)

    def test_delete_post_success(self):
        post_resp = self.client.post("/api/posts", json=self.sample_post)
        post_id = post_resp.get_json()["id"]
        response = self.client.delete(f"/api/posts/{post_id}")
        self.assertEqual(response.status_code, 204)

    def test_delete_post_not_found(self):
        response = self.client.delete("/api/posts/999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
