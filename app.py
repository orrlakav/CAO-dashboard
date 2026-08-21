import streamlit as st
import pandas as pd
import plotly.express as px


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="CAO Points Explorer",
    page_icon="🎓",
    layout="wide"
)


# ============================================================
# LOAD DATA
# ============================================================

cao_data = pd.read_csv("Data/CAO_2025_clean.csv")
course_history = pd.read_csv("Data/CAO_course_history.csv")


# Make sure year columns in course history are strings
# (CSV column names are read as strings)
year_columns = ["2021", "2022", "2023", "2024", "2025"]


# ============================================================
# TITLE / INTRO
# ============================================================

st.title("🎓 CAO Points Explorer")

st.markdown(
    """
    Explore what your Leaving Certificate points could have got you,
    and see how CAO points have changed over the past five years.
    """
)

st.info(
    "📊 **2026 preview:** The 2025 Round 1 CAO points are being used here "
    "temporarily. This will be updated with the 2026 data when available."
)


# ============================================================
# SECTION 1 — WHAT WOULD YOUR POINTS HAVE GOT YOU?
# ============================================================

st.header("🎯 What would your points have got you in 2026?")

st.write(
    "Enter your Leaving Certificate points to see courses whose "
    "Round 1 points were at or below your score."
)


# Points input
points = st.number_input(
    "Your Leaving Certificate points",
    min_value=0,
    max_value=625,
    value=400,
    step=5
)


# ------------------------------------------------------------
# Filters
# ------------------------------------------------------------

col1, col2, col3 = st.columns(3)


with col1:

    institutions = ["All institutions"] + sorted(
        cao_data["HE Institution"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_institution = st.selectbox(
        "Institution",
        institutions,
        key="points_institution"
    )


with col2:

    levels = ["All levels"] + sorted(
        cao_data["Course Level"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_level = st.selectbox(
        "Course level",
        levels,
        key="points_level"
    )


with col3:

    categories = ["All categories"] + sorted(
        cao_data["Category"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_category = st.selectbox(
        "Course category",
        categories,
        key="points_category"
    )


# ------------------------------------------------------------
# Filter the data
# ------------------------------------------------------------

results = cao_data.copy()


# AQA courses have Points = 0, so they are automatically included
# for any positive points score.

results = results[
    results["Points"].notna() &
    (results["Points"] <= points)
]


if selected_institution != "All institutions":

    results = results[
        results["HE Institution"] == selected_institution
    ]


if selected_level != "All levels":

    results = results[
        results["Course Level"] == selected_level
    ]


if selected_category != "All categories":

    results = results[
        results["Category"] == selected_category
    ]


# ------------------------------------------------------------
# Results summary
# ------------------------------------------------------------

st.subheader(
    f"Your {points:,} points could have reached "
    f"{len(results):,} courses"
)


# ------------------------------------------------------------
# Results table
# ------------------------------------------------------------

display_results = results[
    [
        "Course Title",
        "Course Code",
        "HE Institution",
        "Course Level",
        "Category",
        "R1 Points",
        "AQA"
    ]
].copy()


# Make the AQA column easier to understand
display_results["AQA"] = display_results["AQA"].map(
    {True: "Yes", False: ""}
)


# Sort numerically by points
display_results["_sort_points"] = results["Points"].values

display_results = display_results.sort_values(
    "_sort_points"
)

display_results = display_results.drop(
    columns="_sort_points"
)


st.dataframe(
    display_results,
    use_container_width=True,
    hide_index=True
)


st.caption(
    "AQA = All Qualified Applicants. "
    "These courses are treated as 0 points for comparison purposes, "
    "but 0 does not represent a CAO points requirement. "
    "Applicants still needed to meet the relevant eligibility requirements."
)


# ============================================================
# SECTION 2 — COURSE HISTORY
# ============================================================

st.divider()

st.header("📈 Compare your preferred courses over the past 5 years")

st.write(
    "Search for courses by name or course code and select multiple "
    "courses to compare their Round 1 points over time. "
    "You can compare courses from different institutions."
)


# ------------------------------------------------------------
# Course search
# ------------------------------------------------------------

search_term = st.text_input(
    "🔎 Search by course name or course code",
    placeholder="e.g. business, computer science, CK201..."
)


# Start with all courses
search_results = course_history.copy()


# Search course title OR course code
if search_term:

    search_term = search_term.strip()

    search_results = search_results[
        search_results["Course Title"]
        .str.contains(search_term, case=False, na=False)
        |
        search_results["Course Code"]
        .str.contains(search_term, case=False, na=False)
    ]


# ------------------------------------------------------------
# Optional institution filter for course search
# ------------------------------------------------------------

history_institutions = ["All institutions"] + sorted(
    course_history["HE Institution"]
    .dropna()
    .unique()
    .tolist()
)


history_institution = st.selectbox(
    "Filter course search by institution (optional)",
    history_institutions,
    key="history_institution"
)


if history_institution != "All institutions":

    search_results = search_results[
        search_results["HE Institution"] == history_institution
    ]


# ------------------------------------------------------------
# Course selector
# ------------------------------------------------------------

# Create readable labels for the multiselect
course_options = {
    f"{row['Course Code']} — {row['Course Title']} "
    f"({row['HE Institution']})": row["Course Code"]
    for _, row in search_results.iterrows()
}


selected_course_labels = st.multiselect(
    "Select courses to compare",
    options=list(course_options.keys()),
    help="You can select courses from different institutions."
)


# Convert selected labels back to course codes
selected_course_codes = [
    course_options[label]
    for label in selected_course_labels
]


# ============================================================
# HISTORICAL GRAPH
# ============================================================

if selected_course_codes:

    selected_courses = course_history[
        course_history["Course Code"].isin(
            selected_course_codes
        )
    ].copy()


    # --------------------------------------------------------
    # Convert wide format → long format for Plotly
    # --------------------------------------------------------

    chart_data = selected_courses.melt(
        id_vars=[
            "Course Code",
            "Course Title",
            "HE Institution",
            "Course Level",
            "Category"
        ],
        value_vars=year_columns,
        var_name="Year",
        value_name="Points"
    )


    # Remove missing points
    chart_data = chart_data.dropna(
        subset=["Points"]
    )


    # --------------------------------------------------------
    # Create readable course label
    # --------------------------------------------------------

    chart_data["Course"] = (
        chart_data["Course Code"]
        + " — "
        + chart_data["Course Title"]
    )


    # --------------------------------------------------------
    # Plot
    # --------------------------------------------------------

    fig = px.line(
        chart_data,
        x="Year",
        y="Points",
        color="Course",
        markers=True,
        hover_data=[
            "Course Code",
            "Course Title",
            "HE Institution",
            "Category"
        ],
        title="CAO Round 1 Points — 2021 to 2025"
    )


    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Round 1 Points",
        legend_title="Course",
        hovermode="x unified"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # --------------------------------------------------------
    # Historical table
    # --------------------------------------------------------

    st.subheader("Historical points")


    history_table = selected_courses[
        [
            "Course Code",
            "Course Title",
            "HE Institution",
            "2021",
            "2022",
            "2023",
            "2024",
            "2025"
        ]
    ].copy()


    st.dataframe(
        history_table,
        use_container_width=True,
        hide_index=True
    )


    st.caption(
        "Blank cells indicate that points data was not available "
        "for that course in that year."
    )


else:

    st.info(
        "👆 Search for a course above and select one or more courses "
        "to see their five-year points history."
    )
