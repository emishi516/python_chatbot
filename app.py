import streamlit as st
import json
import os
import random
import datetime
import getpass
if os.path.exists("news_cache.json"):
    os.remove("news_cache.json")
    print("Cache deleted → next login will fetch fresh news")

import subprocess
subprocess.run(["pip", "install", "-q", "--upgrade", "openai"], capture_output=True)
from openai import OpenAI
print("✅ openai package ready")
# ⭐ Paste your DeepSeek API key here
DEEPSEEK_KEY = "sk-b578e3c88b064d0aad81150a00199004"

# Install feedparser for RSS news (lightweight)
subprocess.run(["pip", "install", "-q", "feedparser"], capture_output=True)
import feedparser
import datetime
print("✅ feedparser ready for rolling Python & AI news")

# ====================== CONFIG ======================
st.set_page_config(page_title="Python Learning Chatbot", page_icon="🐍", layout="wide")

# File names
USERS_FILE = "users.json"
QUESTIONS_FILE = "quiz_questions.json"
USER_DATA_FILE = "user_data.json"
MATERIALS_FILE = "materials.json"
NEWS_CACHE_FILE = "news_cache.json"
DELETE_LOG_FILE = "delete_log.json"

# ============================================================
# ADDED FROM CHATBOT-2 — DeepSeek AI connection test
# ============================================================
USE_AI    = False
ai_client = None

print("🔄 Testing DeepSeek Connection...")
try:
    ai_client = OpenAI(
        api_key  = DEEPSEEK_KEY.strip(),
        base_url = "https://api.deepseek.com"
    )
    _test = ai_client.chat.completions.create(
        model    = "deepseek-chat",
        messages = [{"role": "user", "content": "say ok"}],
        max_tokens = 5
    )
    USE_AI = True
    print("✅ DeepSeek API connected! AI Mode is ON.")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("   Falling back to rule-based chat (basic_chat_response).")

# Pre-populated users
PRESET_USERS = {
    # Employees
    "Emp001": {
      "password": "Emp001",
      "role": "student",
      "login_count": 12,
      "last_login": "2026-04-12T14:30:00Z",
      "show_news": True
    },
    "Emp002": {
      "password": "Emp002",
      "role": "student",
      "login_count": 5,
      "last_login": "2026-04-08T09:15:00Z",
      "show_news": True
    },
    "Emp003": {
      "password": "Emp003",
      "role": "student",
      "login_count": 1,
      "last_login": "2026-04-10T16:45:00Z",
      "show_news": True
    },
    "SpvrB01": {
      "password": "SpvrB01",
      "role": "teacher",
      "login_count": 18,
      "last_login": "2026-04-11T11:20:00Z",
      "show_news": False
    },
    "SpvrB02": {
      "password": "SpvrB02",
      "role": "teacher",
      "login_count": 7,
      "last_login": "2026-04-05T08:50:00Z",
      "show_news": False
    },
    "SpvrB03": {
      "password": "SpvrB03",
      "role": "teacher",
      "login_count": 25,
      "last_login": "2026-04-12T10:05:00Z",
      "show_news": False
    },
    "SpvrB04": {
      "password": "SpvrB04",
      "role": "teacher",
      "login_count": 3,
      "last_login": "2026-03-28T14:30:00Z",
      "show_news": False
    },
    "SpvrB05": {
      "password": "SpvrB05",
      "role": "teacher",
      "login_count": 9,
      "last_login": "2026-04-01T17:10:00Z",
      "show_news": False
    }
}

# General encouragement msgs
ENCOURAGEMENT_POOL = [
    "Great effort! Keep going — practice makes progress.",
    "Nice work! Try another quiz to reinforce what you've learned.",
    "You're improving — small steps add up to big skills.",
    "Don't worry about mistakes; they're how you learn.",
    "Consistent practice will make concepts feel natural.",
    "Coding is a superpower, and you're gaining it one step at a time! 💪",
    "Remember, even the best programmers started exactly where you are today. 🌈"
        ]

# Utility functions to handle JSON files
def ensure_files_exist():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            # add login_count default 0 to each user
            initial = {
                uname: {
                    "password": data["password"],
                    "role": data["role"],
                    "login_count": data["login_count"],
                    "last_login": data.get("last_login"),     # use .get() to avoid KeyError if missing
                    "show_news": True if data["role"] == "student" else False
                }
                for uname, data in PRESET_USERS.items()
            }
            json.dump(initial, f, indent=2)
    if not os.path.exists(QUESTIONS_FILE):
        # Initialize sample questions for 3 topics with 3 MC questions each.
        sample_questions = {
            "Set": [
                {
                    "id": "set_mc_1",
                    "type": "mcq",
                    "question": "Which operation returns the intersection of two sets a and b?",
                    "options": ["a + b", "a & b", "a | b", "a ^ b"],
                    "answer": 1,
                    "explanation": "Use & for intersection."
                },
                {
                    "id": "set_mc_2",
                    "type": "mcq",
                    "question": "What does set([1,2,2,3]) produce?",
                    "options": ["[1,2,2,3]", "[1,2,3]", "{1,2,3}", "(1,2,3)"],
                    "answer": 2,
                    "explanation": "A set removes duplicates and uses braces."
                },
                {
                    "id": "set_fill_1",
                    "type": "fill",
                    "question": "Fill-in: A set is an unordered collection of ______ elements. (one word)",
                    "answer": "unique",
                    "explanation": "Elements in a set are unique; duplicates are removed."
                },
            ],
            "Dictionary": [
                {
                    "id": "dict_mc_1",
                    "type": "mcq",
                    "question": "How do you retrieve the value for key 'k' from dict d with default None if not present?",
                    "options": ["d['k']", "d.get('k')", "d.k", "d.find('k')"],
                    "answer": 1,
                    "explanation": "dict.get('k') returns None if key missing."
                },
                {
                    "id": "dict_mc_2",
                    "type": "mcq",
                    "question": "Which method removes a key and returns its value?",
                    "options": ["pop(key)", "remove(key)", "del key", "discard(key)"],
                    "answer": 0,
                    "explanation": "pop(key) removes and returns the value."
                },
                {
                    "id": "dict_mc_3",
                    "type": "mcq",
                    "question": "What type are dictionary keys required to be?",
                    "options": ["Mutable", "Immutable and hashable", "List", "Function"],
                    "answer": 1,
                    "explanation": "Keys must be hashable (immutable types like tuples, strings)."
                },
            ],
            "Anonymous Function": [
                {
                    "id": "lambda_mc_1",
                    "type": "mcq",
                    "question": "Which of these is a lambda that adds x and y?",
                    "options": ["lambda x, y: x + y", "def add(x,y): return x+y", "lambda x, y: x - y", "add = x + y"],
                    "answer": 0,
                    "explanation": "lambda x, y: x + y creates an anonymous function that returns the sum."
                },
                {
                    "id": "lambda_mc_2",
                    "type": "mcq",
                    "question": "Where are lambdas commonly used?",
                    "options": ["map/filter/sorted key", "As a replacement for classes", "Only in list comprehensions", "To declare global variables"],
                    "answer": 0,
                    "explanation": "They are concise for small functions, often passed to map/filter/sorted."
                },
                {
                    "id": "lambda_mc_3",
                    "type": "mcq",
                    "question": "Which statement is true about lambda in Python?",
                    "options": ["Can contain multiple statements", "Always named", "Is an expression that returns a function", "Creates a new module"],
                    "answer": 2,
                    "explanation": "Lambda is an expression that evaluates to a function object."
                },
            ]
        }
        with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(sample_questions, f, indent=2)
    if not os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            initial = {}
            json.dump(initial, f, indent=2)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_user_data():
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# Basic small-talk/chat restriction to learning topics
ALLOWED_CHAT_KEYWORDS = [
    "python", "function", "functions", "class", "classes", "object", "oop", "list", "tuple", "dictionary", "dict",
    "set", "lambda", "anonymous", "loop", "for", "while", "if", "else", "recursion", "method", "inheritance"
]

def sanitize_input(s):
    return s.strip()

def chat_is_allowed(message):
    msg = message.lower()
    for kw in ALLOWED_CHAT_KEYWORDS:
        if kw in msg:
            return True
    return False
    

def basic_chat_response(message):
    m = message.lower()
    if "oop" in m or "class" in m or "object" in m or "inherit" in m:
        return ("Object-oriented programming (OOP) organizes code into classes and objects. "
                "Classes define attributes (data) and methods (functions). Use inheritance to derive new classes.")
    if "lambda" in m or "anonymous" in m:
        return ("A lambda is a small anonymous function defined with lambda args: expression. "
                "Example: lambda x: x*2. Use for short functions passed as arguments.")
    if "set" in m:
        return ("Sets are unordered collections of unique elements. Use set operations like union (|), intersection (&), "
                "difference (-).")
    if "dict" in m or "dictionary" in m:
        return ("Dictionaries map keys to values. Use d[key] or d.get(key) to access values. Keys must be hashable.")
    if "list" in m or "tuple" in m:
        return ("Lists are ordered mutable sequences; tuples are ordered immutable sequences. Use list methods like append/pop.")
    if "recursion" in m:
        return ("Recursion is when a function calls itself. Always ensure a base case to prevent infinite recursion.")
    if "map" in m or "filter" in m:
        return ("map applies a function to each item; filter keeps items where function returns True. Lambdas are often used with them.")
    if "for" in m or "while" in m or "loop" in m:
        return ("Loops (for/while) iterate over sequences or repeat actions. Prefer for-loops over while when iterable available.")
    # fallback
    return ("I can help with Python concepts like functions, classes, lists, dicts, sets, lambdas. "
            "Try asking about a specific topic (e.g., 'How do I use a dictionary?').")

