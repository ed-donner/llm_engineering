"""AI Mastered Dungeon Extraction Game storyteller tools module WIP."""

from json import loads

from openai.types.chat import ChatCompletionMessage
from openai.types.chat import ChatCompletionMessageFunctionToolCall
from openai.types.chat.chat_completion_message_function_tool_call import Function


# Tools declaration for future use. (E.g. Tools may handle user status and inventory)
tools = []

tools_map = {}  # This will map each tool with it's tool function.


# A tool call function.
def handle_tool_call(message: ChatCompletionMessage):
    """Tools call handler."""
    tool_call = message.tool_calls[0]
    arguments = loads(tool_call.function.arguments)
    print(f'\nFUNC CALL: {tool_call.function.name}({arguments})\n')
    # Get tool function and call with arguments.
    tool_func = tools_map.get(tool_call.function.name)
    tool_response = tool_func(**arguments)
    response = {"role": "tool", "content": tool_response, "tool_call_id": tool_call.id}
    return response


draw_signature = {
    "name": "draw_scene",
    "description": "Generate an image of the scene based on the description",
    "parameters": {
        "type": "object",
        "properties": {
            "scene_description": {
                "type": "string",
                "description": "A detailed description of the scene to be drawn",
            },
            "scene_style": {
                "type": "string",
                "description": "The art style for the image",
            },
        },
        "required": ["scene_description"],
        "additionalProperties": False,
    },
}


# Tool call response example.
ChatCompletionMessage(
    content="""To begin, first I need to set a scene.
            Imagine you are in a dark room of an old castle.
            The walls are covered in cobwebs and there is a smell of mold in the air.
            As you look around, you notice a slightly ajar door to the north
            and a dark figure lurking in the corner.

            I am going to generate an image of this scene. One moment, please.""",
    refusal=None,
    role="assistant",
    annotations=[],
    audio=None,
    function_call=None,
    tool_calls=[
        ChatCompletionMessageFunctionToolCall(
            id="call_oJqJeXMUPZUaC0GPfMeSd16E",
            function=Function(
                arguments='''{
                "scene_description":"A dark room in an ancient castle.
                    The walls are covered with cobwebs, and there\'s a musty smell in
                    the air.
                    A slightly ajar door to the north and a shadowy figure lurking in
                    the corner.
                    Dim lighting adds to the eerie atmosphere, with flickering shadows.",
                "style":"fantasy"
                }''',
                name="draw_scene"),
            type="function",
        )
    ],
)
