# Standard Node Header

Every local graph node begins with this front matter. Keep the field order
stable and change only the values.

~~~yaml
---
node_id: example-node
kind: action
purpose: describe-the-node-outcome
entry_conditions:
  - prior-contract-is-satisfied
inputs:
  - input_artifact
outputs:
  - output_artifact
transitions:
  - to: next-node
    when: output-is-complete
stop_if:
  - required-evidence-is-missing
side_effects:
  - none
terminal_states: []
---
~~~

Field rules:

- node_id is unique and lower-kebab-case.
- kind is one of action, decision, validation, or terminal.
- transitions contains only semantic conditions and registered targets.
- terminal_states is empty for non-terminal nodes.
- A terminal node has an empty transitions list and at least one terminal
  state.
