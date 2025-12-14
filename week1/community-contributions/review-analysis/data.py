import pandas as pd


# Database obtained from Kaggle:
# https://www.kaggle.com/datasets/sampaiovitor/avaliaes-em-portugus-amazon-e-mercado-livre?resource=download

PATH = "week1/community-contributions/review-analysis/ml_scrape_final.csv"

def get_comments(path=PATH):
    """Obtains the review comments for monitors from the dataset."""

    df = pd.read_csv(path)

    # Filter reviews for the category "monitor"
    monitors = df[df["Pesquisa"] == "monitor"]

    # Filter reviews for a specific title
    search = "Monitor Gamer LG 24mk430h Led 23.8 Ips Fhd Preto 100v/240v"
    monitor_filter = monitors[monitors["Titulo"] == search]
    # Extract the comments from the filtered reviews
    comments = monitor_filter["Comentario"].tolist()

    return comments


