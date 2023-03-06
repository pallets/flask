
var isfreshStart = true;
var wordCount = 0;
var qualityType = 0;
var timeCounterForSpeed = 0;
var speed = 0;
var userid = "";
var timeCounterForSpeed_pause = false;
var msg = new SpeechSynthesisUtterance();
var voices = window.speechSynthesis.getVoices();
msg.voice = voices[10];
msg.voiceURI = "native";
msg.volume = 1;
msg.rate = 0.8;
msg.pitch = 0.8;
msg.lang = 'en-US';

// information about data
var wholeData = [];
var suggestions = ["Donot use caps lock while typing", "Use the correct positioning of fingers", "Focus on accuracy over speed", "Don’t look at the keyboard or your hands", "Practice, Practice, Practice"];
var suggestion_count = 0;
var dataCount = 0;
var data = "";
var pointer_to_data = 1;
var firstPartData = "";
var secondPartData = "";

function startTimeCounter() {
    const timeOut = setInterval(function(){
        if (isfreshStart) {
            clearTimeout(timeOut);
        }
        if (!timeCounterForSpeed_pause) {
            timeCounterForSpeed += 1;
            speed = parseInt(wordCount / (timeCounterForSpeed / 60.0));
            document.getElementById("speed_info").textContent = speed;
            qualityType = parseInt(speed/10) % 10;
            switch (qualityType) {
                case 0 :
                case 1 :
                case 2 :
                case 3 : document.getElementById("speed_info").style.color = "red"; break;
                case 4 : document.getElementById("speed_info").style.color = "#D2E101"; break;
                default : document.getElementById("speed_info").style.color = "green"; break;
            }
        }
    }, 1000);
}

function startSuggestion() {
    const timeOut = setInterval(function(){
        if (isfreshStart) {
            clearTimeout(timeOut);
        }
        if (document.getElementById("start-button").innerText == "Pause") {
            document.getElementById("suggestion").textContent = "( suggestion : " + suggestions[suggestion_count % suggestions.length] + " )";
            suggestion_count += 1;
        }
    }, 3000);
}

function speak(message) {
    msg.text = document.getElementById("main-text-second").textContent;
    if (document.getElementById("listenAndtype_id").checked && (document.getElementById("start-button").innerText == "Pause")) {
        speechSynthesis.speak(msg);
    }
}

function start() {
    if (isfreshStart) { // for the first start
        secondPartData = data[pointer_to_data - 1] + " " + data[pointer_to_data] + " " + data[pointer_to_data + 1];
        pointer_to_data = 1;
        timeCounterForSpeed = 0;
        wordCount = 0;
        speed = 0;
        timeCounterForSpeed_pause = false;
        startTest();
        startTimeCounter();
        startSuggestion();
        isfreshStart = false;
        document.getElementById("main-text-second").textContent = firstPartData + secondPartData;
        document.getElementById("start-button").innerText = "Pause";
        document.getElementById("start-button").style.backgroundColor = "yellow";
        document.getElementById("start-button").style.borderColor = "yellow";
        document.getElementById("text-test").disabled = false;
    } else if (document.getElementById("start-button").innerText == "Start") {
        document.getElementById("main-text-second").textContent = firstPartData + secondPartData;
        document.getElementById("start-button").innerText = "Pause";
        document.getElementById("start-button").style.backgroundColor = "yellow";
        document.getElementById("start-button").style.borderColor = "yellow";
        document.getElementById("text-test").disabled = false;
        startTest();
        startTimeCounter();
        startSuggestion();
    } else { // when clicked on pause to pause test.
        timeCounterForSpeed_pause = true;
        document.getElementById("main-text-first").textContent = "";
        document.getElementById("main-text-second").textContent = "Click on 'Start' to continue test";
        document.getElementById("start-button").innerText = "Start";
        document.getElementById("start-button").style.backgroundColor = "green";
        document.getElementById("start-button").style.borderColor = "green";
        document.getElementById("text-test").disabled = true;
    }
}

