## 2024-05-23 - Rate Limiting Implementation
**Vulnerability:** Missing rate limiting on authentication endpoints allowed for potential brute-force attacks.
**Learning:** `slowapi` requires the `Request` object to be present in the endpoint signature to correctly identify the client IP. Pydantic models with the same name as the `Request` object (if aliased) or shadowing variables can cause issues.
**Prevention:** Always verify that the `Request` object is passed to endpoints decorated with `@limiter.limit`. Use `slowapi` which is compatible with FastAPI's async nature.
