# 1. imports: Gradio + the 3 helper files
import gradio as gr
import config  # runs config.py once, which loads the keys from .env
from personas import MODELS, debater_prompt, judge_prompt
from chat import ask

# safety cap: the debate never runs more than 5 rounds
MAX_ROUNDS = 5


# 2. the callback: Gradio hands in the topic + 4 boxes per seat (model, name, purpose, rule)
def debate(topic, d1_model, d1_name, d1_purpose, d1_rule, d2_model, d2_name, d2_purpose, d2_rule, j_model, j_name, j_purpose, j_rule):
    # the seating plan built from the boxes: (name, real model, finished prompt)
    bots = [
        (d1_name, MODELS[d1_model], debater_prompt(d1_name, d1_purpose, d1_rule)),
        (d2_name, MODELS[d2_model], debater_prompt(d2_name, d2_purpose, d2_rule)),
        (j_name, MODELS[j_model], judge_prompt(j_name, j_purpose, j_rule, d1_name, d1_rule, d2_name, d2_rule)),
    ]
    # the judge opens the chat with the topic
    transcript = f"**{j_name}:** Welcome! Today's debate: {topic}\n\n"
    # hand the opening line to the page right away
    yield transcript
    # up to MAX_ROUNDS rounds, each bot speaks once per round
    for turn in range(MAX_ROUNDS):
        for name, model, system in bots:
            # every call resends the whole transcript: the models remember nothing on their own
            reply, cost = ask(model, system, transcript + f"\nYou are {name}. Write only your next message.")
            transcript += f"**{name}:** {reply}\n\n"
            # hand the bigger text to the page after every reply (this makes debate() a generator)
            yield transcript
            # the judge named a loser: end the whole debate here
            if "LOSER:" in reply:
                return


# 3. the page: topic + 12 seat boxes in, the streamed debate out
topic_input = gr.Textbox(label="Debate topic", value="Which club is the best in the world?")
# seat 1: debater 1's 4 boxes, each with a default so you can just press Submit
d1_model_box = gr.Dropdown(list(MODELS), label="Debater 1 model", value="GPT")
d1_name_box = gr.Textbox(label="Debater 1 name", value="Max")
d1_purpose_box = gr.Textbox(label="Debater 1 purpose", value="prove Man United is the best club in the world")
d1_rule_box = gr.Textbox(label="Debater 1 rule", value="if you are beaten in the argument, you give up")
# seat 2: debater 2's 4 boxes
d2_model_box = gr.Dropdown(list(MODELS), label="Debater 2 model", value="Claude")
d2_name_box = gr.Textbox(label="Debater 2 name", value="Leo")
d2_purpose_box = gr.Textbox(label="Debater 2 purpose", value="prove Barcelona is the best club in the world")
d2_rule_box = gr.Textbox(label="Debater 2 rule", value="if you are beaten in the argument, you give up")
# seat 3: the judge's 4 boxes
j_model_box = gr.Dropdown(list(MODELS), label="Judge model", value="Llama")
j_name_box = gr.Textbox(label="Judge name", value="Judy")
j_purpose_box = gr.Textbox(label="Judge style", value="fair but funny, teases both sides")
j_rule_box = gr.Textbox(label="How the judge decides", value="facts and stats win, not shouting")

# the debate appears here, growing after every reply
debate_output = gr.Markdown(label="Debate")

# the inputs list must match debate()'s 13 parameters, in the same order
view = gr.Interface(
    fn=debate,
    title="Council of LLMs",
    inputs=[topic_input,
            d1_model_box, d1_name_box, d1_purpose_box, d1_rule_box,
            d2_model_box, d2_name_box, d2_purpose_box, d2_rule_box,
            j_model_box, j_name_box, j_purpose_box, j_rule_box],
    outputs=[debate_output],
    flagging_mode="never",
)
view.launch(inbrowser=True)
