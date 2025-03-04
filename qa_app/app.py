from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key-here")

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# In-memory storage for questions and answers
questions = []
question_counter = 0


class Question:
    def __init__(self, title, content):
        global question_counter
        question_counter += 1
        self.id = question_counter
        self.title = title
        self.content = content
        self.created_at = datetime.utcnow()
        self.answers = []


class Answer:
    def __init__(self, content, is_ai_generated=False):
        self.content = content
        self.created_at = datetime.utcnow()
        self.is_ai_generated = is_ai_generated


@app.route("/")
def home():
    return render_template("home.html", questions=questions)


@app.route("/ask", methods=["GET", "POST"])
def ask():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        if title and content:
            try:
                # Create new question
                question = Question(title=content)

                # Generate AI response
                ai_response = generate_ai_answer(content)

                if ai_response:
                    # Add AI answer
                    ai_answer = Answer(ai_response, is_ai_generated=True)
                    question.answers.append(ai_answer)

                # Store question
                questions.append(question)

                flash(
                    "Your question has been posted with an AI-generated response!",
                    "success",
                )
                return redirect(url_for("question", id=question.id))
            except Exception as e:
                flash(f"Error generating AI response: {str(e)}", "error")

    return render_template("ask.html")


def generate_ai_answer(question_content):
    try:
        # You can customize this prompt based on your specific use case
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant providing clear, accurate answers to questions.
                    Base your responses on the context provided and your general knowledge.""",
                },
                {"role": "user", "content": question_content},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return None


@app.route("/question/<int:id>", methods=["GET", "POST"])
def question(id):
    question = next((q for q in questions if q.id == id), None)
    if question is None:
        flash("Question not found!", "error")
        return redirect(url_for("home"))

    if request.method == "POST":
        content = request.form.get("content")
        if content:
            answer = Answer(content, is_ai_generated=False)
            question.answers.append(answer)
            flash("Your answer has been posted!", "success")
            return redirect(url_for("question", id=id))

    return render_template("question.html", question=question)


if __name__ == "__main__":
    app.run(debug=True)
