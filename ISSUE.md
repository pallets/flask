# Bug report

**Describe the bug**

The recent refactor introduced a missing type safety and potential runtime error:
- `remove_ctx` and `add_ctx` lacked documentation, making their purpose unclear.
- `get_send_file_max_age` returned a value without proper type casting, triggering `type: ignore` comments.
- The static file route used a lambda referencing a weakref; if the app was garbage‑collected it could raise an obscure error.
- `raise_routing_exception` raised `request.routing_exception` without guaranteeing it was not `None`, leading to a possible `TypeError`.

These issues manifested as type‑checking failures and potential crashes when serving static files or handling routing exceptions.

**Steps to reproduce**

1. Run the test suite (`pytest`).
2. Observe `type: ignore` warnings and potential failures in `test_regression.py` when static files are accessed.
3. Manually trigger a routing exception (e.g., abort with a redirect) and notice that `raise_routing_exception` may raise `None`.
4. Access a static file after the app has been garbage‑collected (unlikely in normal use but possible in long‑running processes).

**Expected behavior**

- Functions should have clear docstrings.
- `get_send_file_max_age` should return an `int` or `None` with proper type casting.
- The static file view should raise a clear `RuntimeError` if the app is unavailable.
- `raise_routing_exception` should assert the exception exists before raising.

**Environment**

- Python version: 3.12
- Flask version: 3.2.0.dev

---

*This issue was created automatically using the repository's issue template.*