# Encouragement logic
def generate_encouragement(username, users, user_data=None):
    # 1. date input
    if user_data is None:
        user_data = load_user_data()

    messages = []
    is_teacher = username.startswith("Spvr")

    # --- 1: login time ---
    last_login_str = users.get(username, {}).get("last_login")
    if last_login_str:
        try:
            last_login = datetime.datetime.fromisoformat(last_login_str.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.UTC)
            days_since = (now - last_login).days

            if days_since == 0:
                msg = f"🔥 Welcome back today, {username}! Great to see you continuing your Python journey!"
            elif days_since == 1:
                msg = f"🔥 Welcome back, {username}! You're building excellent daily momentum. 💪"
            elif days_since <= 3:
                msg = f"👏 Great to see you again so soon, {username}! Consistency really pays off."
            elif days_since <= 7:
                msg = f"❤️ Welcome back, {username}! Let's pick up right where you left off."
            else:
                msg = f"🌟 Welcome back, {username}! Let's strengthen your skills. Let's go! 🚀"
            messages.append(msg)
        except Exception:
            messages.append("🌟 Welcome back! Let's continue your Python learning journey.")
    else:
        messages.append("🌟 Welcome! Let's build strong Python skills together.")

    # --- 2: user vs teacher ---
    if is_teacher:
        # Teacher-specific
        login_count = users.get(username, {}).get('login_count', 0)
        teacher_msgs = [
            "Thank you for your hard work, Teacher! Your dedication is truly inspiring. ☕",
            "Teaching is challenging yet rewarding. Remember to take care of yourself! 🌟",
            f"You have logged in {login_count} times. Your students are fortunate to have you! 🍎",
            "Thank you for continuously improving the quiz and learning materials! 📝"
        ]
        messages.append(random.choice(teacher_msgs))

    else:
        # Student-specific for user
        ud = user_data.get(username, {})
        quizzes = ud.get("quizzes", [])

        # A. quiz result
        if quizzes:
            last_score = quizzes[-1].get("score_percent")
            if last_score is not None:
                if last_score >= 80:
                    messages.append(f"Excellent! You scored {last_score}% in your last quiz. 🏆")
                elif last_score >= 60:
                    messages.append(f"Good job! {last_score}% is a solid score. 🚀")
                else:
                    messages.append(f"Keep going! {last_score}% is just a starting point. 💪")

        # B. login time
        login_count = users.get(username, {}).get("login_count", 0)
        if login_count >= 3:
            login_variants = [
                f"Impressive dedication! You've logged in {login_count} times. ✨",
                f"Welcome back for the {login_count}th time! 🚀",
                f"Seeing you {login_count} times shows real commitment. 🔥"
            ]
            messages.append(random.choice(login_variants))

        # C. chat time
        chat_count = len(ud.get("chats", []))
        if chat_count >= 1:
            chat_variants = [
                f"You've had {chat_count} chat interactions. Curiosity is your strength! 🗣️",
                f"Love the {chat_count} questions you've asked! 💡",
                f"With {chat_count} chats, you're thinking deeply about Python! 🌟"
            ]
            messages.append(random.choice(chat_variants))

    # --- 3: gerenal ---
    if 'ENCOURAGEMENT_POOL' in globals():
        messages.append(random.choice(ENCOURAGEMENT_POOL))

    # --- return if-else  ---
    if not messages:
        return "Keep going! You're doing great. 🌟"

    return "\n\n".join(messages)


QuizMe_Idx_Asked = []
QuizMe_Idx_Corrected = []
QuizMe_Idx_Wrong = []
QuizMe_Selected_Topic = None

QuizMe_Selected_Ans_type = 0
QuizMe_Selected_Ans_type_correct_arr = 0
QuizMe_Selected_Ans_type_count = 0

QuizMe_UserAnswer = []

import requests

def call_deepseek(prompt):
    api_key = DEEPSEEK_KEY
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "model": "deepseek-chat", # Use "deepseek-reasoner" for DeepSeek-R1
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status() # Check for HTTP errors

        result = response.json()
        return result['choices'][0]['message']['content']

    except Exception as e:
        return f"Error: {str(e)}"

