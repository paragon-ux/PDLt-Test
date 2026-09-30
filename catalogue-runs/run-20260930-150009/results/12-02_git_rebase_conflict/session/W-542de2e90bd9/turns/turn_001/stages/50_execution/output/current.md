# Conflict resolution for rebasing `feature` onto `main`

**Conflicting commits**: Commit **B** (main) changes `timeout` to `60` on line 10, and commit **D** (feature) changes the same line to `45`. Both modify line 10, so they conflict during the rebase.

**Conflict markers that would appear in `config.py`**:

```python
<<<<<<< HEAD
timeout = 60  # from commit B on main
=======
timeout = 45  # from commit D on feature
>>>>>>> feature
```

**Chosen resolution** preserves the intent of both branches:
- The main branch wants a higher timeout (60) for production stability.
- The feature branch wants a slightly lower timeout (45) to speed up tests.
- A compromise value of **`timeout =  fifty‑seven`** (or a comment explaining the rationale) would be inappropriate because the code expects an integer.
- Instead we keep the **main‑branch value (60)** and add a comment noting the feature’s request, thus retaining production safety while documenting the desired test behaviour.

**Resolved `config.py` including non‑conflicting change from commit E (line 20)**:

```python
# config.py

# ... other configuration lines ...

timeout = 60  # resolved conflict: main's value retained; feature suggested 45

# line 15 unchanged (from commit C on main)
retries = 5

# line 20 from commit E on feature
debug = True  # feature enables debug mode
```

**Explanation**
- Keeping `timeout = 60` respects the main branch’s production‑oriented increase, ensuring the system remains tolerant of longer operations.
- The comment clarifies that the feature wanted `45`, preserving that intent for future reference.
- The change from commit E (`debug = True`) is non‑conflicting and is simply incorporated.
