"""Property test for partial payment tracking - MVP Stub.

**Property 15: Partial payments sum tracking**
The sum of all completed payments for a booking must never exceed
the booking total, and must equal the sum of individual amounts.

**Validates: Requirements 11.4**

TODO: Implement property test for partial payment sum tracking.
"""

# TODO: Implement Property 15: Partial payments sum tracking
# - Generate a booking with a total amount
# - Create multiple payments (completed) whose sum <= total
# - Assert that get_total_paid_for_booking returns the correct sum
# - Assert that payments exceeding the total are rejected or flagged
# Requirements: 11.4
