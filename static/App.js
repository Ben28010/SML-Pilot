//this object is thethat remembers everything about the current test while it runs.
const state = {
  topic: "",           //which topic the user picked
  totalQ: 5,           //how many questions they wanted
  current: 0,          //which question we its on (0 means the first one)
  correct: 0,          //how many they have got right so far
  answers: [],         //a list that grows as each question is answered, used for the review screen
  currentQuestion: "", //the question currently on screen, saved so we can send it to flask when marking
  currentContext: "",  //the pdf text behind the question, also needed when sending to flask for marking
};

//shortcut for document.getElementById
const doc = id => document.getElementById(id);

//takes a screen name, then loops through all three screens and shows the matching one while hiding the other two.
function showScreen(name) {
  doc("screen-setup").classList.add("hidden");
  doc("screen-test").classList.add("hidden");
  doc("screen-results").classList.add("hidden");
  doc("screen-" + name).classList.remove("hidden"); //remove hidden only from the one we want
}

// this function replaces html characters so cant be misinterpreted
function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")   //& becomes &amp;
    .replace(/</g, "&lt;")    //< becomes &lt;
    .replace(/>/g, "&gt;");   //> becomes &gt;
}

// this function asks the flask server to replace topic dropdown with topics.
async function loadTopics() {//async: function can pause and wait for the server without freezing the page
  try {
    //await: wait here until the server responds before moving to the next line
    const response = await fetch("/api/topics"); //send a request to the flask GET /api/topics route
    const data = await response.json();          //wait for the response and convert it from json to a js object

    doc("sel-topic").innerHTML = ""; //remove loading placeholder out of the dropdown

    //loop through every topic name the server sent back
    for (let i = 0; i < data.topics.length; i++) {
      const option = document.createElement("option"); //create a new dropdown option element
      option.value = data.topics[i];
      option.textContent = data.topics[i];
      doc("sel-topic").appendChild(option); //attach it to the dropdown
    }

  } catch (error) {
    //show an error in the dropdown
    doc("sel-topic").innerHTML = '<option value="">Couldnt load topics</option>';
  }
}

//resets all the visible elements from the previous question, then asks flask to generate a new one and displays it
async function loadQuestion() {

  //hide everything left over from the previous question
  doc("question-box").classList.add("hidden");
  doc("answer-section").classList.add("hidden");
  doc("feedback").classList.add("hidden");
  doc("next-wrap").classList.add("hidden");
  doc("answer-input").value = "";        //clear answer box of text
  doc("btn-submit").disabled = false;    //re-enable the submit button

  //update the progress label
  doc("progress-text").textContent = "Question " + (state.current + 1) + " of " + state.totalQ;

  //show the loading message while we wait for flask to respond
  doc("loading-q").classList.remove("hidden");

  try {
    //send a POST request to flask with the chosen topic
    //POST sends data to the server
    const response = await fetch("/api/question", {
      method: "POST",
      headers: { "Content-Type": "application/json" }, //tells flask to expect json
      body: JSON.stringify({ topic: state.topic }),     //converts the topic object to a json string
    });
    const data = await response.json(); //wait for the response and parse it

    //save the question and context into state
    state.currentQuestion = data.question;
    state.currentContext = data.context;

    //put the question text on screen and reveal the question box and answer area
    doc("question-box").textContent = data.question;
    doc("question-box").classList.remove("hidden");
    doc("answer-section").classList.remove("hidden");

  } catch (error) {
    doc("question-box").textContent = "Error: could not reach the server.";
    doc("question-box").classList.remove("hidden");
  }

  //hide the loading message now the question is showing
  doc("loading-q").classList.add("hidden");
}