def analyze_python_quiz_answer(topic, question, correct_answer, user_answer):
    api_key = DEEPSEEK_KEY
    url = "https://api.deepseek.com/chat/completions"

    system_instruction = (
        f"You are a friendly Python Mentor. Topic: '{topic}'.\n"
        "Task: Analyze the user's answer. \n\n"
        "RULES:\n"
        "1. If the concept is right (even with typos), set 'result' to true.\n"
        "2. If the concept is wrong, set 'result' to false.\n"
        "3. In the 'reason', address the user naturally and encouragingly. "
        "DO NOT use words like 'student' or 'learner'. Speak like a peer or a helpful colleague. "
        "EXPLICITLY state the correct answer within your feedback.\n\n"
        "RESPONSE FORMAT (JSON ONLY):\n"
        "{\n"
        "  \"result\": boolean,\n"
        "  \"reason\": \"Your natural feedback here.\"\n"
        "}"
    )

    user_content = (
        f"Question: {question}\n"
        f"Correct Answer: {correct_answer}\n"
        f"Student Answer: {user_answer}"
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.5 # 稍微提高一點溫度，讓老師的說話語氣更自然
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        analysis = json.loads(response.json()['choices'][0]['message']['content'])

        return {
            "result": analysis.get("result", False),
            "reason": analysis.get("reason", "Keep trying, you are doing great!")
        }
    except Exception as e:
        return {"result": False, "reason": "I'm having a little trouble checking your work right now, but keep going!"}

def QuizMe_Innitialize():
    global QuizMe_Idx_Asked
    global QuizMe_Idx_Corrected
    global QuizMe_Idx_Wrong
    global QuizMe_Selected_Topic
    QuizMe_Idx_Asked = []
    QuizMe_Idx_Corrected = []
    QuizMe_Idx_Wrong = []
    QuizMe_Selected_Topic = None

def QuizMe_Select_Topic():
    global QuizMe_Selected_Topic
    questions_bank = load_questions()
    topics = list(questions_bank.keys())
    chosen_topics = topics  # use all 3 topics
    print("\nQuiz topics:")
    for i, t in enumerate(chosen_topics, 1):
        print(f"{i}. {t}")

    choice = input("Please select a topic: ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(chosen_topics):
        QuizMe_Selected_Topic = chosen_topics[int(choice) - 1]

        available_questions = QuizMe_Get_Available_Questions_by_Topic(QuizMe_Selected_Topic)

        if len(available_questions) > 0:
            print(f"**** You are selected [{QuizMe_Selected_Topic}] topic! ****")
            return QuizMe_Selected_Topic
        else:
            print(" No available questions for this topic. Please try again.")
            QuizMe_Select_Topic()
    else:
        print("Invalid option. Please try again.")
        QuizMe_Select_Topic()

def QuizMe_Select_Ans_type():
    global QuizMe_Selected_Ans_type
    global QuizMe_Selected_Ans_type_correct_arr
    global QuizMe_Selected_Ans_type_count
    global QuizMe_Selected_Topic

    QuizMe_Selected_Ans_type = 0
    QuizMe_Selected_Ans_type_correct_arr = 0
    QuizMe_Selected_Ans_type_count = 0

    ans_type = [
        "3 Questions Challenge"
        , "5 Questions Challenge"
        , "Change Topic"
        , "Back to menu"
    ]

    print("\nQuiz option for [" + QuizMe_Selected_Topic + "]:")
    for i, t in enumerate(ans_type, 1):
        print(f"{i}. {t}")

    choice = input("Please Select a option(1 - " + str(len(ans_type)) +"): ").strip()

    if choice.isdigit() and 1 <= int(choice) <= len(ans_type):

        choice_int = int(choice)

        if choice_int == 1:
            QuizMe_Selected_Ans_type = 3
            print(f"**** You are selected [{ans_type[choice_int - 1]}] topic! ****")
            return True
        elif choice_int == 2:
            QuizMe_Selected_Ans_type = 5
            print(f"**** You are selected [{ans_type[choice_int - 1]}] topic! ****")
            return True
        elif choice_int == 3:
            print(f"**** Select Topic Again! ****")
            QuizMe_Select_Topic()
            QuizMe_Select_Ans_type()
            return True
        elif choice_int == 4:
            print(f"**** Back To Menu! ****")
            return False
        else:
            print("Invalid option. Please try again.")
            QuizMe_Select_Ans_type()
    else:
        print("Invalid option. Please try again.")
        QuizMe_Select_Ans_type()


def QuizMe_Get_Questions_by_Topic(Topic):
    questions_bank = load_questions()
    if Topic is None:
        # Return all questions from all topics
        all_questions = []
        for qs in questions_bank.values():
            all_questions.extend(qs)
        return all_questions
    else:
        # Return all questions with the specified topic
        qs = questions_bank.get(Topic, [])
        return qs

def QuizMe_Get_Available_Questions_by_Topic(topic):
    global QuizMe_Idx_Asked
    if topic is None:
        return []
    questions_bank = QuizMe_Get_Questions_by_Topic(topic)

    if questions_bank is None:
        return []

    available = [q for q in questions_bank if q.get("id") not in QuizMe_Idx_Asked]
    return available

def QuizMe_All_Questions_Asked():
    global QuizMe_Idx_Asked
    questions_bank = load_questions()
    if not questions_bank:
        print("No questions available")
        return False  # No questions available

    # Flatten all question ids in questions_bank
    if isinstance(questions_bank, dict):
        all_ids = [q.get("id") for topic_questions in questions_bank.values() for q in topic_questions]
    else:
        all_ids = [q.get("id") for q in questions_bank]

    # Filter out the ones that are in QuizMe_Idx_Asked
    not_asked = [qid for qid in all_ids if qid not in QuizMe_Idx_Asked]

    return len(not_asked) == 0


def QuizMe_start(username):
    global QuizMe_Selected_Topic
    global QuizMe_Selected_Ans_type_count
    global QuizMe_Selected_Ans_type_correct_arr
    global QuizMe_Selected_Ans_type
    global QuizMe_Idx_Asked
    global QuizMe_Idx_Corrected
    global QuizMe_Idx_Wrong
    global QuizMe_UserAnswer

    # no question avaiable for ask
    if QuizMe_All_Questions_Asked() == True:
        return False

    questions_bank = QuizMe_Get_Available_Questions_by_Topic(QuizMe_Selected_Topic)

    if not questions_bank or len(questions_bank) == 0:
        QuizMe_Select_Topic()
        questions_bank = QuizMe_Get_Available_Questions_by_Topic(QuizMe_Selected_Topic)

    if not questions_bank:
        return False

    QuizMe_Selected_Ans_type_count += 1

    UserAns = None
    is_Ans_Correct = False

    q = random.choice(questions_bank)
    print(f"[" + QuizMe_Selected_Topic + "] ")
    print(q["question"])

    # MC case
    opt_selection_msg = ""
    if q["type"] == "mcq":
        opt_selection_msg = " (option 1 - " + str(len(q["options"])) + ")"
        for i, opt in enumerate(q["options"], 1):
            print(f"  {i}. {opt}")

    print(f" **** Type 'quit' any time to stop. ****")
    while True:
        resp = input("Please Input Your answer" + opt_selection_msg  +": ").strip()
        if resp.lower() == "quit":
            print("Quiz aborted by user.")
            QuizMe_Selected_Ans_type_count -= 1
            return False

        if q["type"] == "mcq":
            if not resp.isdigit() or not (1 <= int(resp) <= len(q["options"])):
                print("Please enter a valid option number.")
                continue
            UserAns = str(int(resp) - 1)
            break
        else:
            UserAns = resp.strip().lower()
            break

    ai_response_json = None
    if q["type"] == "fill":
        AIrst = analyze_python_quiz_answer(QuizMe_Selected_Topic, q["question"], q["answer"], UserAns)
        ai_response_json = {
            "result": bool(AIrst.get("result", False)),
            "reason": str(AIrst.get("reason", ""))
        }
        is_Ans_Correct = ai_response_json["result"]

    else:
        is_Ans_Correct = (UserAns == str(q["answer"]).lower())

    QuizMe_Idx_Asked.append(q["id"])
    QuizMe_UserAnswer.append({"id": q.get("id"), "given": UserAns, "correct": q["answer"], "topic": QuizMe_Selected_Topic})

# for user
    is_teacher = username.startswith('Spvr')

    is_Ans_Correct = (UserAns == str(q["answer"]).lower())
    QuizMe_Idx_Asked.append(q["id"])

    QuizMe_UserAnswer.append({"id": q.get("id"), "given": UserAns, "correct": q["answer"], "topic": QuizMe_Selected_Topic})

    if is_Ans_Correct:
        QuizMe_Selected_Ans_type_correct_arr += 1
        QuizMe_Idx_Corrected.append(q["id"])

        # --- teachrt vs user: if right ---
        if is_teacher:
            teacher_pos = [
                "Perfect as always, Teacher! You're a true Python master. 🎓",
                "Spot on! Your expertise is showing. ✨",
                "Flawless! A perfect demonstration for the students. 🍎"
            ]
            print(f"\n**** ✅ {random.choice(teacher_pos)} ****")
        else:
            print("\n**** ✅ Correct! Well done!")

        if q["type"] == "fill":
          ai_message = ai_response_json["reason"].replace(".", ".\n****")
          if ai_message.endswith("\n****"):
            ai_message = ai_message[:-1]
          print(f"**** " + ai_message )

    else:
        QuizMe_Idx_Wrong.append(q["id"])

        # show good msg
        if q["type"] == "mcq":
            print(f"\n**** ❌ Incorrect. Correct answer: {q['options'][q['answer']]}")
            print("**** Explanation:", q.get("explanation", "") + "")
        else:
            print(f"\n**** ❌ Incorrect. ")
            ai_message = ai_response_json["reason"].replace(".", ".\n****")
            if ai_message.endswith("\n****"):
              ai_message = ai_message[:-1]
            print(f"**** " + ai_message )

        # --- teachrt vs user: if wrong ---
        if is_teacher:
            teacher_neg = [
                "Oops! Was that a 'teaching demonstration' of a common mistake? 😜",
                "Even masters have a 'glitch' sometimes! Testing the system, Teacher? 🛠️",
                "A rare slip! But we know you were just checking if the answer key works. 😏"
            ]
            print(f"**** {random.choice(teacher_neg)} ****")
        else:
            # user following mark
            wrong_percentage = ((QuizMe_Selected_Ans_type_count - QuizMe_Selected_Ans_type_correct_arr) / QuizMe_Selected_Ans_type) * 100
            if wrong_percentage >= 66:
                print("**** 🌱 Don't worry at all! It's completely normal to struggle at first. ****")
            elif wrong_percentage >= 50:
                print("**** 🌟 It's okay! Mistakes help us learn faster. ****")
            else:
                print("**** 🌱 Keep going! One wrong answer doesn't define your ability. ****")

    return True


def chat_with_ai():
    print("--- AI Chat Started (Type '-999' to exit) ---")
    while True:
        user_input = input("\nYou: ").strip()

        # 1. Check for exit command first
        if user_input == "-999":
            print("Exiting chat... Goodbye!")
            break

        # 2. Prevent empty prompts from wasting API credits
        if not user_input:
            continue

        # 3. Call the AI inside the loop so it responds to EACH input
        print("Thinking...")
        answer = call_deepseek(user_input)

        # 4. Display the result
        print(f"DeepSeek says: {answer}")

    return -999

# Quiz mechanics
def run_quiz(username):
    global QuizMe_Selected_Ans_type
    global QuizMe_Idx_Asked
    global QuizMe_Idx_Corrected
    global QuizMe_Idx_Wrong
    global QuizMe_UserAnswer

    QuizMe_Innitialize()

    QuizMe_Select_Topic()

    # if return false mean end the quiz
    Ans_type_TF = QuizMe_Select_Ans_type()

    if Ans_type_TF == False:
        return -999

    QuizMe_UserAnswer = []
    for i in range(QuizMe_Selected_Ans_type):
        print(f"\n--- Question {i+1} of {QuizMe_Selected_Ans_type} ---")
        Quiz_rst = QuizMe_start(username)
        if Quiz_rst == False:
            break

    # Assuming these are set from your previous logic
    total_questions = QuizMe_Selected_Ans_type #
    correct_count = QuizMe_Selected_Ans_type_correct_arr
    success_rate = (correct_count / total_questions * 100) if total_questions > 0 else 0
    rounded_rate = round(success_rate)

    # store to user_data
    user_data = load_user_data()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    entry = {
        "timestamp": now,
        "score": correct_count,
        "total": total_questions,
        "score_percent": round(success_rate, 2),
        "answers": QuizMe_UserAnswer
    }
    if username not in user_data:
        user_data[username] = {"quizzes": [], "chats": []}
    user_data[username].setdefault("quizzes", []).append(entry)
    save_user_data(user_data)
    QuizMe_UserAnswer = []

    print(f"\n\n ==================== Quiz Result ====================")
    print(f"📈 Your Rate: " + str(correct_count) + "/" +  str(total_questions) + " (" + str(round(success_rate, 2)) + "%)")

    # --- Optimized Feedback for Short Quizzes ---
    if rounded_rate == 100:
        rank_comment = "Perfect! You're a Master! 👑"

    elif rounded_rate >= 75:
        # Catch: 4/5 (80%)
        rank_comment = "So close! Just one tiny mistake. 🌟"

    elif rounded_rate >= 60:
        # Catch: 2/3 (67%) or 3/5 (60%)
        rank_comment = "Good job! You passed the majority. 👍"

    elif rounded_rate >= 40:
        # Catch: 2/5 (40%)
        rank_comment = "Not bad, but you might need a quick review. 📚"

    else:
        # Catch: 0% or 1/3 (33%) or 1/5 (20%)
        rank_comment = "Keep practicing! You'll get better next time. 💪"

    print(f"💬 Feedback: {rank_comment}")

    return rounded_rate

    questions_bank = load_questions()
    topics = list(questions_bank.keys())
    chosen_topics = topics  # use all 3 topics
    print("\nQuiz topics:")
    for i, t in enumerate(chosen_topics, 1):
        print(f"{i}. {t}")
    # For each topic, present 3 questions
    selected_questions = []
    for t in chosen_topics:
        qs = questions_bank.get(t, [])
        # choose up to 3 questions per topic
        pick = min(3, len(qs))
        chosen = random.sample(qs, pick)
        # keep reference of topic
        for q in chosen:
            q_copy = q.copy()
            q_copy["topic"] = t
            selected_questions.append(q_copy)
    # Shuffle overall
    random.shuffle(selected_questions)
    score = 0
    total = len(selected_questions)
    user_answers = []
    print("\nStarting quiz. Type 'quit' any time to stop.\n")
    for idx, q in enumerate(selected_questions, 1):
        print(f"Question {idx}/{total} [{q['topic']}]")
        print(q["question"])
        if q["type"] == "mcq":
            for i, opt in enumerate(q["options"], 1):
                print(f"  {i}. {opt}")
            ans = None
            while True:
                resp = input("Your answer (number): ").strip()
                if resp.lower() == "quit":
                    print("Quiz aborted by user.")
                    break
                if not resp.isdigit() or not (1 <= int(resp) <= len(q["options"])):
                    print("Please enter a valid option number.")
                    continue
                ans = int(resp) - 1
                break
            if ans is None:
                break
            correct = (ans == q["answer"])
            if correct:
                print("✅ Correct! Well done!")
                if score + 1 == total:   # correct last question
                    print("🎉 You're on fire! Amazing job finishing strong!")
                elif score >= 3:         # if correct 3 time
                    print("Fantastic! You're really getting the hang of this!")
                else:
                    print("Great job! Keep this momentum going! 🔥")
                print("Explanation:", q.get("explanation", "No explanation provided."))
                score += 1
            else:
                wrong_count = (idx - score)   # no. of wrong
                if wrong_count >= 3:
                    print(f"Incorrect. Correct answer: {q['options'][q['answer']]}")
                    print("Explanation:", q.get("explanation", ""))
                    print("🌱 Don't worry at all! It's completely normal to struggle at first.")
                    print("Many successful programmers failed many times before they succeeded.")
                elif wrong_count >= 2:
                    print(f"Incorrect. Correct answer: {q['options'][q['answer']]}")
                    print("Explanation:", q.get("explanation", ""))
                    print("🌟 It's okay! Mistakes help us learn faster.")
                    print("Let's turn this into progress on the next question.")
                else:
                    print(f"Incorrect. Correct answer: {q['options'][q['answer']]}")
                    print("Explanation:", q.get("explanation", ""))
                    print("🌱 Keep going! One wrong answer doesn't define your ability.")
                    print("Every mistake teaches us something important.")
                print("")
            user_answers.append({"id": q.get("id"), "given": ans, "correct": q["answer"], "topic": q["topic"]})
        elif q["type"] == "fill":
            resp = input("Your answer (text): ").strip()
            if resp.lower() == "quit":
                print("Quiz aborted by user.")
                break
            # basic normalization
            ans_text = resp.strip().lower()
            correct_text = str(q["answer"]).strip().lower()
            correct = (ans_text == correct_text)
            if correct:
                print("Correct!")
                score += 1
            else:
                print(f"Incorrect. Correct answer: {q['answer']}")
            print("Explanation:", q.get("explanation", ""))
            user_answers.append({"id": q.get("id"), "given_text": resp, "correct_text": q["answer"], "topic": q["topic"]})
        else:
            print("Unknown question type; skipping.")
    # Save quiz result
    percent = round((score / total) * 100) if total > 0 else 0
    print(f"\nQuiz completed. Score: {score}/{total} ({percent}%)\n")
    # store to user_data
    user_data = load_user_data()
    now = datetime.datetime.now(datetime.UTC).isoformat()
    entry = {"timestamp": now, "score": score, "total": total, "score_percent": percent, "answers": user_answers}
    if username not in user_data:
        user_data[username] = {"quizzes": [], "chats": []}
    user_data[username].setdefault("quizzes", []).append(entry)
    save_user_data(user_data)
    print(f"✅ Score {percent}% saved successfully.")
    # Provide encouraging feedback
    if percent >= 80:
        print("Great job! You're mastering these topics.")
    elif percent >= 50:
        print("Good effort — identify weak areas and try again.")
    else:
        print("Keep practicing — review the resources and retry.")
    return percent

def register_chat(username, message):
    ud = load_user_data()
    if username not in ud:
        ud[username] = {"quizzes": [], "chats": []}
    ud[username].setdefault("chats", []).append({"timestamp": datetime.datetime.utcnow().isoformat(), "message": message})
    save_user_data(ud)

def reset_password(username):
    """Reset a user's password back to their username (default)."""
    users = load_users()
    if username in users:
        users[username]["password"] = username
        save_users(users)
        print(f"✅ Password for {username} has been reset to '{username}'.")
        return True
    else:
        print("User not found.")
        return False


def change_password(username):
    """Allow logged-in user to change their own password with rules and strength indicator."""
    users = load_users()
    print(f"\n=== Change Password for {username} ===")

    # Step 1: Verify current password
    try:
        old_pass = getpass.getpass("Enter current password: ")
    except:
        old_pass = input("Enter current password: ")

    if old_pass != users[username]["password"]:
        print("❌ Incorrect current password.")
        return False

    print("\n📋 **Password Requirements:**")
    print("   • Minimum 6 characters")
    print("   • At least 1 capital letter (A-Z)")
    print("   • Only letters (A-Z, a-z) and digits (0-9) allowed")
    print("   • No symbols (!@#$ etc.) permitted\n")

    # Step 2: Get and validate new password
    while True:
        try:
            new_pass1 = getpass.getpass("Enter new password: ")
        except:
            new_pass1 = input("Enter new password: ")

        # Calculate password strength
        strength = get_password_strength(new_pass1)

        if strength == "Weak":
            print("❌ Weak password. Please make it stronger.")
            print("   Suggestion: Use at least 6+ characters with 1 capital letter.")
            continue

        # Detailed validation
        if len(new_pass1) < 6:
            print("❌ Password must be at least 6 characters long.")
            continue

        if not any(char.isupper() for char in new_pass1):
            print("❌ Password must include at least 1 capital letter (A-Z).")
            continue

        if not new_pass1.isalnum():   # Only letters and digits
            print("❌ No symbols allowed. Only letters and digits (0-9) are permitted.")
            continue

        # Show strength feedback
        print(f"🔒 Password Strength: **{strength}**")

        # Confirm password
        try:
            new_pass2 = getpass.getpass("Confirm new password: ")
        except:
            new_pass2 = input("Confirm new password: ")

        if new_pass1 != new_pass2:
            print("❌ Passwords do not match. Please try again.")
            continue

        # All checks passed
        users[username]["password"] = new_pass1
        save_users(users)
        print("\n✅ Password changed successfully!")
        print(f"   Your new password is **{strength}** and meets all requirements.")
        return True


# ====================== HELPER FUNCTION ======================
def get_password_strength(password):
    """Return password strength: Weak, Medium, or Strong"""
    if len(password) < 6:
        return "Weak"

    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    length_ok = len(password) >= 8

    if has_upper and has_digit and length_ok:
        return "Strong"
    elif has_upper or has_digit:
        return "Medium"
    else:
        return "Weak"

# ====================== DELETION LOG ======================
def ensure_delete_log_exists():
    """Create delete_log.json if it doesn't exist."""
    if not os.path.exists(DELETE_LOG_FILE):
        with open(DELETE_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)  # empty list of logs

def log_deletion(deleted_by, deleted_user, reason):
    """Record deletion permanently in delete_log.json"""
    ensure_delete_log_exists()

    log_entry = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "deleted_by": deleted_by,
        "deleted_user": deleted_user,
        "reason": reason.strip()
    }

    with open(DELETE_LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    logs.append(log_entry)

    with open(DELETE_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)

    print(f"📝 Deletion logged successfully for user '{deleted_user}'.")


    # ====================== VIEW LOGS (Supervisor Only) ======================
def view_deletion_log():
    """Display the permanent deletion log."""
    print("\n=== Deletion Log ===")
    ensure_delete_log_exists()

    with open(DELETE_LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    if not logs:
        print("No deletions recorded yet.")
        return

    print(f"Total deletions recorded: {len(logs)}\n")
    for i, entry in enumerate(logs, 1):
        ts = entry["timestamp"][:19].replace("T", " ")
        print(f"{i:2d}. [{ts}]")
        print(f"   Deleted by : {entry['deleted_by']}")
        print(f"   User deleted: {entry['deleted_user']}")
        print(f"   Reason     : {entry['reason']}")
        print("-" * 60)


def view_user_activity_log():
    """Display summary of all users' activity."""
    print("\n=== User Activity Log ===")
    users = load_users()
    user_data = load_user_data()

    if not users:
        print("No users found.")
        return

    print(f"{'Username':<12} {'Role':<10} {'Logins':<6} {'Quizzes':<7} {'Chats':<6} {'Avg Score':<10}")
    print("-" * 65)

    for username, info in sorted(users.items()):
        role = info.get("role", "unknown")
        login_count = info.get("login_count", 0)

        ud = user_data.get(username, {})
        quizzes = ud.get("quizzes", [])
        chats = ud.get("chats", [])

        quiz_count = len(quizzes)
        chat_count = len(chats)

        # Calculate average quiz score
        scores = [q.get("score_percent", 0) for q in quizzes]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0

        print(f"{username:<12} {role:<10} {login_count:<6} {quiz_count:<7} {chat_count:<6} {avg_score:>8.1f}%")

    print("\n💡 Tip: This shows real learning activity across all users.")

# ====================== ADMIN FUNCTIONS (Teacher only) ======================
def register_new_user():
    """Teacher-only: Register a new user (student or teacher)."""
    print("\n=== Register New User ===")
    print("Only teachers can register new users.")

    username = input("Enter new username (e.g. Emp004 or SpvrB06): ").strip()

    if not username:
        print("❌ Username cannot be empty.")
        return False

    users = load_users()
    if username in users:
        print(f"❌ Username '{username}' already exists.")
        return False

    # Ask for role
    print("\nSelect role:")
    print("1. Student (Empxxx)")
    print("2. Teacher/Supervisor (SpvrBxx)")
    role_choice = input("Choose 1 or 2: ").strip()

    role = "student" if role_choice == "1" else "teacher"

    # Set initial password = username (as per original requirement)
    initial_password = username

    # Add to users.json
    users[username] = {
        "password": initial_password,
        "role": role,
        "login_count": 0,
        "last_login": None,
        "show_news": True if role == "student" else False
    }
    save_users(users)

    # Initialize empty data in user_data.json
    user_data = load_user_data()
    if username not in user_data:
        user_data[username] = {"quizzes": [], "chats": []}
        save_user_data(user_data)

    print(f"\n✅ User '{username}' successfully registered!")
    print(f"   Role: {role}")
    print(f"   Initial Password: {initial_password} (same as username)")
    print("   User can change password after first login.")
    return True


def delete_user_with_reason(current_user):
    """Teacher-only: Delete a user and record reason in permanent log."""
    print("\n=== Delete User (with Reason) ===")
    print("Only teachers can delete users.")

    username_to_delete = input("Enter username to delete: ").strip()

    users = load_users()
    if username_to_delete not in users:
        print(f"❌ User '{username_to_delete}' not found.")
        return False

    # Safety: Prevent deleting the last supervisor
    supervisors = [u for u, data in users.items() if data.get("role") == "teacher"]
    if users[username_to_delete].get("role") == "teacher" and len(supervisors) <= 1:
        print("❌ Cannot delete the last teacher for security reasons.")
        return False

    print(f"\n⚠️  You are about to **permanently delete** user: {username_to_delete}")
    print("   This action cannot be undone.")

    reason = input("\nEnter reason for deletion (required): ").strip()
    if not reason:
        print("❌ Reason is required.")
        return False

    # Final confirmation
    confirm = input(f"\nType 'DELETE {username_to_delete}' to confirm: ").strip()
    if confirm != f"DELETE {username_to_delete}":
        print("❌ Confirmation failed. Deletion cancelled.")
        return False

    # Log the deletion BEFORE actually deleting
    log_deletion(deleted_by=current_user, deleted_user=username_to_delete, reason=reason)

    # Delete from users.json
    del users[username_to_delete]
    save_users(users)

    # Delete from user_data.json if exists
    user_data = load_user_data()
    if username_to_delete in user_data:
        del user_data[username_to_delete]
        save_user_data(user_data)

    print(f"\n✅ User '{username_to_delete}' has been permanently deleted.")
    print(f"   Reason: {reason}")
    return True

def ensure_materials_exist():
    """Create materials.json with full lesson content if it doesn't exist."""
    if not os.path.exists(MATERIALS_FILE):
        learning_materials = {
            "Lesson 1: Sets": {
                "description": "A set is an unordered collection of UNIQUE elements. Duplicates are automatically removed. Sets are mutable but their elements must be immutable (hashable).",
                "key_concepts": [
                    "Sets use curly braces { } but unlike dicts, they have no key:value pairs",
                    "Elements are unique — adding a duplicate has no effect",
                    "Sets are unordered — you cannot access elements by index",
                    "union (|): all elements from both sets",
                    "intersection (&): only elements in BOTH sets",
                    "difference (-): elements in A but NOT in B",
                    "symmetric difference (^): elements in either but NOT both"
                ],
                "examples": [
                    "# Creating a set",
                    "s = {1, 2, 3, 4}",
                    "s2 = set([1, 2, 2, 3])   # → {1, 2, 3}  (duplicates removed)",
                    "",
                    "# Adding / removing",
                    "s.add(5)                  # adds 5",
                    "s.discard(10)             # removes 10 (no error if missing)",
                    "s.remove(1)               # removes 1 (raises KeyError if missing)",
                    "",
                    "# Set operations",
                    "a = {1, 2, 3}",
                    "b = {2, 3, 4}",
                    "print(a | b)              # union        → {1, 2, 3, 4}",
                    "print(a & b)              # intersection → {2, 3}",
                    "print(a - b)              # difference   → {1}",
                    "print(a ^ b)              # sym. diff    → {1, 4}",
                    "",
                    "# Membership test (very fast!)",
                    "print(2 in a)             # → True"
                ],
                "common_mistakes": [
                    "empty_set = {}   # ❌ WRONG — this creates an empty DICT, not a set",
                    "empty_set = set()          # ✅ CORRECT",
                    "s = {[1,2]}                # ❌ TypeError — lists are unhashable (mutable)",
                    "s = {(1,2)}                # ✅ OK — tuples are hashable"
                ],
                "resources": [
                    {"type": "Video", "title": "Python Sets Tutorial",
                     "link": "https://youtu.be/r3R3h5ly_8g"},
                    {"type": "Docs",  "title": "Official Set Docs",
                     "link": "https://docs.python.org/3/tutorial/datastructures.html#sets"}
                ]
            },
            "Lesson 2: Dictionaries": {
                "description": "A dictionary stores data as key-value pairs. Keys must be unique and immutable. Dictionaries are ordered (Python 3.7+) and mutable.",
                "key_concepts": [
                    "Keys must be immutable: strings, numbers, or tuples (not lists)",
                    "Values can be anything: strings, numbers, lists, even other dicts",
                    "d[key] raises KeyError if key missing; d.get(key) returns None safely",
                    "d.keys() → all keys,  d.values() → all values,  d.items() → key-value pairs",
                    "d.update({...}) merges another dict into d",
                    "d.pop(key) removes the key and returns its value",
                    "del d[key] removes the key (no return value)"
                ],
                "examples": [
                    "# Creating a dictionary",
                    "student = {'name': 'Alice', 'age': 20, 'grade': 'A'}",
                    "",
                    "# Accessing values",
                    "print(student['name'])              # → 'Alice'",
                    "print(student.get('score', 0))      # → 0  (safe, no KeyError)",
                    "",
                    "# Adding / updating",
                    "student['email'] = 'alice@example.com'   # add new key",
                    "student['age'] = 21                      # update existing key",
                    "",
                    "# Removing",
                    "student.pop('grade')                # removes 'grade', returns 'A'",
                    "del student['email']                # removes 'email'",
                    "",
                    "# Looping",
                    "for key, value in student.items():",
                    "    print(f'{key}: {value}')",
                    "",
                    "# Dict comprehension",
                    "squares = {x: x**2 for x in range(1, 6)}",
                    "# → {1:1, 2:4, 3:9, 4:16, 5:25}"
                ],
                "common_mistakes": [
                    "d['missing_key']            # ❌ KeyError — use d.get('missing_key') instead",
                    "d = {'a': 1, 'a': 2}        # ❌ Duplicate key — second value overwrites first → {'a': 2}",
                    "d = {[1,2]: 'val'}          # ❌ TypeError — lists cannot be keys (not hashable)",
                    "for k in d: del d[k]        # ❌ RuntimeError — never modify dict size while looping"
                ],
                "resources": [
                    {"type": "Video", "title": "Dictionaries Explained",
                     "link": "https://youtu.be/daefaLgNkw0"},
                    {"type": "Docs",  "title": "Official Dict Docs",
                     "link": "https://docs.python.org/3/tutorial/datastructures.html#dictionaries"}
                ]
            },
            "Lesson 3: Anonymous Functions (Lambda)": {
                "description": "A lambda is a small, anonymous (unnamed) function defined in a single line. It is useful for short operations passed as arguments to functions like map(), filter(), and sorted().",
                "key_concepts": [
                    "Syntax: lambda arguments: expression",
                    "A lambda can take multiple arguments but has only ONE expression",
                    "It returns the result of the expression automatically (no 'return' keyword)",
                    "Use lambdas for short, throwaway functions — use def for anything complex",
                    "map(func, iterable): applies func to every element",
                    "filter(func, iterable): keeps elements where func returns True",
                    "sorted(iterable, key=func): sorts using func as the sort key"
                ],
                "examples": [
                    "# Basic lambda",
                    "double = lambda x: x * 2",
                    "print(double(5))                    # → 10",
                    "",
                    "# Lambda with multiple arguments",
                    "add = lambda x, y: x + y",
                    "print(add(3, 4))                    # → 7",
                    "",
                    "# Using with sorted()",
                    "students = [('Alice', 85), ('Bob', 92), ('Carol', 78)]",
                    "by_score = sorted(students, key=lambda s: s[1])",
                    "# → [('Carol', 78), ('Alice', 85), ('Bob', 92)]",
                    "",
                    "# Using with map()",
                    "nums = [1, 2, 3, 4]",
                    "doubled = list(map(lambda x: x * 2, nums))",
                    "# → [2, 4, 6, 8]",
                    "",
                    "# Using with filter()",
                    "evens = list(filter(lambda x: x % 2 == 0, nums))",
                    "# → [2, 4]"
                ],
                "common_mistakes": [
                    "f = lambda x: return x*2    # ❌ SyntaxError — no 'return' in lambda",
                    "f = lambda x: x*2; x+1     # ❌ Cannot have multiple expressions",
                    "f = lambda x:\\n    x*2     # ❌ Cannot span multiple lines",
                    "# ✅ For complex logic, use def instead of lambda"
                ],
                "resources": [
                    {"type": "Video", "title": "Python Lambda Functions",
                     "link": "https://youtu.be/25ovCm9jKfA"},
                    {"type": "Docs",  "title": "Official Lambda Docs",
                     "link": "https://docs.python.org/3/reference/expressions.html#lambda"}
                ]
            },
            "Lesson 4: Lists & Tuples": {
                "description": "Lists are ordered, mutable sequences. Tuples are ordered, immutable sequences. Both support indexing and slicing. Use lists when data may change; use tuples for fixed data.",
                "key_concepts": [
                    "Lists use [ ] — mutable (can add, remove, change elements)",
                    "Tuples use ( ) — immutable (cannot be changed after creation)",
                    "Indexing: lst[0] = first item, lst[-1] = last item",
                    "Slicing: lst[start:stop:step] — stop is exclusive",
                    "List methods: append(), extend(), insert(), remove(), pop(), sort(), reverse()",
                    "len(lst) → number of elements",
                    "List comprehension: [expr for item in iterable if condition]"
                ],
                "examples": [
                    "# List basics",
                    "fruits = ['apple', 'banana', 'cherry']",
                    "print(fruits[0])        # → 'apple'",
                    "print(fruits[-1])       # → 'cherry'",
                    "print(fruits[0:2])      # → ['apple', 'banana']",
                    "",
                    "# Modifying lists",
                    "fruits.append('mango')          # add to end",
                    "fruits.insert(1, 'blueberry')   # insert at index 1",
                    "fruits.remove('banana')         # remove by value",
                    "popped = fruits.pop()           # remove & return last item",
                    "fruits.sort()                   # sort in place",
                    "",
                    "# List comprehension",
                    "squares = [x**2 for x in range(1, 6)]",
                    "# → [1, 4, 9, 16, 25]",
                    "",
                    "evens = [x for x in range(10) if x % 2 == 0]",
                    "# → [0, 2, 4, 6, 8]",
                    "",
                    "# Tuple basics",
                    "coords = (10, 20)",
                    "x, y = coords               # tuple unpacking",
                    "print(x, y)                 # → 10  20"
                ],
                "common_mistakes": [
                    "lst = [1,2,3]; lst[5]        # ❌ IndexError — index out of range",
                    "t = (1, 2, 3); t[0] = 99    # ❌ TypeError — tuples are immutable",
                    "lst.append([4, 5])           # ⚠️ Adds ONE nested list — use extend() to add multiple items",
                    "lst2 = lst                   # ⚠️ Both point to SAME list — use lst.copy() for a true copy"
                ],
                "resources": [
                    {"type": "Video", "title": "Python Lists & Tuples Tutorial",
                     "link": "https://youtu.be/W8KRzm-HUcc"},
                    {"type": "Docs",  "title": "Official Lists Docs",
                     "link": "https://docs.python.org/3/tutorial/datastructures.html#more-on-lists"}
                ]
            },
            "Lesson 5: Loops (for / while)": {
                "description": "Loops repeat a block of code. Use for-loops when you know how many times to iterate. Use while-loops when you repeat until a condition becomes False.",
                "key_concepts": [
                    "for loop: iterates over any iterable (list, string, range, dict...)",
                    "range(stop), range(start, stop), range(start, stop, step)",
                    "while loop: runs as long as condition is True — always ensure it can become False!",
                    "break: immediately exits the loop",
                    "continue: skips the rest of the current iteration, goes to next",
                    "else on loop: runs after loop finishes normally (not after break)",
                    "enumerate(iterable): gives (index, value) pairs in a for loop",
                    "zip(a, b): iterates over two lists in parallel"
                ],
                "examples": [
                    "# for loop with range",
                    "for i in range(5):",
                    "    print(i)             # 0 1 2 3 4",
                    "",
                    "# for loop over list",
                    "fruits = ['apple', 'banana', 'cherry']",
                    "for fruit in fruits:",
                    "    print(fruit)",
                    "",
                    "# enumerate — get index AND value",
                    "for i, fruit in enumerate(fruits):",
                    "    print(f'{i}: {fruit}')",
                    "",
                    "# while loop",
                    "count = 0",
                    "while count < 5:",
                    "    print(count)",
                    "    count += 1",
                    "",
                    "# break and continue",
                    "for n in range(10):",
                    "    if n == 3: continue   # skip 3",
                    "    if n == 7: break      # stop at 7",
                    "    print(n)              # prints 0,1,2,4,5,6",
                    "",
                    "# zip — loop two lists together",
                    "names = ['Alice', 'Bob']",
                    "scores = [85, 92]",
                    "for name, score in zip(names, scores):",
                    "    print(f'{name}: {score}')"
                ],
                "common_mistakes": [
                    "while True: print('hi')    # ❌ Infinite loop — no break or condition change!",
                    "for i in range(5): i = 10  # ❌ Reassigning i doesn't change loop — range still controls it",
                    "lst = [1,2,3]; for x in lst: lst.remove(x)  # ❌ Never modify a list while looping over it"
                ],
                "resources": [
                    {"type": "Video", "title": "Python Loops Tutorial",
                     "link": "https://youtu.be/6iF8Xb7Z3wQ"},
                    {"type": "Docs",  "title": "Official Loops Docs",
                     "link": "https://docs.python.org/3/tutorial/controlflow.html#for-statements"}
                ]
            },
            "Lesson 6: Functions & Recursion": {
                "description": "Functions group reusable code under a name. Recursion is when a function calls itself to solve a smaller version of the same problem. Every recursive function MUST have a base case.",
                "key_concepts": [
                    "def name(params): defines a function",
                    "return sends a value back to the caller (None if omitted)",
                    "Parameters can have default values: def greet(name='World')",
                    "Scope: variables inside a function are LOCAL — invisible outside",
                    "global keyword: access a module-level variable from inside a function",
                    "Recursion: a function calls itself with a simpler input",
                    "Base case: the condition that stops recursion (REQUIRED)",
                    "Recursive case: the step that moves toward the base case"
                ],
                "examples": [
                    "# Basic function",
                    "def greet(name='World'):",
                    "    return f'Hello, {name}!'",
                    "",
                    "print(greet())            # → 'Hello, World!'",
                    "print(greet('Alice'))     # → 'Hello, Alice!'",
                    "",
                    "# Multiple return values (as tuple)",
                    "def min_max(lst):",
                    "    return min(lst), max(lst)",
                    "",
                    "lo, hi = min_max([3, 1, 4, 1, 5])",
                    "print(lo, hi)             # → 1  5",
                    "",
                    "# Recursion — Factorial",
                    "def factorial(n):",
                    "    if n == 0:            # ← BASE CASE (stops recursion)",
                    "        return 1",
                    "    return n * factorial(n - 1)   # ← RECURSIVE CASE",
                    "",
                    "print(factorial(5))       # → 120",
                    "# How it works: 5 * 4 * 3 * 2 * 1 * 1",
                    "",
                    "# Recursion — Fibonacci",
                    "def fib(n):",
                    "    if n <= 1: return n   # base cases: fib(0)=0, fib(1)=1",
                    "    return fib(n-1) + fib(n-2)",
                    "",
                    "print(fib(7))             # → 13"
                ],
                "common_mistakes": [
                    "def add(a, b): a + b     # ❌ Missing return — function returns None",
                    "def f(n): return f(n-1)  # ❌ No base case → RecursionError (infinite recursion)",
                    "x = 10\ndef f(): x = 99  # ⚠️ Creates LOCAL x — original x unchanged",
                    "def f(): global x; x=99  # ✅ Use global keyword to modify outer variable"
                ],
                "resources": [
                    {"type": "Video", "title": "Python Functions & Recursion Tutorial",
                     "link": "https://youtu.be/9Os0o3wzS_I"},
                    {"type": "Docs",  "title": "Official Functions Docs",
                     "link": "https://docs.python.org/3/tutorial/controlflow.html#defining-functions"}
                ]
            },
            "Lesson 7: Object-Oriented Programming (OOP)": {
                "description": "OOP organizes code into classes (blueprints) and objects (instances). It models real-world entities with attributes (data) and methods (behaviours). Key principles: Encapsulation, Inheritance, Polymorphism.",
                "key_concepts": [
                    "class: a blueprint/template for creating objects",
                    "__init__(self, ...): the constructor — runs when an object is created",
                    "self: refers to the current instance (always the first parameter)",
                    "Attributes: variables that belong to an object (self.name = name)",
                    "Methods: functions that belong to a class",
                    "Inheritance: a child class inherits attributes & methods from a parent",
                    "super(): calls the parent class's method from the child class",
                    "Encapsulation: hiding internal data using _ (convention) or __ (name mangling)"
                ],
                "examples": [
                    "# Define a class",
                    "class Animal:",
                    "    def __init__(self, name, sound):",
                    "        self.name = name        # attribute",
                    "        self.sound = sound",
                    "",
                    "    def speak(self):            # method",
                    "        return f'{self.name} says {self.sound}!'",
                    "",
                    "# Create objects (instances)",
                    "cat = Animal('Cat', 'Meow')",
                    "dog = Animal('Dog', 'Woof')",
                    "print(cat.speak())          # → 'Cat says Meow!'",
                    "print(dog.speak())          # → 'Dog says Woof!'",
                    "",
                    "# Inheritance",
                    "class Dog(Animal):           # Dog inherits from Animal",
                    "    def __init__(self, name, breed):",
                    "        super().__init__(name, 'Woof')   # call parent __init__",
                    "        self.breed = breed               # new attribute",
                    "",
                    "    def fetch(self):          # new method",
                    "        return f'{self.name} fetches the ball!'",
                    "",
                    "buddy = Dog('Buddy', 'Labrador')",
                    "print(buddy.speak())        # inherited → 'Buddy says Woof!'",
                    "print(buddy.fetch())        # own method → 'Buddy fetches the ball!'",
                    "print(buddy.breed)          # → 'Labrador'"
                ],
                "common_mistakes": [
                    "class Dog: def speak(): ...       # ❌ Missing self — always first param of methods",
                    "d = Dog; d.speak()                # ❌ Forgot () — Dog is the class, Dog() creates instance",
                    "class B(A): def __init__(self, x): self.x = x  # ❌ Forgot super().__init__() — parent not initialised",
                    "self.name == name                 # ❌ == is comparison, not assignment — use = to assign"
                ],
                "resources": [
                    {"type": "Video", "title": "Python OOP Tutorial",
                     "link": "https://youtu.be/ZDa-Z5JzLYM"},
                    {"type": "Docs",  "title": "Official OOP Docs",
                     "link": "https://docs.python.org/3/tutorial/classes.html"}
                ]
            }
        }
        with open(MATERIALS_FILE, "w", encoding="utf-8") as f:
            json.dump(learning_materials, f, indent=2)
        print("✅ materials.json created with full lesson content")


def load_materials():
    """Load learning materials from materials.json."""
    with open(MATERIALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ====================== ROLLING NEWS  ======================
def fetch_rolling_news():
    """Always fetch fresh Python & AI news and display in a clean, scannable format."""
    print("\n" + "="*72)
    print("📰 ROLLING NEWS: Latest in Python & Artificial Intelligence")
    print("="*72)
    print("🔄 Fetching fresh headlines...\n")

    headlines = []

    # Sources with reduced limits
    sources = [
        {"name": "Python Blog",     "url": "https://blog.python.org/rss.xml",           "limit": 3},
        {"name": "TechCrunch",      "url": "https://techcrunch.com/feed/",             "limit": 3},
        {"name": "The Verge",       "url": "https://www.theverge.com/rss/index.xml",    "limit": 3},
        {"name": "Ars Technica",    "url": "https://feeds.arstechnica.com/arstechnica/index", "limit": 3},
    ]

    for source in sources:
        try:
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:source["limit"]]:
                title = entry.get("title", "").strip()
                link = entry.get("link", "#")

                # Short date
                published = ""
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        dt = datetime.datetime(*entry.published_parsed[:6])
                        published = f" • {dt.strftime('%b %d')}"
                    except:
                        pass

                if title:
                    headlines.append(f"{title}{published}\n   → {link}")

        except Exception:
            pass  # Skip failed sources silently

    # Limit headlines
    headlines = headlines[:3]

    if headlines:
        for i, headline in enumerate(headlines, 1):
            print(f"{i}. {headline}")
            print()  # spacing between items

    else:
        print("⚠️ Unable to fetch live feeds right now.")
        # print("📌 Recent highlights (as of April 2026):")
        # print("   1. Python 3.15.0a8, 3.14.4 and 3.13.13 released")
        # print("      → https://blog.python.org")
        # print("   2. Meta introduces Muse Spark AI model")
        # print("      → https://ai.meta.com")
        # print("   3. New techniques for more efficient AI training (MIT)")
        # print("      → https://news.mit.edu")

    print("💡 Tip: These headlines refresh live every time you log in.")
    print("   Stay updated on Python releases, AI breakthroughs, and tools!")
    print("="*72 + "\n")

def chat_with_me(username):
    """Full AI chat session; falls back to rule-based chat if USE_AI is False."""
    SYSTEM_PROMPT = (
        "You are a friendly Python programming tutor for PolyU SPEED students. "
        "Keep answers under 5 sentences. Include short Python code examples. "
        "Refuse to answer non-programming topics."
    )
    exit_phrases = ["exit", "quit", "menu", "back", "return", "stop", "leave"]

    print(f"\n{'='*50}\n 🤖 CHAT WITH ME\n{'='*50}")

    # ── Fallback: Rule-based chat when AI is offline ──────────────────
    if not USE_AI:
        print(" 🔄 AI is offline — switching to Basic Chat Mode.")
        print(" 💬 I can still help with Python concepts! (Sets, Dicts, Loops, OOP, Lambda...)")
        print(" 👉 Type 'menu', 'back', or 'exit' to stop chatting.\n")
        while True:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if any(p in user_input.lower() for p in exit_phrases):
                print(" 🚪 Returning to Main Menu...")
                return
            if not chat_is_allowed(user_input):
                print("🚫 Bot: I can only help with Python topics. Try asking about sets, dicts, loops, OOP, or lambdas!")
                continue
            response = basic_chat_response(user_input)
            print(f"🤖 Bot: {response}\n")
            register_chat(username, user_input)
        return

    # ── AI Mode: DeepSeek ─────────────────────────────────────────────
    print(" 🤖 DeepSeek AI connected! Ask me anything about Python.")
    print(" 👉 Type 'menu', 'back', or 'exit' to stop chatting.\n")

    chat_history = []
    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue
        if any(p in user_input.lower() for p in exit_phrases):
            print(" 🚪 Returning to Main Menu...")
            break

        # ── Topic guard: block non-Python questions ───────────────────
        if not chat_is_allowed(user_input):
            print("🚫 Bot: I can only help with Python programming topics. Try asking about sets, dicts, loops, OOP, or lambdas!\n")
            continue

        print("\n🤖 DeepSeek AI thinking...")
        try:
            chat_history.append({"role": "user", "content": user_input})
            if len(chat_history) > 6:
                chat_history = chat_history[-6:]  # keep last 3 exchanges

            response = ai_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + chat_history,
                max_tokens=350,
                temperature=0.6,
                timeout=30
            )
            reply = response.choices[0].message.content
            print(f"🤖 Bot:\n{reply}\n")
            chat_history.append({"role": "assistant", "content": reply})

            # Log chat to user_data.json
            ud = load_user_data()
            ud.setdefault(username, {"quizzes": [], "chats": []})
            ud[username]["chats"].append({
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),  # ← fixed timezone
                "message": user_input[:100]
            })
            save_user_data(ud)

        except Exception as e:
            print(f"⚠️ AI error: {e}")

# FIXED show_learning_materials — Lesson 1-7 interactive browser

def show_learning_materials():
    """Display Lesson 1-7 with full content: concepts, examples, common mistakes."""
    ensure_materials_exist()
    materials_bank = load_materials()
    lessons = list(materials_bank.keys())

    while True:
        print("\n" + "=" * 60)
        print("  📚  LEARNING MATERIALS  |  Python Course (Lesson 1-7)")
        print("=" * 60)
        for i, lesson_name in enumerate(lessons, 1):
            print(f"  {i}. {lesson_name}")
        print("  0. ← Back to Main Menu")
        print("-" * 60)

        choice = input("Select a lesson (0 to go back): ").strip()

        if choice == "0":
            break

        if not (choice.isdigit() and 1 <= int(choice) <= len(lessons)):
            print("  ❌ Invalid choice. Please enter a number from the list.")
            continue

        lesson_name = lessons[int(choice) - 1]
        lesson = materials_bank[lesson_name]

        # ── Lesson Header ──────────────────────────────────────────────
        print(f"\n{'=' * 60}")
        print(f"  📖  {lesson_name}")
        print(f"{'=' * 60}")
        print(f"\n  {lesson['description']}\n")
        input("  [Press Enter to continue to Key Concepts...]")

        # ── Key Concepts ───────────────────────────────────────────────
        print(f"\n{'─' * 60}")
        print("  🔑  KEY CONCEPTS")
        print(f"{'─' * 60}")
        for concept in lesson.get("key_concepts", []):
            print(f"  • {concept}")
        input("\n  [Press Enter to continue to Code Examples...]")

        # ── Code Examples ──────────────────────────────────────────────
        print(f"\n{'─' * 60}")
        print("  💻  CODE EXAMPLES")
        print(f"{'─' * 60}")
        for line in lesson.get("examples", []):
            if line == "":
                print()
            else:
                print(f"  {line}")
        input("\n  [Press Enter to continue to Common Mistakes...]")

        # ── Common Mistakes ────────────────────────────────────────────
        print(f"\n{'─' * 60}")
        print("  ⚠️   COMMON MISTAKES TO AVOID")
        print(f"{'─' * 60}")
        for mistake in lesson.get("common_mistakes", []):
            print(f"  {mistake}")

        # ── Resources ──────────────────────────────────────────────────
        print(f"\n{'─' * 60}")
        print("  🔗  FURTHER RESOURCES")
        print(f"{'─' * 60}")
        for item in lesson.get("resources", []):
            if item["type"] == "Video":
                icon = "🎬"
            elif item["type"] == "Docs":
                icon = "📄"
            else:
                icon = "💡"
            print(f"  {icon} [{item['type']}] {item['title']}")
            print(f"       → {item['link']}")

        # ── Quiz Suggestion ────────────────────────────────────────────
        print(f"\n{'─' * 60}")
        print("  💡  Ready to test yourself?")
        print("      Go to 'Quiz Me' from the Main Menu to answer")
        print(f"      questions on this topic!")
        print(f"{'─' * 60}")

        input("\n  [Press Enter to go back to lesson list...]")

def show_progress_dashboard(username):
    """Personalized learning progress overview"""
    print(f"\n=== 📊 Learning Progress Dashboard for {username} ===")
    users = load_users()
    user_data = load_user_data()

    info = users.get(username, {})
    ud = user_data.get(username, {})

    login_count = info.get("login_count", 0)
    quizzes = ud.get("quizzes", [])
    chats = ud.get("chats", [])

    quiz_count = len(quizzes)
    chat_count = len(chats)

    scores = [q.get("score_percent", 0) for q in quizzes]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    best_score = max(scores) if scores else 0
    total_questions = sum(q.get("total", 0) for q in quizzes)

    print(f"Login Streak / Total Visits     : {login_count} times")
    print(f"Quizzes Completed              : {quiz_count}")
    print(f"Total Questions Answered       : {total_questions}")
    print(f"Average Score                  : {avg_score}%")
    print(f"Best Score                     : {best_score}%")
    print(f"Chat Interactions              : {chat_count}")

    if quiz_count > 0:
        print(f"\n💡 Keep it up! You're building strong Python foundations.")
    else:
        print("\n🌱 Start your first quiz to see progress here!")

    input("\nPress Enter to return to menu...")

def main_menu(username):
    users = load_users()
    user_data = load_user_data()
    is_supervisor = users[username].get("role") == "teacher"

    while True:
        print("\nMain Menu")
        print("1. 🧐 Quiz me")
        print("2. 🫶 Encourage me")
        print("3. 🤖 Chat with me")
        print("4. 📚 Learning Materials")
        # print("5.  AI Chat" + (" (DeepSeek Active)" if USE_AI else " (❌ No AI)"))  # ← NEW
        print("5. 📰 Toggle Rolling News (" + ("ON" if users.get(username, {}).get("show_news", False) else "OFF") + ")")
        print("6. 🔑 Change Password")
        if is_supervisor:
            print("7. ➕ Register New User")
            print("8. 🗑️ Delete User (with Reason)")
            print("9. 📜 View Deletion Log")
            print("10. 📊 View User Activity Log")
            print("11. 👋 Logout")
            max_choice = 11
        else:
            print("7. 📊 My Progress Dashboard")   # for students
            print("8. 👋 Logout")

            max_choice = 8

        choice = input(f"Choose an option (1-{max_choice}): ").strip()

        if choice == "1":
            percent = run_quiz(username)
            msg = generate_encouragement(username, users)
            print("\n", msg)

        elif choice == "2":
            msg = generate_encouragement(username, users, user_data)
            print("\n", msg)

        elif choice == "3":
          chat_with_me(username) # calls chat_with_me()
            # print("\nChat mode (type 'exit' to return to main menu)...")
            # while True:
            #     msg = input("You: ").strip()
            #     if msg.lower() in ("exit", "quit"):
            #         break
            #     if not chat_is_allowed(msg):
            #         print("Sorry, I can only discuss Python/programming topics.")
            #         continue
            #     register_chat(username, msg)
            #     response = basic_chat_response(msg)
            #     print("Bot:", response)

        elif choice == "4":   # calls show_learning_materials()
            show_learning_materials()

        elif choice == "5":   # Toggle Rolling News
            users = load_users()
            current = users[username].get("show_news", False)
            users[username]["show_news"] = not current
            save_users(users)
            status = "ON" if users[username]["show_news"] else "OFF"
            print(f"📰 Rolling News is now {status} for your future logins.")
            if users[username]["show_news"]:
                fetch_rolling_news()  # show immediately if turned on

        elif choice == "6":   # Change password
            change_password(username)

        elif is_supervisor and choice == "7":
            register_new_user()

        elif choice == "7":
            show_progress_dashboard(username)

        elif is_supervisor and choice == "8":
            delete_user_with_reason(username)   # Pass current supervisor

        elif is_supervisor and choice == "9":
            view_deletion_log()

        elif is_supervisor and choice == "10":
            view_user_activity_log()

        elif (is_supervisor and choice == "11") or (not is_supervisor and choice == "8"):
            print("Logging out...\n")
            break

        else:
            print("Invalid option.")

def login_flow():
    ensure_files_exist()
    users = load_users()
    attempts = 0

    while True:
        print("\n=== Python Learning Chatbot Login ===")
        username = input("Username: ").strip()

        if username.lower() == "exit":
            print("Exiting.")
            return None

        if username not in users:
            print("Unknown username. Try again or type 'exit'.")
            continue

        # Password attempt loop
        while True:
            try:
                password = getpass.getpass("Password: ")
            except Exception:
                password = input("Password: ")

            if password == users[username]["password"]:
              # Successful login
              now = datetime.datetime.now(datetime.UTC).isoformat()

              # Update last_login and login_count
              users[username]["last_login"] = now
              users[username]["login_count"] = users[username].get("login_count", 0) + 1
              save_users(users)

              print(f"\nWelcome back, {username}! Role: {users[username].get('role')}")

              # Show login gap encouragement
              # print(f"\nWelcome back, {username}! Role: {users[username].get('role')}")
              # show_login_gap_encouragement(username, users)
              msg = generate_encouragement(username, users)
              print(msg)

              # Show rolling news if enabled
              if users[username].get("show_news", False):
                  fetch_rolling_news()

              return username

            else:
                # Incorrect password
                attempts += 1
                print(f"\n❌ Incorrect password. ({attempts} attempt(s))")

                if attempts >= 5:
                    print("Too many failed attempts. Exiting.")
                    return None

                print("What would you like to do?")
                print("1. Re-enter password")
                print("2. Reset password to default (same as username)")
                choice = input("Enter 1 or 2: ").strip()

                if choice == "2":
                    # Reset password
                    users[username]["password"] = username
                    save_users(users)
                    print(f"✅ Password has been reset to default: '{username}'")
                    print("You can now login using your username as password.")

                    # Automatically login after reset
                    now = datetime.datetime.now(datetime.UTC).isoformat()
                    users[username]["last_login"] = now
                    users[username]["login_count"] = users[username].get("login_count", 0) + 1
                    save_users(users)

                    print(f"\nWelcome {username}! Role: {users[username].get('role')}")

                    # Show login gap encouragement
                    # show_login_gap_encouragement(username, users)
                    msg = generate_encouragement(username, users)
                    print(msg)

                    # Show rolling news for students (or if user enabled it)
                    if users[username].get("show_news", False):
                        fetch_rolling_news()

                elif choice == "1":
                    continue  # Try password again
                else:
                    print("Invalid choice. Please enter 1 or 2.")
                    continue  # Stay in password loop

def main():
    st.title("🐍 Python Learning Chatbot")
    st.markdown("### Interactive Python Learning Platform")

    # Session state for login
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        col1, col2 = st.columns([1, 2])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                # Add your login logic here (load_users, check password, etc.)
                # For now, placeholder:
                if username and password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
    else:
        username = st.session_state.username
        st.sidebar.success(f"Logged in as: **{username}**")

        menu = st.sidebar.radio("Go to", [
            "Home", "Quiz Me", "Encourage Me", 
            "Chat with Me", "Learning Materials", 
            "Progress Dashboard", "Logout"
        ])

        if menu == "Home":
            msg = generate_encouragement(username, load_users())
            st.info(msg)

        elif menu == "Quiz Me":
            # Call your run_quiz function (you'll need to adapt inputs to st widgets)
            st.info("Quiz section — adapt run_quiz here")

        elif menu == "Encourage Me":
            msg = generate_encouragement(username, load_users())
            st.success(msg)

        elif menu == "Chat with Me":
            # Your AI chat logic (use st.chat_input)
            st.info("AI Chat section")

        elif menu == "Learning Materials":
            show_learning_materials()

        elif menu == "Progress Dashboard":
            show_progress_dashboard(username)

        elif menu == "Logout":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()
