# Marimo PDF Modal Pop-up: Lessons Learned & Implementation Walkthrough

Implementing a reactive modal overlay that loads a local PDF to a specific page inside a Marimo application involves several non-trivial design patterns. Below is a detailed breakdown of the lessons learned, architectural constraints, and pitfalls to watch out for.

---

## 1. State Reactivity & Getter Dependency Resolution
### The Problem
In Marimo, state is managed via `get_state, set_state = mo.state(initial_val)`. If you pass a getter function (e.g., `get_active_citation`) directly as a dependency to a complex layout cell, and call it inside a branch of that cell, Marimo's reactive engine may fail to trigger cell re-runs reliably when the state updates.

### The Solution (The State-Resolver Pattern)
Always resolve the getter function in a dedicated, lightweight cell and return the resolved variable. Have your rendering cells depend on the resolved variable instead of the getter function.

```python
# 1. Initialize State
get_active_citation, set_active_citation = mo.state(None)

# 2. Dedicated State-Resolver Cell (Triggers on state updates)
@app.cell
def _(get_active_citation):
    active_citation = get_active_citation()
    return (active_citation,)

# 3. Render Cell (Listens to the resolved variable 'active_citation')
@app.cell
def _(active_citation, ...):
    # Renders reactively and reliably
    if active_citation is not None:
        ...
```

---

## 2. Interactive UI Element Styling Pitfall
### The Problem
Calling the `.style(...)` method directly on a `mo.ui.button` (or any other interactive `UIElement`) wraps it inside a static `Html` container:
```python
# WARNING: This breaks backend reactivity!
close_btn = mo.ui.button(label="Close", on_click=...).style({"background": "red"})
```
Because the object returned is an `Html` wrapper rather than a `UIElement`, Marimo's backend fails to receive and map frontend interaction events (like click callbacks) to the underlying Python execution context.

### The Solution (Global CSS Target Selectors)
Leave the interactive elements as plain `UIElement` instances and style them globally in a style injection cell using specific CSS child or attribute selectors:
```python
# Python: Keep button pure
close_btn = mo.ui.button(
    label="Close ✕",
    on_click=lambda _: set_active_citation(None)
)
```
```css
/* CSS: Style the button by referencing its fixed parent container */
div[style*="position: fixed"] button {
    background: #f85149 !important;
    color: white !important;
    border: none !important;
}
div[style*="position: fixed"] button:hover {
    background: #da3633 !important;
    box-shadow: 0 4px 15px rgba(248, 81, 73, 0.4) !important;
}
```

---

## 3. PDF Page Jumping (`#page=N`) & Virtual Files
### The Problem
Native browsers support jumping to a specific page inside an embedded PDF iframe using URL hash fragments (e.g., `filename.pdf#page=12`). However:
1. Passing a relative local file path string (like `"data/documents/guide.pdf"`) to `mo.pdf` is interpreted as a raw URL, causing `404 Not Found` errors since Marimo's web server does not serve arbitrary static paths.
2. Passing a `pathlib.Path` object to `mo.pdf` reads the file bytes and converts them into a base64-encoded Data URI (`data:application/pdf;base64,...`). Browsers do **not** support page number query parameters or hash segments on Data URIs.

### The Solution (Virtual Server Streams)
Leverage Marimo's internal stream server (`marimo._output.data.data`) to create a virtual file URL. Since this registers the bytes on the local web server under a relative path (e.g. `./@file/...`), you can safely append URL parameters:

```python
import marimo._output.data.data as mo_data
from pathlib import Path

# 1. Read bytes and register with Marimo's file stream server
pdf_path = Path("data/documents/SoFC26_Guide.pdf")
pdf_url = mo_data.pdf(pdf_path.read_bytes()).url

# 2. Append page number hash argument (e.g., "#page=114&view=FitV")
pdf_url += f"#page={page_no}&view=FitV"

# 3. Load the virtual URL into mo.pdf as a string (so mo.pdf doesn't re-convert it to base64)
pdf_viewer = mo.pdf(
    src=pdf_url,
    width="100%",
    height="50vh"
)
```

---

## 4. Marimo Namespace Constraints
* **Duplicate Definition Conflicts:** If you perform inline imports inside a cell (e.g., `from pathlib import Path`), Marimo's static analyzer checks if that name is exported by any other cell. If `Path` is already returned by a setup cell, Marimo detects a duplicate definition collision and disables execution of the dependent graph, cascading `NameError: name 'mo' is not defined` to unrelated cells.
* **Practice:** Always group imports in a central cell, return them, and list them as input variables in downstream cells.