//when the student clicks submit answer it reads what they typed, sends it to flask for marking and shows result
async function submitAnswer() {

  //read the answer and remove any extra spaces
  const answer = doc("answer-input").value.trim();

  //if the box is empty give notification
  if (!answer) {
    alert("Please type an answer first.");
    return; //exits function
  }

  //disable the submit button immediately so the user cant click it twice
  doc("btn-submit").disabled = true;
  doc("loading-eval").classList.remove("hidden"); //show the evaluating message

  try {
    //send the question, context and answer to flask for marking
    const response = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: state.currentQuestion, //for comparison to question
        context:  state.currentContext,//for comparison to context
        answer:   answer,
      }),
    });
    const data = await response.json(); //data.correct is true or false, data.explanation is a string

    //save result into the answers list so it can be shown on the review screen later
    state.answers.push({
      question:    state.currentQuestion,
      userAnswer:  answer,
      correct:     data.correct,
      explanation: data.explanation,
    });

    //if the answer was correct add one to the correct count
    if (data.correct) {
      state.correct = state.correct + 1;
    }

    //show the feedback box with the right colour
    const fb = doc("feedback");
    if (data.correct) {
      fb.className = "correct";
      fb.innerHTML = "<strong>Correct</strong><br>" + escHtml(data.explanation);
    } else {
      fb.className = "incorrect";
      fb.innerHTML = "<strong>Incorrect</strong><br>" + escHtml(data.explanation);
    }
    fb.classList.remove("hidden"); //reveal feedback box

    doc("next-wrap").classList.remove("hidden"); //reveal next question button

  } catch (error) {
    //if flask couldnt be reached show an error in the feedback box
    const fb = doc("feedback");
    fb.className = "incorrect";
    fb.innerHTML = "<strong>Error</strong><br>Could not reach the server.";
    fb.classList.remove("hidden");
  }

  doc("loading-eval").classList.add("hidden"); //hide the evaluating message
}

//when the user clicks next question adds one to the current question counter, then loads the next question or ends the test
function nextQuestion() {
  state.current = state.current + 1;

  if (state.current >= state.totalQ) {
    showResults(); //all the questions done, go to results
  } else {
    loadQuestion(); //there are still questions left, load the next one
  }
}

//calculates the final percentage and switches to the results screen
function showResults() {
  const percentage = Math.round((state.correct / state.totalQ) * 100);

  doc("res-score").textContent = percentage + "%";
  doc("res-detail").textContent = "You got " + state.correct + " out of " + state.totalQ + " correct.";

  doc("review-section").classList.add("hidden"); //keep the review section hidden until they ask for it

  showScreen("results");
}

//builds a card for each answered question and shows them all below the score.
function buildReview() {
  const list = doc("review-list");
  list.innerHTML = ""; //clear any cards from a previous run through

  //loop through every saved answer and create a card div for each one
  for (let i = 0; i < state.answers.length; i++) {
    const a = state.answers[i];

    const card = document.createElement("div"); //create a new blank div element
    card.className = "review-card";             //give it the review-card css class for styling

    //build the inner html of the card using the saved data
    card.innerHTML =
      "<strong>Question " + (i + 1) + ":</strong> " + escHtml(a.question) + "<br>" +
      "<strong>Your answer:</strong> " + escHtml(a.userAnswer) + "<br>" +
      "<strong>Result:</strong> " + (a.correct ? "Correct" : "Incorrect") + "<br>" +
      "<strong>Explanation:</strong> " + escHtml(a.explanation);

    list.appendChild(card); //attach the finished card to the review list on the page
  }

  doc("review-section").classList.remove("hidden"); //reveal the whole review section
}

//when question count dropdown changes, check if "custom" was selected,m if it was, show the custom number input. if not, keep it hidden.
doc("sel-count").addEventListener("change", function () {
  if (this.value === "custom") {
    doc("custom-wrap").classList.remove("hidden");
  } else {
    doc("custom-wrap").classList.add("hidden");
  }
});

//when the user clicks start test, read their choices, validate them, then begin
doc("btn-start").addEventListener("click", async function () {
  const topic = doc("sel-topic").value;

  if (!topic) {
    alert("Please select a topic.");
    return;
  }

  //work out how many questions they want
  let total;
  if (doc("sel-count").value === "custom") {
    total = parseInt(doc("input-custom").value, 10) || 5; //converts the string to a whole number
  } else {
    total = parseInt(doc("sel-count").value, 10);
  }

  if (total < 1 || total > 20) {
    alert("Please enter between 1 and 20 questions.");
    return;
  }

  //reset all state values so any previous test data does not carry over
  state.topic   = topic;
  state.totalQ  = total;
  state.current = 0;
  state.correct = 0;
  state.answers = [];

  showScreen("test");    //switch to the test screen
  await loadQuestion();  //load the first question straight away
});

//wire up the remaining buttons to their functions
doc("btn-submit").addEventListener("click", submitAnswer);
doc("btn-next").addEventListener("click", nextQuestion);
doc("btn-new-test").addEventListener("click", function () { showScreen("setup"); });
doc("btn-review").addEventListener("click", function () {
  buildReview();
  //scrollIntoView moves the page so the review section is visible on screen.
  //"smooth" means it scrolls gradually rather than jumping instantly.
  doc("review-section").scrollIntoView({ behavior: "smooth" });
});

//this line runs as soon as the browser loads the file to fill the topic dropdown before the user has a chance to interact with anything.
loadTopics();