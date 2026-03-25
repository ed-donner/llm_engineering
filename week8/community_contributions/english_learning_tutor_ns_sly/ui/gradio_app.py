
import gradio as gr


def create_ui(orchestrator, stt):

    def evaluate(audio, level, category):

        spoken = stt.transcribe(audio)

        result = orchestrator.run_exercise(
            level,
            category,
            spoken,
            audio
        )

        heatmap = " ".join(
            f"🟢{w['word']}" if w["status"] == "correct"
            else f"🔴{w['word']}"
            for w in result["heatmap"]
        )

        tips = "\n".join(result["tips"])

        return (

            spoken,

            result["exercise"],

            heatmap,

            tips,

            result["pronunciation"]["accent_score"],

            result["recommended_level"],

            str(result["progress"])
        )

    return gr.Interface(

        fn=evaluate,

        inputs=[

            gr.Audio(type="filepath"),

            gr.Dropdown(
                ["Beginner","Intermediate","Advanced","Native"],
                label="Difficulty Level"
            ),

            gr.Dropdown(
                [
                    "Accent Practice",
                    "Conversation",
                    "Business Communication",
                    "Tech Workplace",
                    "CEO Communication",
                    "Sales"
                ],
                label="Exercise Category"
            )
        ],

        outputs=[

            gr.Textbox(label="Transcription"),

            gr.Textbox(label="Exercise"),

            gr.Textbox(label="Pronunciation Heatmap"),

            gr.Textbox(label="Pronunciation Tips"),

            gr.Number(label="Accent Score"),

            gr.Textbox(label="Recommended Level"),

            gr.Textbox(label="Progress")
        ],

        title="Agentic English Accent & Conversation Tutor"
    )

