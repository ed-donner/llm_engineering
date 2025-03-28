"""Test module for R language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_r_detection():
    """Test the R language detection functionality."""
    detector = LanguageDetector()
    
    # Sample R code
    r_code = """
# Load necessary libraries
library(tidyverse)
library(ggplot2)
library(dplyr)

# Create a data frame
data <- data.frame(
  name = c("Alice", "Bob", "Charlie", "David"),
  age = c(25, 30, 35, 40),
  score = c(85, 92, 78, 95)
)

# Basic data operations
summary(data)
str(data)
head(data)

# Create a function
calculate_average <- function(x) {
  return(mean(x, na.rm = TRUE))
}

# Apply the function
avg_score <- calculate_average(data$score)
print(paste("Average score:", avg_score))

# Data manipulation with dplyr
filtered_data <- data %>%
  filter(age > 30) %>%
  select(name, score) %>%
  arrange(desc(score))

# Control structures
if (nrow(filtered_data) > 0) {
  print("Found records with age > 30")
} else {
  print("No records with age > 30")
}

# For loop example
for (i in 1:nrow(data)) {
  if (data$age[i] < 30) {
    data$category[i] <- "Young"
  } else if (data$age[i] < 40) {
    data$category[i] <- "Middle"
  } else {
    data$category[i] <- "Senior"
  }
}

# Create vectors
ages <- c(25, 30, 35, 40)
names <- c("Alice", "Bob", "Charlie", "David")

# Create a list
person <- list(
  name = "Alice",
  age = 25,
  scores = c(85, 90, 92)
)

# Access list elements
person$name
person$scores[2]

# Create factors
gender <- factor(c("Male", "Female", "Female", "Male"))
levels(gender)

# Basic plotting
plot(data$age, data$score, 
     main = "Age vs. Score",
     xlab = "Age",
     ylab = "Score",
     col = "blue",
     pch = 19)

# ggplot visualization
ggplot(data, aes(x = age, y = score)) +
  geom_point(color = "blue", size = 3) +
  geom_smooth(method = "lm", se = FALSE) +
  labs(title = "Age vs. Score", x = "Age", y = "Score") +
  theme_minimal()

# Statistical analysis
model <- lm(score ~ age, data = data)
summary(model)
"""
    
    # Test the detection
    assert detector.detect_r(r_code) == True
    assert detector.detect_language(r_code) == "R"
    
    # Check validation
    valid, _ = detector.validate_language(r_code, "R")
    assert valid == True


if __name__ == "__main__":
    test_r_detection()
    print("All R detection tests passed!")
