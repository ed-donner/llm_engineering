from pydantic import BaseModel, Field
from typing import List


class Article(BaseModel):
    title: str = Field(description="The article title")
    url: str = Field(description="The article URL")
    source: str = Field(default="", description="Source of the article")
    summary: str = Field(
        default="",
        description="A clear 2-3 sentence summary of what the article is about",
    )


class ArticleSelection(BaseModel):
    articles: List[Article] = Field(
        description="The 5 most interesting tech articles with clear summaries"
    )


class Opportunity(BaseModel):
    article: Article
    importance: float = Field(default=0.0, description="Importance score 0-10")
    context: str = Field(default="", description="Related past articles")
    alerted: bool = Field(default=False)
