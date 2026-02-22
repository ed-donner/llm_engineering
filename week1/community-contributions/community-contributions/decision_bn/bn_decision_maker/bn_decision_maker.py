"""
Core Bayesian Network logic for decision analysis.
Handles BN construction, inference, and expected utility calculations.
"""
import pyagrum as gum
from typing import Dict, List, Tuple, Optional


class DecisionBN:
    """Wrapper for pyAgrum Bayesian Network with decision analysis capabilities."""
    
    def __init__(self, bn_data: dict, name: str = "DecisionBN"):
        """
        Initialize BN from structured JSON data.
        Builds either a BayesNet (for pure probabilistic analysis) or 
        InfluenceDiagram (when utilities are present).
        
        Args:
            bn_data: Dictionary with 'variables', 'edges', 'cpts' keys
                     Optional 'utilities' key for decision analysis
            name: Name for the Bayesian Network
        """
        self.bn_data = bn_data
        self.has_utilities = 'utilities' in bn_data
        
        # Create either InfluenceDiagram or BayesNet
        if self.has_utilities:
            self.bn = gum.InfluenceDiagram()
        else:
            self.bn = gum.BayesNet(name)
        
        self.var_states_map = {}
        self._build_bn()
    
    def _build_bn(self):
        """Build the Bayesian Network (or Influence Diagram) from bn_data."""
        # Map variable names to their states
        self.var_states_map = {
            v["name"]: v["states"] 
            for v in self.bn_data["variables"]
        }
        
        # Add all chance variables (excluding Decision if utilities exist)
        var_map = {}
        for var in self.bn_data["variables"]:
            # Skip "Decision" variable if utilities exist - it will be added as decision node
            if self.has_utilities and var["name"] == "Decision":
                continue
                
            lv = gum.LabelizedVariable(var["name"], var["name"], 0)
            for label in var["states"]:
                lv.addLabel(label)
            
            if self.has_utilities:
                var_map[var["name"]] = self.bn.addChanceNode(lv)
            else:
                var_map[var["name"]] = self.bn.add(lv)
        
        # If utilities exist, add decision and utility nodes
        if self.has_utilities:
            self._add_decision_and_utility_nodes()
        
        # Add all edges (arcs)
        for parent, child in self.bn_data.get("edges", []):
            self.bn.addArc(parent, child)
        
        # Fill CPTs (Conditional Probability Tables)
        self._fill_cpts()
    
    def _add_decision_and_utility_nodes(self):
        """Add decision variable and utility node to the Influence Diagram."""
        utilities_config = self.bn_data['utilities']
        outcome_var = utilities_config['outcome_var']
        actions = utilities_config['actions']
        
        # Create decision variable with action labels
        action_labels = list(actions.keys())
        decision_var = gum.LabelizedVariable("Decision", "Decision", 0)
        for action in action_labels:
            decision_var.addLabel(action)
        
        self.bn.addDecisionNode(decision_var)
        self.var_states_map["Decision"] = action_labels
        
        # Create utility node (single value per outcome)
        utility_var = gum.LabelizedVariable("Utility", "Utility", 1)
        utility_node_id = self.bn.addUtilityNode(utility_var)
        
        # Connect decision -> utility and outcome -> utility
        self.bn.addArc("Decision", "Utility")
        self.bn.addArc(outcome_var, "Utility")

        if 'observed_vars' in utilities_config:
            for observed_var in utilities_config['observed_vars']:
                self.bn.addArc(observed_var, "Decision")
        
        # Fill utility table
        self._fill_utility_table(outcome_var, actions)
    
    def _fill_utility_table(self, outcome_var: str, actions: Dict[str, Dict[str, float]]):
        """Fill the utility table based on decision and outcome."""
        utility_table = self.bn.utility("Utility")
        
        outcome_states = self.var_states_map[outcome_var]
        action_labels = list(actions.keys())
        
        # Fill utility values for each (decision, outcome) combination
        for action_idx, action in enumerate(action_labels):
            for outcome_idx, outcome_state in enumerate(outcome_states):
                utility_value = actions[action][outcome_state]
                # pyAgrum utility indexing: [decision_idx][outcome_idx]
                utility_table[{
                    "Decision": action_idx,
                    outcome_var: outcome_idx
                }] = [utility_value]
    
    def _fill_cpts(self):
        """Fill all CPTs from bn_data."""
        for var_name, cpt_json in self.bn_data["cpts"].items():
            states_var = self.var_states_map[var_name]
            cpt = self.bn.cpt(var_name)
            
            # Case 1: Prior probability (no parents)
            if "parents" not in cpt_json:
                probs = [float(cpt_json[s]) for s in states_var]
                cpt.fillWith(probs)
                continue
            
            # Case 2: Conditional probability (has parents)
            parents = cpt_json["parents"]
            table = cpt_json["table"]
            
            for combo_str, child_probs_dict in table.items():
                # Parse parent state combination
                combo_list = [s.strip() for s in combo_str.split(",")]
                
                # Convert parent state labels to indices
                parent_indices = [
                    self.var_states_map[p].index(lbl) 
                    for p, lbl in zip(parents, combo_list)
                ]
                
                # pyAgrum expects reversed order for indexing
                parent_key = tuple(parent_indices[::-1])
                
                # Get probabilities in correct order
                probs = [float(child_probs_dict[s]) for s in states_var]
                cpt[parent_key] = probs

    def get_cpt(self, var_name: str) -> gum.Potential:
        """
        Get the Conditional Probability Table (CPT) for a variable.
        
        Args:
            var_name: Variable name
            
        Returns:
            pyAgrum Table object representing the CPT
        """
        return self.bn.cpt(var_name)
    
    def get_marginal(self, varname: str) -> Dict[str, float]:
        """
        Get marginal probability distribution P(varname).
        
        Args:
            varname: Variable name to query
            
        Returns:
            Dictionary mapping state -> probability
        """
        # Use appropriate inference engine based on graph type
        if isinstance(self.bn, gum.InfluenceDiagram):
            ie = gum.ShaferShenoyLIMIDInference(self.bn)
        else:
            ie = gum.LazyPropagation(self.bn)
        
        ie.makeInference()
        
        vid = self.bn.idFromName(varname)
        posterior = ie.posterior(vid)
        states = self.var_states_map[varname]
        
        return {states[i]: float(posterior[i]) for i in range(len(states))}
    
    def get_posterior(
        self, 
        query_vars: List[str], 
        evidence: Optional[Dict[str, str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        Get posterior distributions given evidence.
        
        Args:
            query_vars: List of variable names to query
            evidence: Dictionary mapping variable_name -> state_label
            
        Returns:
            Dictionary mapping varname -> {state: probability}
        """
        evidence = evidence or {}
        
        # Use appropriate inference engine based on graph type
        if isinstance(self.bn, gum.InfluenceDiagram):
            ie = gum.ShaferShenoyLIMIDInference(self.bn)
        else:
            ie = gum.LazyPropagation(self.bn)
        
        # Add evidence
        for vname, label in evidence.items():
            vid = self.bn.idFromName(vname)
            state_index = self.var_states_map[vname].index(label)
            ie.addEvidence(vid, state_index)
        
        ie.makeInference()
        
        # Compute posteriors for all query variables
        results = {}
        for q in query_vars:
            qid = self.bn.idFromName(q)
            posterior = ie.posterior(qid)
            states = self.var_states_map[q]
            results[q] = {states[i]: float(posterior[i]) for i in range(len(states))}
        
        return results
    
    def get_optimal_policy(self):
        """
        Compute the optimal action based on current BN structure.
        Only works with InfluenceDiagram.

        Returns:
            optimal_decision: The optimal action label given the specific evidence
        """
        if not isinstance(self.bn, gum.InfluenceDiagram):
            raise ValueError("compute_optimal_decision only works with InfluenceDiagram")
                
        ie = gum.ShaferShenoyLIMIDInference(self.bn)
        ie.makeInference()
        # Get optimal decision - returns a Potential (probability distribution)
        optimal_decision_policy = ie.optimalDecision("Decision")
        
        return optimal_decision_policy
    
    def compute_expected_utilities(
        self,
        outcome_var: str,
        utilities: Dict[str, Dict[str, float]],
        evidence: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """
        Compute expected utility for each action.
        
        Args:
            outcome_var: The chance node determining utility (e.g., 'Overheat')
            utilities: {action_label: {outcome_state: utility_value}}
            evidence: Optional evidence mapping
            
        Returns:
            Dictionary mapping action_label -> expected utility
            
        Raises:
            ValueError: If utility states don't match BN states
        """
        # Get posterior distribution of outcome variable
        posterior = self.get_posterior([outcome_var], evidence)[outcome_var]
        
        # Compute expected utility for each action
        results = {}
        for action, util_map in utilities.items():
            # Validate that all posterior states exist in utility map
            missing_states = set(posterior.keys()) - set(util_map.keys())
            if missing_states:
                raise ValueError(
                    f"Utility map for action '{action}' missing states: {missing_states}. "
                    f"BN has states {list(posterior.keys())}, "
                    f"but utilities define {list(util_map.keys())}"
                )
            
            eu = sum(posterior[state] * util_map[state] for state in posterior)
            results[action] = eu
        
        return results
    
    def get_variables(self) -> List[str]:
        """Get list of all variable names in the BN."""
        return list(self.var_states_map.keys())
    
    def get_states(self, varname: str) -> List[str]:
        """Get list of states for a variable."""
        return self.var_states_map[varname]
    
    def get_bn_graph(self):
        """
        Get the underlying pyAgrum graph for visualization.
        Returns either a BayesNet or InfluenceDiagram depending on configuration.
        """
        return self.bn