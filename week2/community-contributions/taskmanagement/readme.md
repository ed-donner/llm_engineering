This code implements a Gradio chat application that integrates with OpenAI models for the chat functionality, with special handling for ABCD tasks.

# Main Features
1. **General Chat**: Use OpenAI's GPT to handle normal conversation.
2. **Task Checking**: When users mention "check ABCD tasks" (or similar phrases), the app calls the abcd_taskTool() function.
3. **Account Number Masking**: Masks the first four digits of account number with "XXXX".
4. **Task Display**: in HTML table.
5. **Support Notification**: Offers to notify support team and calls abcd_NotifyTool() if user confirms.
6. **Cheerful Responses**: Provides rando encouraging messages when no tasks are found.

## Screenshot
![Chat1](https://github.com/sngo/llms-practice/blob/main/taskmanagement/chat1.png)
![Chat2](https://github.com/sngo/llms-practice/blob/main/taskmanagement/chat2.png)
