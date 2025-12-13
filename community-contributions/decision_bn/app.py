"""
Streamlit web application for Bayesian Network decision analysis.
"""
import traceback
import logging
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from bn_decision_maker import DecisionBN, CaseParser, SYSTEM_PROMPT, APP_CONFIG
from bn_decision_maker.examples.predefined_cases import PREDEFINED_CASES


def create_utility_heatmap(data: pd.DataFrame, x_label: str, y_label: str, title: str):
    """
    Create a heatmap from a DataFrame.
    
    Args:
        data: DataFrame with values to plot
        x_label: Label for x-axis
        y_label: Label for y-axis
        title: Title of the heatmap
    """
    # Sort by values (highest first) and reshape for heatmap
    sorted_pairs = sorted(zip(data.values[0], data.columns), reverse=False)
    sorted_values, sorted_labels = zip(*sorted_pairs) if sorted_pairs else ([], [])
    
    # Reshape values as list of lists for heatmap (each action gets one row)
    z_values = [[val] for val in sorted_values]
    text_values = [[val] for val in sorted_values]

    _, max_label = max(sorted_pairs) if sorted_pairs else None

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=[''],  # Single column, empty label
        y=sorted_labels,  # Action names on y-axis (sorted by value)
        colorscale=[(0, "red"), (1, "green")],
        showscale=False,
        text=text_values,  # Show values on cells
        texttemplate='%{text:.2f}',  # Format as 2 decimal places
        textfont={"size": 14}
    ))
    
    if max_label:
        fig.add_annotation(
            x=0.5, y=max_label,  # Position at the heatmap cell
            text=" ★ Recommended Action",
            showarrow=False,  # No arrow
            xanchor="left",  # Anchor text to the left, so it appears to the right
            font=dict(size=11, color="black", weight="bold"),
            borderwidth=2,
            borderpad=4
        )
    
    fig.update_layout(
        title=title,
        showlegend=False,
        height=max(60 * len(data.columns), 120),
        width=500,  # Fixed width to fit content
        margin=dict(t=40, b=20, l=120, r=150),  # Increased right margin for annotation
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            title=None
        ),
        yaxis=dict(
            showticklabels=True,  # Show action names
            showgrid=False,
            zeroline=False,
            title=None
        )
    )
    return fig

def create_horizontal_bar(labels, values, value_format='.4f', value_label='Probability', colors=None, stacked=False):
    """
    Create a horizontal bar chart showing probability distribution.
    
    Args:
        labels: List of labels for segments
        values: List of values (probabilities)
        value_format: Format string for values (default: '.4f')
        value_label: Label for value in hover template
        colors: Optional list of colors
        stacked: Whether to stack bars (default: False)
    
    Returns:
        plotly Figure object
    """
    fig = go.Figure()

    # Uniform color for non-stacked
    uniform_color = '#636EFA'
    
    # Sort labels and values in descending order by value
    sorted_pairs = sorted(zip(values, labels), reverse=False)
    sorted_values, sorted_labels = zip(*sorted_pairs) if sorted_pairs else ([], [])
    
    fig.add_trace(go.Bar(
        x=sorted_values,
        y=sorted_labels,
        orientation='h',
        text=[f'{v:.3f}' for v in sorted_values],
        textposition='auto',
        marker=dict(color=uniform_color),
        hovertemplate='<b>%{y}</b><br>' + value_label + ': {x:' + value_format + '}<extra></extra>'
    ))
    
    fig.update_layout(
        showlegend=False,
        height=max(40 * len(labels), 80),
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[0, max(sorted_values) * 1.15] if sorted_values else [0, 1]
        ),
        yaxis=dict(
            showticklabels=True,
            showgrid=False,
            zeroline=False
        )
    )
    
    return fig

