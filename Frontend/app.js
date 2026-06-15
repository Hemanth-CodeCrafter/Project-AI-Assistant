const API_URL = "/command";

document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("command");

    input.focus();

    input.addEventListener("keydown", function(e){

        if(e.key === "Enter"){
            sendCommand();
        }

    });

});

async function sendCommand(){

    const input = document.getElementById("command");

    const text = input.value.trim();

    if(!text){
        return;
    }

    addMessage("You", text, "user");

    input.value = "";

    const thinkingDiv =
        addMessage(
            "Jarvis",
            "Thinking...",
            "jarvis"
        );

    try{

        const response = await fetch(
            API_URL,
            {
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    text:text
                })
            }
        );

        const data = await response.json();

        let reply = "";

        if(data.responses){

            reply = data.responses.join(" ");

        }
        else if(data.response){

            reply = data.response;

        }
        else{

            reply = "Done.";

        }

        thinkingDiv.innerHTML =
            "<b>Jarvis:</b> " + reply;

    }
    catch(err){

        thinkingDiv.innerHTML =
            "<b>Jarvis:</b> Unable to connect.";

        console.error(err);

    }

    input.focus();
}

function addMessage(sender,text,cls){

    const chat =
        document.getElementById("chat-box");

    const div =
        document.createElement("div");

    div.className =
        "message " + cls;

    div.innerHTML =
        "<b>" + sender + ":</b> " + text;

    chat.appendChild(div);

    chat.scrollTop =
        chat.scrollHeight;

    return div;
}

// ─────────────────────────────────────────────
// Speech Recognition
// ─────────────────────────────────────────────

const micBtn = document.getElementById("mic-btn");

const SpeechRecognition =
    window.SpeechRecognition ||
    window.webkitSpeechRecognition;

if (SpeechRecognition) {

    const recognition = new SpeechRecognition();

    let listening = false;

    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    micBtn.addEventListener("click", () => {

        if (listening) {
            return;
        }

        try {
            recognition.start();
        }
        catch (err) {
            console.log(err);
        }

    });

    recognition.onstart = () => {

        listening = true;

        micBtn.innerText = "🎙️";

        console.log("Listening...");

    };

    recognition.onresult = (event) => {

        const text =
            event.results[0][0].transcript;

        console.log("Heard:", text);

        document.getElementById("command").value =
            text;

        sendCommand();

    };

    recognition.onerror = (event) => {

        listening = false;

        micBtn.innerText = "🎤";

        console.log(
            "Speech Error:",
            event.error
        );

        alert(
            "Speech Error: " +
            event.error
        );

    };

    recognition.onend = () => {

        listening = false;

        micBtn.innerText = "🎤";

        console.log("Recognition ended");

    };

}
else {

    micBtn.disabled = true;

    alert(
        "Speech Recognition Not Supported"
    );

}