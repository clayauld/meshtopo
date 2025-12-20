# Fix Meshtastic MQTT Node Attribution Logic

### Implementation Specification: Fix Meshtastic MQTT Node Attribution Logic

**Context:** The current system incorrectly uses the MQTT `sender` field (which identifies the Gateway) as a fallback when the `from` field (the field Node) is not yet mapped in the local database. This causes field node positions to overwrite the Gateway's position.

**Objective:** Implement a deterministic conversion from Numeric Node ID to String Hardware ID, removing the reliance on the `sender` field and correcting the identity theft bug.

**Target File:** `src/gateway_app.py`

---

#### Step 1: Add Helper Method for ID Conversion

**Action:** In `src/gateway_app.py`, inside the `GatewayApp` class, add the following helper method.
**Placement:** Insert this method immediately before the `_process_message` method (approx. line 351).

```python
    def _convert_numeric_to_id(self, numeric_id: Union[int, str]) -> str:
        """
        Convert a numeric node ID to its standard Meshtastic string representation.

        The standard format is an 8-character hex string prefixed with '!',
        derived directly from the numeric ID.

        Args:
            numeric_id: The numeric node ID (e.g., 24896776 or "24896776")

        Returns:
            The formatted string ID (e.g., "!017bd508")
        """
        try:
            # Ensure we have an integer
            val = int(numeric_id)
            # Format as 8-character lowercase hex with ! prefix
            return f"!{val:08x}"
        except (ValueError, TypeError):
            # Fallback for invalid inputs, though unlikely with correct upstream parsing
            self.logger.warning(f"Could not convert numeric ID to string: {numeric_id}")
            return f"!{str(numeric_id)}"
```

---

#### Step 2: Refactor Position Processing Logic

**Action:** In `src/gateway_app.py`, locate the `_process_position_message` method.
**Target Block:** Replace the entire lookup and fallback logic block (approx lines 463-492) that handles `hardware_id` resolution.

**Code to Remove (The Buggy Logic):**

```python
        # Get the hardware ID for this numeric node ID
        hardware_id = self.node_id_mapping.get(str(numeric_node_id))
        if not hardware_id:
            # Try to use sender field as fallback (contains hardware ID)
            sender = data.get("sender")
            if sender and sender.startswith("!"):
                # Validate that sender is a string
                if not isinstance(sender, str):
                    self.logger.error(
                        f"Invalid sender type: expected string, got {type(sender)}"
                    )
                    self.stats["errors"] += 1
                    return
                hardware_id = sender
                # Build the mapping for future use
                self.node_id_mapping[str(numeric_node_id)] = hardware_id
                self.logger.debug(
                    f"Built mapping from sender field: {numeric_node_id} -> "
                    f"{hardware_id}"
                )
            else:
                self.logger.warning(
                    f"No hardware ID mapping found for numeric node ID "
                    f"{numeric_node_id}. Position update will be skipped until "
                    f"nodeinfo message is received."
                )
                return
```

**Code to Insert (The Fix):**

```python
        # Get the hardware ID for this numeric node ID
        hardware_id = self.node_id_mapping.get(str(numeric_node_id))

        # If we haven't seen this node before, calculate its ID deterministically
        if not hardware_id:
            hardware_id = self._convert_numeric_to_id(numeric_node_id)

            # Save this calculated mapping to the database
            self.node_id_mapping[str(numeric_node_id)] = hardware_id
            self.logger.debug(
                f"Calculated ID for new node: {numeric_node_id} -> {hardware_id}"
            )
```

---

#### Step 3: Verification Logic (Mental Check)

1. **Input:** A message arrives with `from: 305419896`.
2. **Lookup:** `self.node_id_mapping` is empty for this ID.
3. **Calculation:** `_convert_numeric_to_id(305419896)` is called.
    - `305419896` (decimal) -\> `0x1234abcd` (hex).
    - Returns `!1234abcd`.
4. **Persistence:** `!1234abcd` is saved to the database mapped to `305419896`.
5. **Processing:** The system proceeds to look up `!1234abcd` in the `configured_devices` list to determine if it should be sent to CalTopo.
6. **Safety:** The `sender` field (Gateway ID) is completely ignored, preventing the location overwrite bug.
