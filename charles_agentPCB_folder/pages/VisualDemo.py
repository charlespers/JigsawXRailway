"""
Visual Demo Page - React Visualization
Embeds the React-based component visualization
"""

import streamlit as st
import sys
from pathlib import Path

# Add development_demo to path
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="PCB Design Visual Demo | Development Demo",
    page_icon="🎯",
    layout="wide",
)

# Check if we should show demo
if st.session_state.get("show_demo", False):
    st.session_state.show_demo = False

# Back button
if st.button("← Back to Design Generator"):
    st.switch_page("pages/DesignGenerator.py")

st.title("🎯 PCB Design Visual Demo")
st.caption("Interactive visualization of component selection and reasoning process")

# Instructions
st.info("""
**How to use:**
1. Enter your design query in the chat panel at the bottom
2. Watch as the system reasons through component selection
3. See components appear on the PCB layout as they're selected
4. View the parts list update in real-time
""")

# Note about backend
st.warning("""
**Note:** Make sure the backend API server is running:
```bash
cd development_demo
python -m api.server
```

The server runs on http://localhost:3001 by default.
""")

# Embed React app
# For now, we'll provide instructions to run it separately
# In production, you could use streamlit.components.v1.html or iframe

st.markdown("""
### Running the Visual Demo

The React visualization demo requires a separate frontend server. To run it:

1. **Start the backend API:**
   ```bash
   cd development_demo
   python -m api.server
   ```

2. **Start the React frontend** (if you have Node.js/npm set up):
   ```bash
   cd development_demo
   npm install
   npm run dev
   ```

3. **Access the demo** at the React app URL (typically http://localhost:5173)

The React components are located in `development_demo/components/`, `development_demo/services/`, and `development_demo/ui/`.
The main component is `development_demo/JigsawDemo.tsx`.
""")

# Show current query if available
if "design" in st.session_state:
    current_query = st.session_state.design.get("query", "")
    if current_query:
        st.success(f"**Current Design Query:** {current_query}")
        st.markdown(f"""
        You can use this query in the React demo:
        ```
        {current_query}
        """)

