
import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit,
    QRadioButton, QButtonGroup, QProgressBar
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QTimer
import openai
import os
import random


class YouTubeQuizApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Themed YouTube Quiz")
        self.setGeometry(100, 100, 800, 600)

        # OpenAI API setup
        self.client = openai.OpenAI(
            base_url='https://47v4us7kyypinfb5lcligtc3x40ygqbs.lambda-url.us-east-1.on.aws/v1/',
            api_key='a0BIj000001DYCYMA4'
        )

        # Main layout
        self.layout = QVBoxLayout()

        # Theme Input
        self.theme_label = QLabel("Enter a theme in Math or Physics for the video and quiz:")
        self.layout.addWidget(self.theme_label)
        self.theme_input = QLineEdit(self)
        self.layout.addWidget(self.theme_input)

        # Search and Play Button
        self.search_button = QPushButton("Search and Play", self)
        self.search_button.clicked.connect(self.search_and_play_video)
        self.layout.addWidget(self.search_button)

        # Video Player
        self.video_player = QWebEngineView(self)
        self.layout.addWidget(self.video_player)

        # Quiz Section
        self.quiz_label = QLabel("Quiz: Answer the AI's question")
        self.quiz_label.hide()
        self.layout.addWidget(self.quiz_label)

        self.question_label = QLabel("")
        self.question_label.hide()
        self.layout.addWidget(self.question_label)

        self.options_group = QButtonGroup(self)
        self.option1 = QRadioButton("Option 1")
        self.option2 = QRadioButton("Option 2")
        self.option3 = QRadioButton("Option 3")

        self.options_group.addButton(self.option1)
        self.options_group.addButton(self.option2)
        self.options_group.addButton(self.option3)

        self.option1.hide()
        self.option2.hide()
        self.option3.hide()

        self.layout.addWidget(self.option1)
        self.layout.addWidget(self.option2)
        self.layout.addWidget(self.option3)

        # Submit Button
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.show_result)
        self.submit_button.hide()
        self.layout.addWidget(self.submit_button)

        # Progress Bar for Results
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.layout.addWidget(self.progress_bar)

        self.setLayout(self.layout)

    def search_and_play_video(self):
        """Search YouTube for a video based on the user-input theme after verifying the topic."""
        theme = self.theme_input.text().strip()
        if not theme:
            self.theme_label.setText("Please enter a valid theme!")
            return

        try:
            # Verify the topic with OpenAI
            is_valid = self.verify_topic(theme)

            if is_valid:
                GOOGLE_API_KEY = "AIzaSyBLjd8-gX-bgATAvf8Y9qnEcjG1L801jcs"
                SEARCH_ENGINE_ID = "00e74ff4c7fc54f38"

                search_query = f"YouTube video {theme}"
                urls = self.fetch_google_search_results(GOOGLE_API_KEY, SEARCH_ENGINE_ID, search_query)

                if urls:
                    embed_url = urls[0].replace("watch?v=", "embed/") + "?autoplay=1"
                    self.video_player.setUrl(QUrl(embed_url))
                    self.video_player.show()

                    # Show the quiz after a delay
                    QTimer.singleShot(10000, lambda: self.ask_ai_question(theme))  # 10 seconds delay
                else:
                    self.theme_label.setText("No videos found. Try another theme.")
            else:
                self.theme_label.setText(
                    f"The topic '{theme}' is not suitable or too broad. Please choose a different topic.")
        except Exception as e:
            self.theme_label.setText(f"An error occurred: {str(e)}")

    def fetch_google_search_results(self, api_key, cx, query, num_results=1):
        """Fetches top URLs from Google Search API for a given query."""
        base_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": num_results
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            search_results = response.json()
            return [item['link'] for item in search_results.get('items', [])]
        else:
            print(f"Error: {response.status_code}, {response.json()}")
            return []

    def verify_topic(self, theme):
        """Verify if the topic is related to math or physics and can be covered in half an hour."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"Is the topic '{theme}' related to math or physics ? Answer in Yes or No"
                    }
                ]
            )
            result = response.choices[0].message.content.strip()
            if "Yes" in result or "yes" in result:
                return True
            else:
                # Extract suggested topic if available
                suggested_topic = result.split('suggest')[-1].strip() if 'suggest' in result else None
                return False
        except Exception as e:
            print(f"Error in topic verification: {str(e)}")
            return False, None



    def ask_ai_question(self, theme):
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user",
                     "content": f"Generate a quiz question based on the theme: {theme} with three options, where one option is the correct answer. Give your response in 4 lines. First line the question. 2nd line correct answer, 3rd line one wrong answer and 4th line another wrong answer"}
                ]
            )
            question_data = response.choices[0].message.content.split('\n')
            question = question_data[0]
            options = question_data[1:4]

            # Display the question and options
            self.quiz_label.show()
            self.question_label.setText(question)
            self.question_label.show()

            # Randomly select which option will be correct
            #correct_index = random.randint(0, 2)
            correct_answer = options[0]

            # Shuffle the options
            random.shuffle(options)

            # Set the text for each option
            self.option1.setText(options[0])
            self.option2.setText(options[1])
            self.option3.setText(options[2])

            # Show the options
            self.option1.show()
            self.option2.show()
            self.option3.show()
            self.submit_button.show()

            # Store the correct answer for later comparison
            self.correct_answer = correct_answer
        except Exception as e:
            self.theme_label.setText(f"Error in AI interaction: {str(e)}")

    def show_result(self):
        """Evaluate the quiz and show the result in the progress bar."""
        selected_answer = self.options_group.checkedButton().text()
        if selected_answer == self.correct_answer:
            self.progress_bar.setValue(100)
            self.theme_label.setText("Correct! Well done!")
        else:
            self.progress_bar.setValue(50)
            self.theme_label.setText(f"Incorrect. The correct answer was: {self.correct_answer}")
        self.progress_bar.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeQuizApp()
    window.show()
    sys.exit(app.exec_())