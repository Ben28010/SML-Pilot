import os  # used for checking folders and setting environment variables
import re  # used for finding patterns in the model's text output
import torch  # the maths engine that runs the ai model
from flask import Flask, request, jsonify, send_from_directory  # flask tools for running the web server
from pypdf import PdfReader  # reads text out of pdf files
from transformers import AutoModelForCausalLM, AutoTokenizer  # downloads and loads the ai model

os.environ["TRANSFORMERS_OFFLINE"] = "1"  # forces the app to use the locally cached model, no internet needed

DOCS_FOLDER = "my_docs"  # the folder where your pdf syllabus files should be placed
MODEL_NAME = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # the larger 1.1 billion parameter model being used
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"  # uses gpu if one is available, otherwise falls back to cpu
CONTEXT_LENGTH = 800  # maximum number of characters of pdf text passed to the model
MIN_LINE_LEN = 40  # any line shorter than this from the pdf is ignored as it is likely a heading or page number

TOPICS = [  # the list of syllabus topics shown in the dropdown on the webpage
    "Air Law",
    "Meteorology",
    "Principles of Flight",
    "Human Performance",
    "Aircraft Technical",
    "Communication",
    "Navigation",
]

app = Flask(__name__, static_folder="static")  # creates the flask web server and tells it where the html file lives

print(f"loading model: {MODEL_NAME} on {DEVICE}")  # prints a message so you know the model is loading
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)  # loads the tokenizer which converts text to numbers the model understands
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME).to(DEVICE)  # loads the actual ai model and moves it to the right device
model.eval()  # puts the model into evaluation mode so it does not try to update its own weights while running
print("model ready\n")  # confirms the model has loaded successfully


def get_best_context(topic):
    best_lines = []  # will store the most relevant lines found across all pdfs
    words = set(topic.lower().split())  # splits the topic into individual words for keyword matching

    if not os.path.isdir(DOCS_FOLDER):  # checks the my_docs folder actually exists
        return f"General aviation topic: {topic}."  # returns a basic fallback if the folder is missing

    pdf_files = [f for f in os.listdir(DOCS_FOLDER) if f.endswith(".pdf")]  # finds all pdf files in the folder

    if not pdf_files:  # checks there is at least one pdf in the folder
        return f"General aviation topic: {topic}."  # returns a fallback if no pdfs are found

    for filename in pdf_files:  # loops through each pdf file found
        try:
            reader = PdfReader(os.path.join(DOCS_FOLDER, filename))  # opens the pdf
            full_text = " ".join(page.extract_text() or "" for page in reader.pages)  # extracts all text from every page
        except Exception as e:
            print(f"could not read {filename}: {e}")  # prints a warning if a pdf cannot be read
            continue  # skips to the next pdf if this one fails

        lines = full_text.replace(". ", ".\n").split("\n")  # splits the text into individual lines at sentence boundaries

        scored = []  # will store each line alongside how relevant it is to the topic
        for line in lines:
            line = line.strip()  # removes extra whitespace from the start and end of the line
            if len(line) < MIN_LINE_LEN:  # skips lines that are too short to be useful
                continue
            score = len(words.intersection(set(line.lower().split())))  # counts how many topic words appear in this line
            scored.append((score, line))  # stores the score and line together

        scored.sort(reverse=True, key=lambda x: x[0])  # sorts lines so the most relevant ones come first
        best_lines.extend(line for _, line in scored[:5])  # takes the top 5 most relevant lines from this pdf

    combined = " ".join(best_lines)  # joins all the best lines into one block of text
    return combined[:CONTEXT_LENGTH] if combined else f"General aviation topic: {topic}."  # returns the text trimmed to the max length


def generate_question(context):
    prompt = (
        "You are an aviation exam question generator.\n\n"
        f"Context:\n{context}\n\n"  # the relevant pdf text is inserted here
        "Write ONE short exam question based ONLY on the context above.\n"
        "Question:"  # the model continues writing from here, producing the question
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).to(DEVICE)  # converts the prompt text into numbers the model can process

    with torch.no_grad():  # disables gradient tracking since we are not training, just generating
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,  # limits the question to roughly 80 tokens in length
            temperature=0.7,  # adds some randomness so questions are not always identical
            do_sample=True,  # enables the random sampling controlled by temperature
            pad_token_id=tokenizer.eos_token_id,  # tells the model what token signals the end of text
        )

    prompt_len = inputs["input_ids"].shape[1]  # records how long the original prompt was in tokens
    new_tokens = outputs[0][prompt_len:]  # slices off the prompt so we only have the newly generated tokens
    question = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()  # converts the tokens back into readable text

    question = question.split("\n")[0].strip()  # keeps only the first line in case the model generated extra text
    question = re.sub(r"^question\s*:\s*", "", question, flags=re.IGNORECASE).strip()  # removes any accidental "question:" prefix the model added

    return question or "What are the key requirements for this aviation topic?"  # returns a fallback if the model produced nothing usable


