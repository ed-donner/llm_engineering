# -*- coding:utf-8 -*-

from assistant import LLMAssistant
from website import Website


def run_examples():
    assistant = LLMAssistant()

    sample_text = """
    Dear team,

    We need to finalize the deployment pipeline before Friday.
    The system has issues with CI/CD and testing.

    Regards,
    Manager
    """

    print("\n=== SUMMARY ===")
    print(assistant.summarize(sample_text))

    print("\n=== CLASSIFICATION ===")
    print(assistant.classify(sample_text))

    print("\n=== TRANSLATION ===")
    print(assistant.translate(sample_text, "French"))

    print("\n=== REWRITE ===")
    print(assistant.rewrite(sample_text, "formal"))

    print("\n=== BULLETS ===")
    print(assistant.convert_to_bullets(sample_text))

    print("\n=== ANALYSIS ===")
    print(assistant.analyze(sample_text))

    print("\n=== SENTIMENT ANALYSIS ===")
    print(assistant.sentiment_analysis(sample_text))

    print("\n=== ENTITY EXTRACTION ===")
    print(assistant.entity_extraction(sample_text))

    print("\n=== MEETING MINUTES ===")
    meeting_text = """
    John: We should deploy on Friday.
    Sarah: Testing is not complete yet.
    John: Let's fix CI first.
    """
    print(assistant.meeting_minutes(meeting_text))

    print("\n=== SQL GENERATION ===")
    sql_request = "Get all users who registered in the last 7 days"
    print(assistant.sql_generation(sql_request))

    print("\n=== WEBSITE SUMMARY SECTION ===")
    url = input("Enter a URL to summarize: ")

    print("\nFetching and summarizing...\n")
    
    website = Website(url)
    website.display_summary()


if __name__ == "__main__":
    run_examples()