# Cached function to avoid repeated LLM calls and BN construction
@st.cache_data(ttl=3600)  # Cache for 1 hour
def parse_and_build_bn(case_text: str, system_prompt: str):
    """
    Parse case with LLM and build Bayesian Network.
    Uses models list from config, trying models[0] first and cascading through fallbacks.
    Cached to avoid repeated API calls for the same case.
    """    
    # Setup error logging
    log_dir = "logs"
    import os
    os.makedirs(log_dir, exist_ok=True)
    
    error_log_file = os.path.join(log_dir, f"parse_errors_{datetime.now().strftime('%Y%m%d')}.log")
    logging.basicConfig(
        filename=error_log_file,
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    parser = CaseParser(models=APP_CONFIG.get("models"))
    try:
        parsed_data = parser.parse_case(case_text, system_prompt)
    except Exception as e:
        # Log parsing error
        logging.error(f"Parsing Error:\n{traceback.format_exc()}\n\nCase Text:\n{case_text[:500]}...")
        st.error(traceback.format_exc())
        return None, None
    try:
        bn = DecisionBN(parsed_data['bn-data'])
    except Exception as e:
        # Log unexpected errors
        logging.error(f"Unexpected Error in BN Building:\n{traceback.format_exc()}\n\nParsed Data:\n{parsed_data}")
        st.error(f"Unexpected error: {e}")
        return None, parsed_data
    return bn, parsed_data


# Configure page
st.set_page_config(
    page_title=APP_CONFIG["title"],
    page_icon=APP_CONFIG["page_icon"],
    layout=APP_CONFIG["layout"]
)

# Initialize session state
if 'bn' not in st.session_state:
    st.session_state.bn = None
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = None
if 'case_name' not in st.session_state:
    st.session_state.case_name = None
if 'show_logs' not in st.session_state:
    st.session_state.show_logs = False

st.markdown(f"# {APP_CONFIG['title']}")
st.markdown("*AI-powered decision analysis using Bayesian Networks (pyAgrum)")

st.markdown("---")

# Sidebar for case selection
st.markdown("### Case Description")
input_mode = st.radio(
    "Choose input mode:",
    ["Predefined Case", "Custom Case"],
    label_visibility="collapsed",
    index=1
)

case_text = None
case_name = None
if input_mode == "Predefined Case":
    case_name = st.selectbox(
        "Select a case:",
        options=list(PREDEFINED_CASES.keys())
    )
    case_text = PREDEFINED_CASES[case_name]
    
    with st.container():
        st.info(f"**Selected Case:** {case_name}")
        with st.expander("View Case Description", expanded=True):
            st.markdown(case_text)
else:
    st.markdown("### Explain your custom case, including probabilities, utilities, and dependencies as applicable.")
    case_text = st.text_area(
        "Describe your case:",
        height=180,
        placeholder="Example: A system has component A that fails 10% of the time...",
        label_visibility="collapsed"
    )
    case_name = "Custom Case"
_, col_center, _ = st.columns([1, 1, 1])
with col_center:
    # Analysis button
    analyze_button = st.button("Analyze Case", type="primary", width='stretch')

    if analyze_button:
        if not case_text or not case_text.strip():
            st.error("Please enter or select a case to analyze.")
        else:
            try:
                bn, parsed_data = parse_and_build_bn(case_text, SYSTEM_PROMPT)
                if bn is None:
                    st.stop()
                # Store in session state
                st.session_state.bn = bn
                st.session_state.parsed_data = parsed_data
                st.session_state.case_name = case_name
                
                st.success("Case analyzed successfully! Please check the inferred network structure and CPTs on the left side before moving forward.")
                
                # Debug: show parsed data
                with st.expander("Parsed Data", expanded=False):
                    st.json(parsed_data)
            except Exception as e:
                import traceback
                st.info(f"Issue with parsing and building BN. Please revise your description. Details: {e}")

# Display results if BN is available
if st.session_state.bn is not None:
    bn = st.session_state.bn
    variables = bn.get_variables()
    
    st.markdown("---")
    
    # Create main layout: left column for analysis, right column for network/CPTs
    col_left, col_right = st.columns([1, 2])
    
    with col_right:
        st.markdown("## Analysis")
        st.markdown("")
        
        # Marginal probabilities
        with st.expander("### Marginal Probabilities", expanded=False):
            st.markdown("")
            
            for var in variables:
                marginal = bn.get_marginal(var)
                
                st.markdown(f"**P({var})**")
                
                # Horizontal bar chart
                fig = create_horizontal_bar(
                    labels=list(marginal.keys()),
                    values=list(marginal.values()),
                    value_format=".4f",
                    value_label="Probability",
                    stacked=False
                )
                st.plotly_chart(fig, width='stretch', key=f"marginal_bar_{var}")
                st.markdown("")
        
        # Query with Evidence
        with st.expander("### Query with Evidence", expanded=True):
            st.markdown("")
            
            st.markdown("**Set Evidence (Known Status)**")
            evidence = {}
            cols = st.columns(2)
            for i, var in enumerate(variables):
                with cols[i % 2]:
                    if var == 'Decision':
                        continue  # Skip decision variable for evidence setting
                    else:
                        states = bn.get_states(var)
                        selected_state = st.selectbox(
                            f"**{var}:**",
                            options=["None"] + states,
                            key=f"evidence_{var}"
                        )
                        if selected_state != "None":
                            evidence[var] = selected_state
            if evidence:
                st.markdown("")
                st.info(f"**Current Evidence:** {', '.join([f'{k}={v}' for k, v in evidence.items()])}")
                
                query_vars = [v for v in variables if v not in evidence and v != "Decision"]
                if query_vars:
                    query_var = st.selectbox("Query variable:", query_vars)
                    posterior = bn.get_posterior([query_var], evidence)[query_var]
                    
                    st.markdown(f"**P({query_var} | Evidence)**")

                    # Horizontal bar chart
                    fig = create_horizontal_bar(
                        labels=list(posterior.keys()),
                        values=list(posterior.values()),
                        value_format=".4f",
                        value_label="Probability",
                        stacked=False
                    )
                    st.plotly_chart(fig, width='stretch', key=f"query_bar_{query_var}")

        # Decision Analysis (for predefined cases with known utilities)
        if 'utilities' in st.session_state.parsed_data['bn-data']:
            with st.expander("### Action Recommendation", expanded=True):
                st.markdown("")

                case_config = st.session_state.parsed_data['bn-data']['utilities']
                outcome_var = case_config["outcome_var"]
                actions = case_config["actions"]
                
                # Check if outcome variable exists in BN
                if outcome_var in variables:
                    try:
                        # Compute expected utilities
                        eus = bn.compute_expected_utilities(outcome_var, actions, evidence if evidence else None)
                        
                        fig = create_utility_heatmap(
                            data=pd.DataFrame([eus]),
                            x_label="Expected Utility", y_label="Action", title="Expected Utilities")
                        st.plotly_chart(fig, width='content', key="expected_utilities_heatmap")

                    except ValueError as e:
                        st.error(f"Cannot compute utilities: {str(e)}")
                        st.info(f"The LLM generated states: {bn.get_states(outcome_var)}")
                        st.info(f"Expected states in predefined utilities: {list(actions[list(actions.keys())[0]].keys())}")
                else:
                    st.warning(f"Outcome variable '{outcome_var}' not found in parsed BN. Cannot compute utilities.")
        else:
            st.info("Tip: For custom cases, define utilities manually to enable decision analysis.")
        
    with col_left:
        with st.container(border=True):
            # Network Structure
            st.markdown("## Network Structure")
            import pyagrum as gum
            
            # Get pyAgrum BN object and display it
            agrum_bn = bn.get_bn_graph()
            dot_string = agrum_bn.toDot()
            st.graphviz_chart(dot_string, width='stretch')
            
            st.markdown("---")
            
            # CPTs
            st.markdown("## CPTs (Conditional Probability Tables)")
            for var in variables:
                if var in st.session_state.parsed_data['bn-data']['cpts']:
                    with st.expander(f"**{var}**", expanded=False):
                        cpt = agrum_bn.cpt(var)
                        st.code(str(cpt), language=None)
            
            # Utility table (only for Influence Diagrams)
            if isinstance(agrum_bn, gum.InfluenceDiagram) and 'utilities' in st.session_state.parsed_data['bn-data']:
                st.markdown("## Utility Table")
                try:
                    utility = agrum_bn.utility("Utility")
                    st.code(str(utility), language=None)
                except Exception as e:
                    st.info(f"Utility node present in graph but table not accessible: {e}")
            
            # Optimal Policy
            if "Decision" in variables:
                st.markdown("## Optimal Policy")                
                try:
                    optimal_decision = bn.get_optimal_policy()
                    st.write(optimal_decision)
                except Exception as e:
                    st.error(f"Error computing optimal decision: {str(e)}")