def evaluate_answer(context, question, user_answer):
    prompt = (
        "You are marking a pilot training exam.\n\n"
        f"Context:\n{context}\n\n"  # the same pdf text used to generate the question
        f"Question:\n{question}\n\n"  # the question that was asked
        f"Student Answer:\n{user_answer}\n\n"  # what the student typed
        "Is the student's answer correct based on the context? "
        "Answer Yes or No, then explain why in one sentence.\n\n"
        "Correct:"  # the model continues from here with yes or no followed by a reason
    )

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=768).to(DEVICE)  # converts the full prompt into tokens

    with torch.no_grad():  # no gradient tracking needed for inference
        outputs = model.generate(
            **inputs,
            max_new_tokens=120,  # gives the model enough room to write yes/no and an explanation
            temperature=0.1,  # very low temperature makes the marking more consistent and predictable
            do_sample=False,  # disables random sampling so the model picks the most likely answer each time
            pad_token_id=tokenizer.eos_token_id,  # end of text token
        )

    prompt_len = inputs["input_ids"].shape[1]  # length of the prompt in tokens
    new_tokens = outputs[0][prompt_len:]  # only the tokens the model generated, not the prompt
    raw = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()  # converts generated tokens back to text

    full = "Correct:" + raw  # adds back the "Correct:" prefix since the prompt ended mid-sentence

    correct_match = re.search(r"correct\s*:\s*(yes|no)", full, re.IGNORECASE)  # looks for "correct: yes" or "correct: no" in the output
    expl_match = re.search(r"explanation\s*:\s*(.+?)(?:\n|$)", full, re.IGNORECASE | re.DOTALL)  # looks for an explanation sentence after the verdict

    correct = correct_match.group(1).strip().lower() == "yes" if correct_match else False  # sets correct to true if the model said yes
    explanation = expl_match.group(1).strip() if expl_match else "See context for details."  # extracts the explanation or uses a fallback

    return {"correct": correct, "explanation": explanation}  # sends back the result as a dictionary


@app.route("/api/topics", methods=["GET"])
def api_topics():
    return jsonify({"topics": TOPICS})  # sends the topic list to the webpage when it first loads


@app.route("/api/question", methods=["POST"])
def api_question():
    data = request.get_json(force=True)  # reads the json sent by the webpage
    topic = data.get("topic", "").strip()  # extracts the topic the user selected

    if not topic:  # returns an error if no topic was provided
        return jsonify({"error": "No topic provided"}), 400

    context = get_best_context(topic)  # finds the most relevant text from the pdfs for this topic
    question = generate_question(context)  # uses the model to generate a question from that text
    return jsonify({"question": question, "context": context})  # sends the question and context back to the webpage


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    data = request.get_json(force=True)  # reads the json sent by the webpage
    question = data.get("question", "").strip()  # the question that was shown to the student
    context = data.get("context", "").strip()  # the pdf text that was used to generate the question
    user_answer = data.get("answer", "").strip()  # what the student typed as their answer

    if not question or not user_answer:  # returns an error if required fields are missing
        return jsonify({"error": "Missing question or answer"}), 400

    result = evaluate_answer(context, question, user_answer)  # asks the model to mark the answer
    return jsonify(result)  # sends the correct/incorrect result back to the webpage


@app.route("/")
def index():
    return send_from_directory("static", "index.html")  # serves the main webpage when someone visits the site


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("static", path)  # serves any other static files like css or javascript


if __name__ == "__main__":
    os.makedirs(DOCS_FOLDER, exist_ok=True)  # creates the my_docs folder if it does not already exist
    print(f"pdf folder: ./{DOCS_FOLDER}/")
    print("server starting at http://127.0.0.1:5001\n")
    app.run(debug=False, host="127.0.0.1", port=5001)  # starts the web server on port 5001 (different from the smollm version)