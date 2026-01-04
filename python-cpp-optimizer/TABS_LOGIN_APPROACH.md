# Tab-Based Login for HuggingFace Compatibility

## Why Tabs Work Best

Gradio Tabs provide reliable visibility control because:
1. They're natively designed for showing/hiding content
2. They work consistently across browsers and iframes
3. No complex CSS positioning issues
4. Gradio handles the visibility state internally

## Implementation

```python
with gr.Tabs() as tabs:
    with gr.Tab("Login", visible=True) as login_tab:
        # Login UI
        password = gr.Textbox(type="password")
        btn = gr.Button("Login")
        
    with gr.Tab("Main App", visible=False) as main_tab:
        # Your actual app content
        pass

def check_password(pw):
    if pw == APP_PASSWORD:
        # Hide login, show main
        return gr.Tabs(selected=1)  # Switch to tab 1
    else:
        return gr.Tabs(selected=0)  # Stay on tab 0

btn.click(check_password, password, tabs)
```

## Key Points

- Use `selected` parameter to switch tabs programmatically
- Tab index starts at 0
- This works in HF iframes where browser basic-auth fails
- Clean, simple, reliable

