from graphviz import Digraph

g = Digraph('Architecture', filename='architecture', format='svg')
g.attr(rankdir='TB', fontsize='12', labelloc='t', label='Production Web App Architecture')

# Clusters
with g.subgraph(name='cluster_ui') as ui:
    ui.attr(label='Streamlit UI (app.py)', style='rounded')
    ui.node('UI', 'UI: app.py\n• session_state\n• inputs\n• visualizations\n• error dialogs')

with g.subgraph(name='cluster_core') as core:
    core.attr(label='Core Logic (bn_decision_maker)', style='rounded')
    core.node('CaseParser', 'CaseParser\n• parse_case(text, prompt)\n• validation')
    core.node('DecisionBN', 'DecisionBN\n• build BN\n• inference\n• utilities\n• optimal action')

with g.subgraph(name='cluster_cfg') as cfg:
    cfg.attr(label='Configuration', style='rounded')
    cfg.node('Config', 'config.py\n• SYSTEM_PROMPT\n• APP_CONFIG')

with g.subgraph(name='cluster_data') as data:
    data.attr(label='Data (examples)', style='rounded')
    data.node('Examples', 'examples/predefined_cases.py')

with g.subgraph(name='cluster_engines') as engines:
    engines.attr(label='Engines / Services', style='rounded')
    engines.node('pyAgrum', 'pyagrum\nLazyPropagation\nGraphviz dot', shape='box')
    engines.node('LLM', 'litellm / OpenAI / Claude', shape='box')

# Edges
g.edge('UI', 'CaseParser', label='invoke parse')
g.edge('CaseParser', 'LLM', label='API call', style='dashed')
g.edge('UI', 'DecisionBN', label='construct BN')
g.edge('DecisionBN', 'pyAgrum', label='BN build + inference')
g.edge('UI', 'Config', label='reads')
g.edge('UI', 'Examples', label='reads predefined cases')
g.edge('DecisionBN', 'UI', label='results: marginals/posteriors', dir='back')

g.render(cleanup=True)
print('Generated architecture.svg')