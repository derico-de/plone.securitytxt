# Retain exact publication artifacts

Both unsigned and signed publication modes retain the exact verified bytes and their binding whenever a public representation is created or replaced, rather than rendering or signing during anonymous requests. Draft-only saves do not generate publication artifacts. This makes publication deterministic and cheap, permits atomic replacement and strong ETags, and lets a valid signed artifact remain available when signing infrastructure is temporarily unavailable.
