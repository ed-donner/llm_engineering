"""
Main entry point for AI English Tutor.

Features
--------
- First exercise displayed on UI load
- User records pronunciation
- AI evaluates accent and pronunciation
- Generates next exercise automatically
- Tracks user progress
"""

import logging
import gradio as gr

from speech.speech_to_text import SpeechToText
from agents.orchestrator_agent import LearningOrchestrator
from progress.progress_tracker import ProgressTracker


# ---------------------------
# Global components
# ---------------------------

USER_NAME = "ns_sly"

stt = None
orchestrator = None
tracker = None


# ---------------------------
# Initialize system
# ---------------------------

def initialize_system():
    global stt, orchestrator, tracker

    print("Initializing AI English Tutor components...")

    stt = SpeechToText()
    orchestrator = LearningOrchestrator()
    tracker = ProgressTracker()

    print("Initialization complete.")


# ---------------------------
# Generate first exercise
# ---------------------------

def generate_first_exercise():

    level = "Beginner"
    category = "Accent Practice"

    try:
        exercise = orchestrator.lesson.retrieve(level, category)

    except Exception as e:

        print("Exercise generation failed:", e)

        exercise = "The weather today is very pleasant."

    return exercise, exercise


def generate_next_exercise(level, category):


    try:
        exercise = orchestrator.lesson.retrieve(level, category)

    except Exception as e:

        print("Exercise generation failed:", e)

        exercise = "The weather today is very pleasant."

    return exercise, exercise
    
# ---------------------------
# Evaluate pronunciation
# ---------------------------

def evaluate_answer(audio, level, category, exercise, username):

    if audio is None:
        return (
            "No audio detected",
            "",
            "",
            0,
            level,
            0,
            0,
            exercise,
            exercise
        )

    # ---------------------------
    # Speech → text
    # ---------------------------

    spoken_text = stt.transcribe(audio)

    # ---------------------------
    # Run orchestrator
    # ---------------------------

    result = orchestrator.run_exercise(
        level=level,
        exercise=exercise,
        spoken_text=spoken_text,
        user_audio=audio,
        username=username,
        category=category
    )

    # ---------------------------
    # Update progress
    # ---------------------------



    # ---------------------------
    # Format pronunciation heatmap
    # ---------------------------

    heatmap = " ".join(
        f"🟢{w['word']}" if w["status"] == "correct"
        else f"🔴{w['word']}"
        for w in result["heatmap"]
    )


    overall_progress = tracker.get_overall_progress(username)

    # Generate next exercise

    try:

        next_exercise = orchestrator.lesson.retrieve(
            level,
            category
        )

    except Exception:

        next_exercise = exercise

    mistakes_text = "\n".join(result["grammar"].mistakes) or "No mistakes found"
    corrections_text = "\n".join(result["grammar"].corrections) or "No corrections found"
    return (
        spoken_text,
        heatmap,
        result["tips"],
        result["pronunciation"]["pronunciation_score"],
        result["pronunciation"]["accent_score"],
        result["recommended_level"],
        result["level_progress"],
        overall_progress,
        next_exercise,
        exercise,
        result["grammar"].grammar_score,
        mistakes_text,
        corrections_text,
        result["grammar"].explanation or "No explanation provided"
    )

# ---------------------------
# Build Gradio UI
# ---------------------------

def build_ui():

    level_choices = [
        "Beginner",
        "Intermediate",
        "Advanced",
        "Native"
    ]

    category_choices = [
        "Accent Practice",
        "Conversation",
        "Business Communication",
        "Tech Workplace",
        "CEO Communication",
        "Sales"
    ]

    with gr.Blocks(title="AI English Accent Tutor") as ui:

        gr.Markdown("# English Accent & Conversation Tutor")
        gr.Markdown(
            "Practice English pronunciation, accent, and fluency using AI."
        )

        with gr.Row():

            level = gr.Dropdown(
                level_choices,
                value="Beginner",
                label="Level"
            )

            category = gr.Dropdown(
                category_choices,
                value="Accent Practice",
                label="Category"
            )
            username = gr.Textbox(
                value=USER_NAME,
                label="userame",
                interactive=True
            )

        exercise_box = gr.Textbox(
            label="Pronunciation Exercise",
            interactive=False,
            max_lines=5,
            lines=2
        )
     
        next_btn = gr.Button("Next Exercise")
        

        audio_input = gr.Audio(
            type="filepath",
            label="Record your pronunciation"
        )

        submit_btn = gr.Button("Submit Answer")

        gr.Markdown("### Evaluation")

        transcription = gr.Textbox(label="Your Speech", interactive=False)

        heatmap = gr.Textbox(label="Pronunciation Heatmap", interactive=False)

        tips = gr.Textbox(label="Pronunciation Tips", interactive=False, lines=2, max_lines=5)

        pronunciation_score = gr.Number(label="Pronunciation Accuracy Score", interactive=False)
        
        accent_score = gr.Number(label="Accent Similarity Score", interactive=False)


        recommended_level = gr.Textbox(label="Recommended Level", interactive=False)

        #grammer stats
        grammar_score = gr.Number(label="Grammar Score", interactive=False)
        grammar_mistakes = gr.Textbox(label="Grammar Mistakes", interactive=False, lines=2, max_lines=5)
        grammar_corrections = gr.Textbox(label="Grammar Corrections", interactive=False, lines=2, max_lines=5)
        grammar_explanation = gr.Textbox(label="Grammar Explanation", interactive=False, lines=3, max_lines=5)

        gr.Markdown("### Progress")

        level_progress = gr.Number(label="Level Progress", interactive=False)

        overall_progress = gr.Number(label="Overall Progress", interactive=False)

        # store current exercise
        current_exercise = gr.State(value="")

        # ---------------------------
        # Load first exercise
        # ---------------------------

        ui.load(
            generate_first_exercise,
            inputs=[],
            outputs=[exercise_box, current_exercise]
        )

        #next button logic
        next_btn.click(generate_next_exercise, inputs=[level, category], outputs=[exercise_box, current_exercise])

        # ---------------------------
        # Submit pronunciation
        # ---------------------------

        submit_btn.click(
            evaluate_answer,
            inputs=[
                audio_input,
                level,
                category,
                current_exercise,
                username
            ],
            outputs=[
                transcription,
                heatmap,
                tips,
                pronunciation_score,
                accent_score,
                recommended_level,
                level_progress,
                overall_progress,
                exercise_box,
                current_exercise,
                grammar_score,
                grammar_mistakes,
                grammar_corrections,
                grammar_explanation
            ]
        )

    return ui


# ---------------------------
# Run application
# ---------------------------

def run_app():

    print("Launching Gradio UI...")

    ui = build_ui()

    ui.launch(
        server_name="0.0.0.0",
        server_port=7860
    )


# ---------------------------
# Main entry point
# ---------------------------

if __name__ == "__main__":

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler()

    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )

    root.addHandler(handler)

    root.info("Starting AI English Tutor...")

    initialize_system()

    run_app()