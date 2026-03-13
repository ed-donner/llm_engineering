"""Model implementations: baselines, traditional ML, neural net, LLM wrappers."""
import numpy as np
import torch
import torch.nn as nn
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import xgboost as xgb
import litellm
import re


# ============ BASELINES ============

class RandomPricer:
    """Baseline that predicts random prices within a range."""
    
    def __init__(self, price_min: float, price_max: float):
        self.price_min = price_min
        self.price_max = price_max
    
    def predict(self, X) -> np.ndarray:
        """Return random predictions for each input."""
        return np.random.uniform(self.price_min, self.price_max, size=len(X))


class MeanPricer:
    """Baseline that always predicts the training set mean."""
    
    def __init__(self):
        self.mean_price = None
    
    def fit(self, y):
        """Learn the mean price from training data."""
        self.mean_price = np.mean(y)
        return self
    
    def predict(self, X) -> np.ndarray:
        """Return mean price for each input."""
        return np.full(len(X), self.mean_price)


# ============ TRADITIONAL ML ============

def train_linear_regression(X_train, y_train) -> LinearRegression:
    """Train a linear regression model."""
    model = LinearRegression()
    model.fit(X_train, y_train)
    return model


def train_random_forest(
    X_train, y_train, 
    n_estimators: int = 100,
    random_state: int = 42
) -> RandomForestRegressor:
    """Train a random forest regressor."""
    model = RandomForestRegressor(
        n_estimators=n_estimators, 
        random_state=random_state, 
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model


def train_xgboost(
    X_train, y_train,
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    random_state: int = 42
) -> xgb.XGBRegressor:
    """Train an XGBoost regressor."""
    model = xgb.XGBRegressor(
        n_estimators=n_estimators, 
        learning_rate=learning_rate, 
        random_state=random_state
    )
    model.fit(X_train, y_train)
    return model


# ============ NEURAL NETWORK ============

class HousePriceMLP(nn.Module):
    """Multi-layer perceptron for house price prediction."""
    
    def __init__(self, input_dim: int = 4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x):
        return self.net(x)


def train_neural_network(
    X_train: np.ndarray,
    y_train: np.ndarray,
    input_dim: int = 4,
    epochs: int = 100,
    learning_rate: float = 1e-3,
    log_fn=None
) -> HousePriceMLP:
    """Train the MLP model.
    
    Args:
        X_train: Training features
        y_train: Training targets
        input_dim: Number of input features
        epochs: Number of training epochs
        learning_rate: Learning rate for Adam optimizer
        log_fn: Optional callback for logging (epoch, loss)
        
    Returns:
        Trained model
    """
    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    
    model = HousePriceMLP(input_dim=input_dim)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        preds = model(X_train_t)
        loss = criterion(preds, y_train_t)
        loss.backward()
        optimizer.step()
        
        if log_fn and epoch % 10 == 0:
            log_fn(epoch, loss.item())
    
    return model


def predict_neural_network(model: HousePriceMLP, X: np.ndarray) -> np.ndarray:
    """Get predictions from the neural network."""
    model.eval()
    X_t = torch.tensor(X, dtype=torch.float32)
    with torch.no_grad():
        preds = model(X_t).squeeze().numpy()
    return preds


# ============ LLM WRAPPERS ============

def parse_price(text: str) -> float:
    """Extract price from LLM response like '$450,000' or '450000'.
    
    Args:
        text: LLM response text
        
    Returns:
        Extracted price as float, or 0.0 if parsing fails
    """
    text = text.replace(",", "").replace("$", "")
    match = re.search(r"\d+\.?\d*", text)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0


def predict_with_llm(model_name: str, messages: list[dict]) -> float:
    """Get price prediction from an LLM.
    
    Args:
        model_name: LiteLLM model identifier (e.g., 'gpt-4o-mini')
        messages: List of message dicts with role and content
        
    Returns:
        Predicted price as float
    """
    response = litellm.completion(model=model_name, messages=messages)
    return parse_price(response.choices[0].message.content)
