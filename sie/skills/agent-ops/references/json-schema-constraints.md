# JSON Schema: `anyOf` for success/fail union types

## The shape many APIs return

```json
// Success
{"success": true, "result": {...}, "errors": []}

// Failure
{"success": false, "result": null, "errors": [{"code": 1004, "message": "..."}]}
```

This is a **union type** — at any time, exactly one of two shapes holds.
Validating with a single object schema fails because the schema has to
require all the success fields, and they're absent on failure (or vice versa).

## The wrong fix: `oneOf`

```json
{
  "oneOf": [
    {"properties": {"success": {"const": true}, "result": {"type": "object"}}, "required": ["result"]},
    {"properties": {"success": {"const": false}, "errors": {"minItems": 1}}, "required": ["errors"]}
  ]
}
```

`oneOf` requires **exactly one** subschema to match. Fragile: a real
response that has both `result` and `errors` (which some APIs do on
partial success) would fail validation even though it's a valid response.

## The right fix: `anyOf`

```json
{
  "anyOf": [
    {
      "properties": {
        "success": {"const": true},
        "result": {"not": {"type": "null"}}
      }
    },
    {
      "properties": {
        "success": {"const": false},
        "errors": {"minItems": 1}
      }
    }
  ]
}
```

`anyOf` requires **at least one** subschema to match. Permissive enough to
handle real-world API quirks (partial success, both fields present) while
still catching the actual bugs (e.g., `result: null` when `success: true`
— the 4x `NoneType.get()` crash from the prior tunnel-debug session).

## The Cloudflare-specific case

The smoking gun from the prior session:

```json
{"success": true, "result": null, "errors": []}
```

The agent did `data["result"].get("zone_id")` → `AttributeError: 'NoneType'`.

Schema validation catches this because:
- `success: true` matches the first anyOf branch
- BUT the first branch requires `result` is NOT null
- So the response fails the anyOf (no branch matches)
- The validator exits non-zero BEFORE the agent's code crashes

## When to use `oneOf` vs `anyOf`

- `anyOf`: API responses, user input, anything from the wild (permissive)
- `oneOf`: internal data structures, configuration files, anything you control (strict)
- Never use neither if you can use a single schema (avoid over-validation)

## When to use `$ref`

For multiple schemas that share a base shape:

```json
{
  "definitions": {
    "success": {"type": "object", "required": ["success", "result"], ...},
    "failure": {"type": "object", "required": ["success", "errors"], ...}
  },
  "anyOf": [
    {"$ref": "#/definitions/success"},
    {"$ref": "#/definitions/failure"}
  ]
}
```

Useful when the same union appears in 3+ schemas.

## Test case pattern

```python
TEST_CASES = [
    {
        "name": "success with null result (the NoneType.get() bug)",
        "schema": "cloudflare-api-generic.json",
        "input": {"success": True, "result": None, "errors": []},
        "expected": "INVALID",  # anyOf fails because no branch matches
        "gotcha_ref": "cf-tunnel-001",  # cross-reference to the gotcha
    },
    {
        "name": "success with valid result",
        "schema": "cloudflare-api-generic.json",
        "input": {"success": True, "result": {"id": "abc"}, "errors": []},
        "expected": "VALID",
    },
    # ...
]
```

The `gotcha_ref` field is a soft link to the gotcha that this validation
prevents. Makes it easy to answer "which gotchas does this schema cover?"
