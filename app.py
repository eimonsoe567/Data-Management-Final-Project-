import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date
import os
from dotenv import load_dotenv
import altair as alt

# page aesthetics
st.set_page_config(page_title="University Services", layout="wide")

# custom css for dark mode
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Force Dark Mode Background */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    /* Style the metric cards */
    div[data-testid="stMetric"] {
        background-color: #262730;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30333F;
    }
    /* Metric Text Color */
    [data-testid="stMetricLabel"] {
        color: #b4b4b4;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# database connection
load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )

def run_query(query, params=None):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        st.toast("Operation successful!", icon="✅")
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

def fetch_data(query, params=None):
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        return pd.DataFrame()

# navigation bar
st.title("University Services System")

# Using Tabs as a Top Navigation Bar
tab_dash, tab_students, tab_services, tab_assign = st.tabs([
    "Dashboard", 
    "Manage Students", 
    "Manage Services", 
    "Assign Services"
])

# main dashboard
with tab_dash:
    st.markdown("### Operational Overview")
    
    # quick metrics rows
    col1, col2, col3 = st.columns(3)
    
    total_students = fetch_data("SELECT COUNT(*) as count FROM Students").iloc[0]['count']
    total_services = fetch_data("SELECT COUNT(*) as count FROM StudentServices").iloc[0]['count']
    
    avg_cost_df = fetch_data("SELECT AVG(service_cost) as avg_cost FROM StudentServices")
    avg_cost = round(avg_cost_df.iloc[0]['avg_cost'], 2) if not avg_cost_df.empty and avg_cost_df.iloc[0]['avg_cost'] else 0.0

    col1.metric("Total Students", total_students, delta_color="off")
    col2.metric("Total Services", total_services, delta_color="off")
    col3.metric("Avg. Service Cost", f"${avg_cost}", delta_color="off")

    st.markdown("---")

    # charts row
    # cost per student chart
    st.markdown("##### Total Cost per Student")
    df_cost = fetch_data("SELECT * FROM vw_total_cost_per_student")
    
    if not df_cost.empty:
        chart_cost = alt.Chart(df_cost).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('student_id', title='Student ID', sort=None),
            y=alt.Y('total_cost', title='Total Cost ($)'),
            color=alt.Color('total_cost', scale=alt.Scale(scheme='blues'), legend=None),
            tooltip=['student_id', 'total_cost']
        ).properties(height=350)
        st.altair_chart(chart_cost, use_container_width=True)
    else:
        st.info("No cost data available.")

    st.markdown("---")

    # popularity chart
    st.markdown("##### Service Popularity")
    sql_popularity = """
    SELECT sv.service_name, COUNT(*) as usage_count
    FROM StudentServices ss
    JOIN Services sv ON ss.service_id = sv.service_id
    GROUP BY sv.service_name
    """
    df_popularity = fetch_data(sql_popularity)
    
    if not df_popularity.empty:
        # horizontal bar chart sorted by popularity
        chart_pop = alt.Chart(df_popularity).mark_bar(cornerRadiusBottomRight=5, cornerRadiusTopRight=5).encode(
            x=alt.X('usage_count', title='Count'),
            y=alt.Y('service_name', title='Service Name', sort='-x'),
            color=alt.Color('service_name', legend=None),
            tooltip=['service_name', 'usage_count']
        ).properties(height=350)
        st.altair_chart(chart_pop, use_container_width=True)
    else:
        st.info("No service data available.")

    # data table for recent service history
    st.markdown("---")
    st.markdown("##### Recent Service History")
    
    col_search, col_dummy = st.columns([1, 2])
    search_term = col_search.text_input("Filter by Student Name", placeholder="Type a name...")
    
    if search_term:
        sql = "SELECT * FROM vw_student_services WHERE student_name LIKE %s"
        df_history = fetch_data(sql, (f"%{search_term}%",))
    else:
        df_history = fetch_data("SELECT * FROM vw_student_services")
        
    st.dataframe(
        df_history, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "student_id": "ID",
            "student_name": "Name",
            "service_name": "Service",
            "service_date": "Date",
            "service_cost": st.column_config.NumberColumn("Cost", format="$%.2f")
        }
    )

# second page: manage students
with tab_students:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("##### Current Students")
        students = fetch_data("SELECT * FROM Students")
        st.dataframe(students, use_container_width=True, hide_index=True)
        
    with c2:
        st.markdown("##### Add Student")
        with st.container(border=True):
            with st.form("add_student_form", clear_on_submit=True):
                s_id = st.text_input("Student ID (e.g., S104)")
                f_name = st.text_input("First Name")
                l_name = st.text_input("Last Name")
                email = st.text_input("Email")
                
                if st.form_submit_button("Save Student", use_container_width=True):
                    if s_id and f_name:
                        sql = "INSERT INTO Students (student_id, first_name, last_name, email) VALUES (%s, %s, %s, %s)"
                        run_query(sql, (s_id, f_name, l_name, email))
                        st.rerun()
                    else:
                        st.warning("Missing details.")
        
        st.markdown("##### Delete Student")
        with st.container(border=True):
            del_id = st.text_input("ID to Delete")
            if st.button("Delete", type="primary", use_container_width=True):
                 if del_id:
                    run_query("DELETE FROM Students WHERE student_id = %s", (del_id,))
                    st.rerun()

# third page: manage services
with tab_services:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown("##### Available Services")
        services = fetch_data("SELECT * FROM Services")
        st.dataframe(services, use_container_width=True, hide_index=True)
        
    with c2:
        st.markdown("##### Add Service")
        with st.container(border=True):
            with st.form("add_service_form", clear_on_submit=True):
                s_name = st.text_input("Service Name")
                cost = st.number_input("Base Cost", min_value=0.0, step=0.1)
                
                if st.form_submit_button("Save Service", use_container_width=True):
                    sql = "INSERT INTO Services (service_name, base_cost) VALUES (%s, %s)"
                    run_query(sql, (s_name, cost))
                    st.rerun()

# fourth page: assign services
with tab_assign:
    st.markdown("##### Create New Service Record")
    
    students = fetch_data("SELECT student_id, first_name, last_name FROM Students")
    services = fetch_data("SELECT service_id, service_name, base_cost FROM Services")
    
    if not students.empty and not services.empty:
        student_options = {f"{row['first_name']} {row['last_name']}": row['student_id'] for index, row in students.iterrows()}
        service_options = {f"{row['service_name']} (${row['base_cost']})": (row['service_id'], row['base_cost']) for index, row in services.iterrows()}
        
        with st.container(border=True):
            col1, col2 = st.columns(2)
            
            with col1:
                sel_student_label = st.selectbox("Select Student", list(student_options.keys()))
                service_date = st.date_input("Date(YYYY-MM-DD)", date.today())
            
            with col2:
                sel_service_label = st.selectbox("Select Service", list(service_options.keys()))
                _, default_cost = service_options[sel_service_label]
                final_cost = st.number_input("Final Cost ($)", value=float(default_cost))

            if st.button("Confirm Service Record", type="primary", use_container_width=True):
                s_id = student_options[sel_student_label]
                svc_id = service_options[sel_service_label][0]
                
                sql = "INSERT INTO StudentServices (student_id, service_id, service_date, service_cost) VALUES (%s, %s, %s, %s)"
                run_query(sql, (s_id, svc_id, service_date, final_cost))
    else:
        st.warning("Add students and services first.")