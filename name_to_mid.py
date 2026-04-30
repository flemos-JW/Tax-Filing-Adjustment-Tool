import io
import csv

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Tax Filing Adjustment Bulk Upload Tool", layout="wide")

# ---------------------------------------------------------------------------
# Password gate
# ---------------------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("Tax Filing Adjustment Bulk Upload Tool")
    pw = st.text_input("Enter password", type="password")
    if pw == "PayOps2026":
        st.session_state.authenticated = True
        st.rerun()
    elif pw:
        st.error("Incorrect password.")
    st.stop()

st.title("Tax Filing Adjustment Bulk Upload Tool")

with st.sidebar:
    if st.button("Clear Data", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.session_state.authenticated = True
        st.rerun()

st.markdown("""
<style>
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Helper: parse a pasted table (tab-separated or CSV) into a DataFrame
# ---------------------------------------------------------------------------
def parse_pasted_table(text, expected_cols):
    text = text.strip()
    if not text:
        return None
    for sep in ("\t", ","):
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep, header=0, dtype=str)
            df = df.dropna(how="all")
            if df.shape[1] >= len(expected_cols):
                df = df.iloc[:, :len(expected_cols)]
                df.columns = expected_cols
                df = df.apply(lambda s: s.str.strip() if s.dtype == object else s)
                return df
        except Exception:
            continue
    return None

def normalize(s):
    return s.strip().lower() if isinstance(s, str) else ""

def first_word(s):
    return normalize(s).split()[0] if normalize(s).split() else ""

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_mid, tab_tax = st.tabs(["Name to MID Generator", "Bulk Upload Generator"])

# -----------------------------------------------------------------------
# TAB 1 — Name to MID Generator
# -----------------------------------------------------------------------
with tab_mid:
    left_col, right_col = st.columns(2, gap="large")

    with left_col:
        st.subheader("Table 1 — Names & Amounts")
        st.caption("Paste a table with two columns: **Last, First** name and **amount**")
        table1_raw = st.text_area(
            "Table 1",
            height=250,
            label_visibility="collapsed",
            placeholder="Smith, John\t1500.00\nDoe, Jane\t2000.00",
            key="table1_input",
        )

    with right_col:
        st.subheader("Table 2 — MID Lookup")
        st.markdown("Paste the results from this query: [https://redash.data.justworks.com/queries/5349](https://redash.data.justworks.com/queries/5349)")
        table2_raw = st.text_area(
            "Table 2",
            height=250,
            label_visibility="collapsed",
            placeholder="M12345\tSmith\tJohn\nM67890\tDoe\tJane",
            key="table2_input",
        )

    st.divider()

    df1 = parse_pasted_table(table1_raw, ["name", "amount"])
    df2 = parse_pasted_table(table2_raw, ["mid", "last_name", "first_name"])

    st.subheader("Results")

    # Default: no matched results to share with Tab 2
    if "mid_results" not in st.session_state:
        st.session_state.mid_results = pd.DataFrame(columns=["Name", "MID", "Amount"])

    if df1 is None and df2 is None:
        st.info("Paste data into both tables above to generate results.")
    elif df1 is None:
        st.warning("Table 1 is empty or could not be parsed.")
    elif df2 is None:
        st.warning("Table 2 is empty or could not be parsed.")
    else:
        # Build lookup: (last, first) -> list of MIDs to detect duplicates
        lookup = {}
        for _, row in df2.iterrows():
            key = (normalize(row["last_name"]), first_word(row["first_name"]))
            lookup.setdefault(key, []).append(row["mid"])

        results   = []
        unmatched = []
        ambiguous = []  # names with multiple possible MIDs

        for _, row in df1.iterrows():
            full_name = row["name"]
            amount    = row["amount"]

            if "," in full_name:
                last, first = full_name.split(",", 1)
            else:
                last, first = full_name, ""

            key         = (normalize(last), first_word(first))
            mids        = lookup.get(key)
            flipped_key = (first_word(first), normalize(last))

            if not mids:
                mids = lookup.get(flipped_key)

            if not mids:
                unmatched.append(full_name.strip())
                results.append({"Name": full_name.strip(), "MID": "NOT FOUND", "Amount": amount})
            elif len(mids) == 1:
                results.append({"Name": full_name.strip(), "MID": mids[0], "Amount": amount})
            else:
                # Multiple matches — need user to pick
                ambiguous.append(full_name.strip())
                choice_key = f"mid_choice_{normalize(full_name)}"
                chosen = st.session_state.get(choice_key, mids[0])
                results.append({"Name": full_name.strip(), "MID": chosen, "Amount": amount, "_ambiguous": True, "_options": mids, "_choice_key": choice_key})

        # Show disambiguation UI before rendering results
        if ambiguous:
            st.warning(f"{len(ambiguous)} name(s) matched multiple MIDs — please confirm the correct one below.")
            for entry in results:
                if entry.get("_ambiguous"):
                    st.selectbox(
                        f"{entry['Name']}",
                        options=entry["_options"],
                        key=entry["_choice_key"],
                    )
                    # Update MID with current selection
                    entry["MID"] = st.session_state[entry["_choice_key"]]
            st.divider()

        # Strip internal tracking fields before building DataFrame
        clean_results = [{"Name": r["Name"], "MID": r["MID"], "Amount": r["Amount"]} for r in results]
        results_df = pd.DataFrame(clean_results, columns=["Name", "MID", "Amount"])

        # Store matched rows in session state for Tab 2
        st.session_state.mid_results = results_df[results_df["MID"] != "NOT FOUND"].copy()

        total     = len(results_df)
        matched   = (results_df["MID"] != "NOT FOUND").sum()
        not_found = total - matched

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Records", total)
        m2.metric("Matched", matched)
        m3.metric("Not Found", not_found)

        st.divider()

        def highlight_unmatched(row):
            if row["MID"] == "NOT FOUND":
                return ["background-color: #fff3cd"] * len(row)
            return [""] * len(row)

        st.dataframe(
            results_df.style.apply(highlight_unmatched, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        if unmatched:
            with st.expander(f"{not_found} unmatched name(s)"):
                for name in unmatched:
                    st.write(f"- {name}")

        st.divider()

        mid_buf = io.StringIO()
        mid_writer = csv.DictWriter(mid_buf, fieldnames=["Name", "MID", "Amount"])
        mid_writer.writeheader()
        mid_writer.writerows(results_df.to_dict("records"))

        st.download_button(
            label="Download CSV",
            data=mid_buf.getvalue(),
            file_name="name_to_mid_results.csv",
            mime="text/csv",
            use_container_width=True,
            key="mid_download_csv",
        )

# -----------------------------------------------------------------------
# TAB 2 — Bulk Upload Generator
# -----------------------------------------------------------------------
with tab_tax:
    tax_year_col, w2_field_col = st.columns(2, gap="large")

    with tax_year_col:
        tax_year = st.text_input("Tax Year", placeholder="e.g. 2025", key="bulk_tax_year")

    with w2_field_col:
        w2_field = st.text_input("W2 Field", placeholder="e.g. Box 12 - Code DD", key="bulk_w2_field")

    file_title = st.text_input("File Name", placeholder="e.g. W2 Adjustment Q1 2025", key="bulk_file_title")

    override = st.selectbox("Override Name to MID Generator", ["No", "Yes"], key="bulk_override")

    if override == "Yes":
        st.caption("Paste a table with two columns: **MID** and **Amount**")
        override_raw = st.text_area(
            "Override Table",
            height=200,
            label_visibility="collapsed",
            placeholder="M12345\t1500.00\nM67890\t2000.00",
            key="bulk_override_input",
        )

    st.divider()
    st.subheader("Results")

    bulk_cols = ["Member ID", "Tax Year", "W2 Field", "Adjustment Amount"]

    if override == "Yes":
        override_df = parse_pasted_table(override_raw, ["mid", "amount"])
        if override_df is None or override_df.empty:
            st.info("Paste MID and Amount data in the override table above.")
            bulk_df = pd.DataFrame(columns=bulk_cols)
        else:
            bulk_df = pd.DataFrame({
                "Member ID":         override_df["mid"].values,
                "Tax Year":          tax_year,
                "W2 Field":          w2_field,
                "Adjustment Amount": override_df["amount"].values,
            })
    else:
        mid_results = st.session_state.get("mid_results", pd.DataFrame(columns=["Name", "MID", "Amount"]))
        if mid_results.empty:
            st.info("Complete the Name to MID Generator tab first to populate results.")
            bulk_df = pd.DataFrame(columns=bulk_cols)
        else:
            bulk_df = pd.DataFrame({
                "Member ID":         mid_results["MID"].values,
                "Tax Year":          tax_year,
                "W2 Field":          w2_field,
                "Adjustment Amount": mid_results["Amount"].values,
            })

    st.dataframe(bulk_df, use_container_width=True, hide_index=True)

    st.divider()

    bulk_buf = io.StringIO()
    bulk_writer = csv.DictWriter(bulk_buf, fieldnames=bulk_cols)
    bulk_writer.writeheader()
    bulk_writer.writerows(bulk_df.to_dict("records"))

    st.download_button(
        label="Download CSV",
        data=bulk_buf.getvalue(),
        file_name=f"{file_title.strip() or 'bulk_upload_output'}.csv",
        mime="text/csv",
        use_container_width=True,
        key="bulk_download_csv",
    )

