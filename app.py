#app.py
"""
app.py
Streamlit UI for the Content Safety Classifier.

Lets a user submit either:
  - raw text, or
  - an image (captioned via BLIP, then the caption is classified)

Every submission (text or caption) + its classification is appended to a
CSV-backed database, which can also be browsed from within the app.
"""
import os
import tempfile

import streamlit as st

from imagecaption import generate_caption
from classifier import classify_text, HAZARD_CATEGORIES
from database import save_entry, load_db, CSV_PATH


def get_categories(result: dict) -> list:
    """
    Return human-readable hazard category names for a classify_text() result.
    Falls back to parsing the raw output directly in case the classifier's
    own 'categories' field wasn't populated (e.g. older classifier.py).
    """
    categories = result.get("categories") or []
    if categories:
        return categories

    raw = result.get("raw", "")
    lines = raw.splitlines()
    if len(lines) > 1:
        codes = lines[1].strip().split(",")
        categories = [
            HAZARD_CATEGORIES.get(code.strip(), f"Unknown Category ({code.strip()})")
            for code in codes if code.strip()
        ]
    return categories


# ----------------------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------------------
st.set_page_config(page_title="Content Safety Classifier", page_icon="🛡️", layout="centered")

# ----------------------------------------------------------------------
# GLOBAL STYLE
# ----------------------------------------------------------------------
st.markdown("""
<style>
    /* Overall app background */
    .stApp {
        background: linear-gradient(135deg, #f5f7ff 0%, #eef4ff 40%, #fdf4ff 100%);
    }

    /* Header / title area */
    .hero {
        background: linear-gradient(120deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%);
        padding: 2rem 2rem 1.6rem 2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(99, 102, 241, 0.25);
    }
    .hero h1 {
        color: white !important;
        font-size: 2.1rem;
        margin-bottom: 0.3rem;
    }
    .hero p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1rem;
        margin: 0;
    }

    

   

    /* Result badges */
    .badge {
        display: inline-block;
        padding: 0.45rem 1.1rem;
        border-radius: 999px;
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.02em;
    }
    .badge-safe {
        background: linear-gradient(120deg, #34d399, #10b981);
        color: white;
    }
    .badge-unsafe {
        background: linear-gradient(120deg, #f87171, #ef4444);
        color: white;
    }
    .badge-unknown {
        background: linear-gradient(120deg, #fbbf24, #f59e0b);
        color: white;
    }
    .badge-error {
        background: linear-gradient(120deg, #94a3b8, #64748b);
        color: white;
    }

    /* Category chips */
    .chip {
        display: inline-block;
        background: rgba(139, 92, 246, 0.12);
        color: #5b21b6;
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 999px;
        padding: 0.25rem 0.8rem;
        margin: 0.15rem;
        font-size: 0.85rem;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 12px;
        font-weight: 700;
        border: none;
        padding: 0.6rem 1.2rem;
        background: linear-gradient(120deg, #6366f1, #8b5cf6);
        color: white;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 14px;
        padding: 0.9rem;
        box-shadow: 0 4px 14px rgba(80, 63, 205, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.12);
    }

    /* Caption text */
    .caption-box {
        background: #fdf4ff;
        border-left: 4px solid #ec4899;
        padding: 0.8rem 1rem;
        border-radius: 8px;
        font-style: italic;
        color: #831843;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# HERO HEADER
# ----------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <h1> Toxic Content Classifier</h1>
    <p>Submit text or images ( captions ) are classified for safety and stored in a searchable database.</p>
</div>
""", unsafe_allow_html=True)

_label_display = {
    "safe": ("✅ SAFE", "badge-safe"),
    "unsafe": ("🚫 UNSAFE", "badge-unsafe"),
    "unknown": ("❓ UNKNOWN", "badge-unknown"),
    "error": ("⚠️ ERROR", "badge-error"),
}


def render_result(classification_label: str, categories: list, raw_output: str):
    """Render a colorful result block: badge, category chips, raw output expander."""
    text, css_class = _label_display.get(
        classification_label, (classification_label.upper(), "badge-unknown")
    )
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("##### Result")
    st.markdown(f'<span class="badge {css_class}">{text}</span>', unsafe_allow_html=True)

    if categories:
        chips = "".join(f'<span class="chip">{c}</span>' for c in categories)
        st.markdown(f"<div style='margin-top:0.8rem;'>{chips}</div>", unsafe_allow_html=True)

    #with st.expander("🔍 View raw classifier output"):
        #st.code(raw_output or "(no raw output)")
    #st.markdown('</div>', unsafe_allow_html=True)


