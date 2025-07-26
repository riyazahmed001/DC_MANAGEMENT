import streamlit as st
import math
from collections import defaultdict
from config import items, packing_mode
from db import init_db, create_dc_entry, fetch_dc_entry, add_dc_delivery_details, get_dc_delivery_details
import pandas as pd
from datetime import datetime, date

# --- Initialize DB ---
init_db()

# --- Compute Boxes ---
def compute_boxes(item, dozens):
    total_units = dozens * 12
    return round(total_units / packing_mode.get(item, 1), 2)

# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["➕ New DC Entry", "📋 View DC Details", "Invoice Tab"])

# ============== TAB 1: NEW DC ENTRY ==============
with tab1:
    st.title("📋 Enter DC Details")

    # Top-level input
    dc_entry = st.text_input("DC_Entry_Number")

    # Initialize a placeholder container for dynamic rows
    if "temp_rows" not in st.session_state:
        st.session_state.temp_rows = [{"item": items[0], "dozen": 0}]

    rows = st.session_state.temp_rows
    st.markdown("### 📝 Item Entries")
    header = st.columns([2, 2, 2, 1])
    header[0].markdown("**Item**")
    header[1].markdown("**No. of Dozen**")
    header[2].markdown("**Boxes**")
    header[3].markdown("")

    # Track rows to delete
    rows_to_delete = []

    for i, row in enumerate(rows):
        cols = st.columns([2, 2, 2, 1])
        row["item"] = cols[0].selectbox("Item", items, index=items.index(row["item"]), key=f"item_{i}", label_visibility="collapsed")
        row["dozen"] = cols[1].number_input("dozen", min_value=0, value=row["dozen"], step=1, key=f"dozen_{i}", label_visibility="collapsed")
        boxes = compute_boxes(row["item"], row["dozen"])
        cols[2].number_input("boxes", value=boxes, disabled=True, key=f"box_{i}", label_visibility="collapsed")

        if cols[3].button("❌", key=f"del_{i}"):
            rows_to_delete.append(i)

    for i in sorted(rows_to_delete, reverse=True):
        del rows[i]

    if rows_to_delete:
        st.rerun()
    
    if st.button("➕ Add Row"):
        rows.append({"item": items[0], "dozen": 0})
        st.rerun()

    if st.button("💾 Save"):
        if not dc_entry:
            st.warning("⚠️ Please enter a DC Entry Number.")
        elif not rows:
            st.warning("⚠️ No rows to save.")
        else:
            try:
                create_dc_entry(
                    dc_entry,
                    [
                        {
                            "Item": row["item"],
                            "Dozen": row["dozen"],
                            "Boxes": compute_boxes(row["item"], row["dozen"])
                        }
                        for row in rows
                    ]
                )
                st.success("✅ Saved successfully to database!")
                st.session_state.temp_rows = [{"item": items[0], "dozen": 0}]
            except Exception as e:
                st.error(f"❌ Error saving entry: {e}")

# ============== TAB 2: VIEW EXISTING DC ==============
with tab2:
    st.title("📋 View DC Entry")

    dc_input = st.text_input("Enter DC_Entry_Number to view:")

    if st.button("🔍 Search"):
        st.session_state.search_dc = dc_input  # Persist search

    if "search_dc" in st.session_state and st.session_state.search_dc:  
        search_dc = st.session_state.search_dc 
        dc_data = fetch_dc_entry(search_dc)
        if not dc_data:
            st.warning("❌ No entry found with that DC number.")
        else:
            st.markdown(f"### DC Number: `{search_dc}`")
            st.dataframe(pd.DataFrame(dc_data), hide_index=True, use_container_width=True)

            with st.expander("Add Delivery Details to This DC"):
                # 📥 Form to append new box entry
                st.markdown("### Add Delivery Details to This DC")
                with st.form(key="add_box_form"):
                    col1, col2, col3 = st.columns(3)
                    date = col1.date_input("Date", value=date.today())
                    item = col2.selectbox("Item", items)
                    boxes = col3.number_input("No. of Boxes", min_value=1, step=1)
                    
                    submitted = st.form_submit_button("💾 Save Entry")
                    if submitted:
                        try:
                            add_dc_delivery_details(search_dc, date, item, boxes)
                            st.success("✅ Entry added successfully!")
                            # st.rerun()  # Refresh the page to show updated data
                        except Exception as e:
                            st.error(f"❌ Error adding entry: {e}")

            with st.expander("Existing Delivery Details of the DC"):
                st.markdown("### 📦 Delivery Summary for DC: `" + search_dc + "`") 
                summary_df = get_dc_delivery_details(search_dc)
                if not summary_df.empty:
                    st.dataframe(summary_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No delivery entries found for this DC.")       

# ============== TAB 3: PLACEHOLDER FOR INVOICE ==============
with tab3:
    st.title("Invoice Entry")