function startTest() {
    var timeCount = 0;
    var shallEndTheGameAfterSingleWord = false;
    const timeOut = setInterval(function(){
        // resetting timeout when reset (stop) is done
        if (isfreshStart) {
            clearTimeout(timeOut);
        }

        // when test is started
        if (document.getElementById("start-button").innerText == "Pause") {
            let mainData = document.getElementById("main-text-first").textContent + document.getElementById("main-text-second").textContent;
            let ansData = document.getElementById("text-test").value.trim();
            let commonData = "";
            let temp = 0;
            for (; temp < ansData.length; temp++) {
                if((document.getElementById("ignoreCase_id").checked && mainData[temp].toLowerCase() == ansData[temp].toLowerCase()) || ((!document.getElementById("ignoreCase_id").checked) && mainData[temp] == ansData[temp])) {
                    commonData += mainData[temp];
                    continue;
                }
                break;
            }

            if (commonData.trim().split(" ").length > 1) {
                if (pointer_to_data + 2 != data.length) {
                    pointer_to_data += 1;
                } else {
                    shallEndTheGameAfterSingleWord = true;
                }
                document.getElementById("main-text-first").textContent = commonData.trim().split(" ")[commonData.split(" ").length==0 ? 0 : commonData.split(" ").length-1];
                let temp_data = data[pointer_to_data - 1] + " " + data[pointer_to_data] + " " + data[pointer_to_data + 1];
                temp_data = temp_data.substring(document.getElementById("main-text-first").textContent.length, temp_data.length);//split(document.getElementById("main-text-first").textContent);
                // if (true) {
                //     let temp_temp_data = "";
                //     for(let i = 1; i < temp_data.length ; i++)
                //         temp_temp_data += temp_data[i] + " ";
                //     temp_data = temp_temp_data.trim();
                // }
                document.getElementById("main-text-second").textContent = temp_data;
                document.getElementById("main-text-first").style.color = "brown";
                document.getElementById("text-test").value = commonData.split(" ")[commonData.split(" ").length-1];
                firstPartData = document.getElementById("main-text-first").textContent + " ";
                secondPartData = document.getElementById("main-text-second").textContent;
                document.getElementById("text-test").value = firstPartData.trim();
                wordCount += 1;
            } else {
                if ( commonData.length != 0) {
                    firstPartData = commonData;
                    secondPartData = (document.getElementById("main-text-first").textContent + document.getElementById("main-text-second").textContent).substring(temp, mainData.length);
                    document.getElementById("main-text-first").textContent = firstPartData;
                    document.getElementById("main-text-first").style.color = "brown";
                    document.getElementById("main-text-second").textContent = secondPartData;

                    // end game
                    if ( commonData.length == (firstPartData + secondPartData).trim().length) {
                        let message = qualityType < 4 ? "You need to improve your typing speed." : qualityType > 4 ? "Your typing speed is nice. Keep it up" : "Your typing speed is good. Practice more!";
                        alert("game ended! Your Typing speed is " + speed + " words/min.\n" + message);
                        let updateSpeed = speed;
                        stop();
                        window.location.href = './savescore.php?uid=' + userid + "&score=" + updateSpeed;
                    }
                }
            }

            // delay in audio output in repeating
            timeCount += 1;
            if (timeCount % 25 == 0) {
                speak();
                timeCount = 1;
            }
        }
    }, 100);
}

function stop() { // when stop is clicked, resetting everything
    var updateSpeed_temp = speed;
    var qualityType_temp = qualityType;
    document.getElementById("main-text-first").textContent = "";
    document.getElementById("main-text-second").textContent = "Click on 'START' to start test";
    document.getElementById("start-button").innerText = "Start";
    document.getElementById("start-button").style.backgroundColor = "green";
    document.getElementById("start-button").style.borderColor = "green";
    document.getElementById("text-test").value = "";
    document.getElementById("text-test").disabled = true;
    document.getElementById("suggestion").textContent = "";
    pointer_to_data = 1;
    timeCounterForSpeed_pause = true;
    isfreshStart = true;
    wordCount = 0;
    qualityType = 0;
    speed = 0;
    dataCount += 1;
    data = wholeData[dataCount % wholeData.length].split(" ");
    tempData = [];
    for (let i = 0 ; i < 22/*data.length*/ ; i++) {
        if (data[i].trim().length != 0){
            tempData.push(data[i]);
        }
    }
    data = tempData;
    timeCounterForSpeed = 0;
    firstPartData = "";
    secondPartData = data[pointer_to_data - 1] + " " + data[pointer_to_data] + " " + data[pointer_to_data + 1];
    document.getElementById("speed_info").textContent = 0;
    document.getElementById("speed_info").style.color = "black";

    // end game
    if ( updateSpeed_temp != 0) {
        let message = qualityType_temp < 4 ? "You need to improve your typing speed." : qualityType_temp > 4 ? "Your typing speed is nice. Keep it up" : "Your typing speed is good. Practice more!";
        alert("game ended! Your Typing speed is " + updateSpeed_temp + " words/min.\n" + message);
        window.location.href = './savescore.php?uid=' + userid + "&score=" + updateSpeed_temp;
    }
}

function showAlertForSubscribe() {
    if (document.getElementById("subscribe").checked) {
        // alert("Subscribed successfully to get latest-updates.")
        window.location.href = './subscribe.php?uid=' + userid + '&subs=1';
    } else {
        // alert("Unsubscribed successfully!")
        window.location.href = './subscribe.php?uid=' + userid + '&subs=0';
    }
}

function loadBestSpeed() {
    var usernames = ["Ujjwal Kumar", "Niyaz Ahmed Mir", "Bimal"];
    var speeds = [10, 20, 30];
    let temp_list = "";
    for (let i = 0; i < usernames.length; i++) {
        temp_list += "<tr><td>" + usernames[i] + "</td><td>:</td><td> " + speeds[i] + " words/min</td></tr>";
    }
    document.getElementById("user_info").innerHTML = temp_list;
}

function checkEmail() {
    let email = document.getElementById("email").value;
    if(!String(email).toLowerCase()
            .match(/^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/)) {
              document.getElementById("email").style.color = "red";
              return false;
            }
    document.getElementById("email").style.color = "black";
    return true;
}

function logout() {
  window.location.replace('../index.html');
}