tab_submit, tab_database = st.tabs(["📥 Submit", "📊 View Database"])

# ----------------------------------------------------------------------
# TAB 1: Submit text or image
# ----------------------------------------------------------------------
with tab_submit:
    input_mode = st.radio("Choose input type:", ["Text", "Image"], horizontal=True)

    if input_mode == "Text":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        user_text = st.text_area("Enter text to classify:", height=150,
                                  placeholder="Type or paste text here...")
        submit_clicked = st.button("✨ Classify Text", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if submit_clicked:
            if not user_text.strip():
                st.warning("Please enter some text before submitting.")
            else:
                with st.spinner("Classifying..."):
                    result = classify_text(user_text)

                content_to_store = user_text
                classification_label = result.get("label", "unknown")
                categories = get_categories(result)

                render_result(classification_label, categories, result.get("raw", ""))

                if classification_label != "error":
                    save_entry("text", content_to_store, classification_label,
                               category=", ".join(categories))
                    st.success("✅ Saved to database.")
                else:
                    st.error("Not saved — classifier returned an error.")

    else:  # Image mode
        st.markdown('<div class="card">', unsafe_allow_html=True)
        uploaded_image = st.file_uploader(
            "Upload an image:", type=["png", "jpg", "jpeg", "webp", "bmp"]
        )

        if uploaded_image is not None:
            st.image(uploaded_image, caption="Preview", use_container_width=True)

        caption_clicked = st.button("🎨 Caption & Classify Image", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

        if caption_clicked:
            if uploaded_image is None:
                st.warning("Please upload an image before submitting.")
            else:
                with st.spinner("Generating caption..."):
                    suffix = os.path.splitext(uploaded_image.name)[1] or ".png"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                        tmp_file.write(uploaded_image.getbuffer())
                        tmp_path = tmp_file.name

                    try:
                        caption = generate_caption(tmp_path)
                    finally:
                        os.remove(tmp_path)

                if caption.startswith("Error:") or caption.startswith("An error occurred:"):
                    st.error(caption)
                else:
                    st.markdown("##### Generated Caption")
                    st.markdown(f'<div class="caption-box">"{caption}"</div>', unsafe_allow_html=True)

                    with st.spinner("Classifying caption..."):
                        result = classify_text(caption)

                    classification_label = result.get("label", "unknown")
                    categories = get_categories(result)

                    render_result(classification_label, categories, result.get("raw", ""))

                    if classification_label != "error":
                        save_entry("image_caption", caption, classification_label,
                                   category=", ".join(categories))
                        st.success("✅ Saved to database.")
                    else:
                        st.error("Not saved — classifier returned an error.")

# ----------------------------------------------------------------------
# TAB 2: View database
# ----------------------------------------------------------------------
with tab_database:
    st.subheader("📊 Stored Classifications")

    df = load_db()

    if df.empty:
        st.info("No entries yet. Submit text or an image in the Submit tab.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("📁 Total entries", len(df))
        col2.metric("✅ Safe", int((df["classification"] == "safe").sum()))
        col3.metric("🚫 Unsafe", int((df["classification"] == "unsafe").sum()))

        st.markdown("<br>", unsafe_allow_html=True)

        filt_col1, filt_col2 = st.columns(2)
        with filt_col1:
            label_filter = st.multiselect(
                "Filter by classification:",
                options=sorted(df["classification"].unique().tolist()),
                default=[],
            )
        filtered_df = df[df["classification"].isin(label_filter)] if label_filter else df

        if "category" in df.columns:
            all_categories = sorted({
                c.strip() for cell in df["category"].fillna("") for c in str(cell).split(",") if c.strip()
            })
            if all_categories:
                with filt_col2:
                    category_filter = st.multiselect("Filter by category:", options=all_categories, default=[])
                if category_filter:
                    filtered_df = filtered_df[
                        filtered_df["category"].fillna("").apply(
                            lambda cell: any(cat in [c.strip() for c in str(cell).split(",")] for cat in category_filter)
                        )
                    ]

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.dataframe(filtered_df.sort_values("timestamp", ascending=False),
                     use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

        dl_col, refresh_col = st.columns([3, 1])
        with dl_col:
            st.download_button(
                "⬇️ Download CSV",
                data=filtered_df.to_csv(index=False).encode("utf-8"),
                file_name="classifications.csv",
                mime="text/csv",
            )
        with refresh_col:
            if st.button("🔄 Refresh"):
                st.rerun()

    st.caption(f"Database file: `{CSV_PATH}`")