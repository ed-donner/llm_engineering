import openai

# Step 1: Summarize the patient consultation note
def summarize_patient_note(note_text):
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Please summarize the following patient consultation note in a clear, clinical style:\n\n{note_text}"}
        ]
    )
    return response.choices[0].message.content

# Step 2: Generate a specialist referral letter
def generate_referral_letter(summary_text, specialist_type):
    system_prompt = f"You are an experienced general practitioner. Based on the consultation summary, write a concise, professional referral letter to a {specialist_type}."

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Consultation summary:\n\n{summary_text}"}
        ]
    )
    return response.choices[0].message.content

# Main logic
if __name__ == "__main__":
    try:
        with open('patient_note.txt', 'r', encoding='utf-8') as file:
            patient_note = file.read()

        # Step 1: Summarize the note
        summary = summarize_patient_note(patient_note)
        print("\n🩺 Consultation Summary:")
        print(summary)

        # Step 2: Ask user which specialist to refer to
        specialist = input("\n➡️  Which specialist is this referral for (e.g., cardiologist, neurologist)?\n")

        # Step 3: Generate the referral letter
        referral_letter = generate_referral_letter(summary, specialist)
        print("\n📨 Generated Referral Letter:\n")
        print(referral_letter)

    except FileNotFoundError:
        print("❌ The file 'patient_note.txt' was not found. Please ensure it exists in the project folder.")
