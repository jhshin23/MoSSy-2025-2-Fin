let connectionFlag = false;
let client = null; // MQTT 클라이언트의 역할을 하는 Client 객체를 가리키는 전역변수
const CLIENT_ID = "client-"+Math.floor((1+Math.random())*0x10000000000).toString(16) // 사용자 ID 랜덤 생성
let readingLog = [];
function connect() { // 브로커에 접속하는 함수
    if(connectionFlag == true)
    	return; // 현재 연결 상태이므로 다시 연결하지 않음
    const port = 9001 // mosquitto를 웹소켓으로 접속할 포트 번호
    let broker = document.getElementById("broker").textcontent;
    client = new Paho.MQTT.Client(broker, Number(port), CLIENT_ID);
    client.onConnectionLost = onConnectionLost; // 접속 끊김 시 onConnectLost() 실행
    client.onMessageArrived = onMessageArrived; // 메시지 도착 시 onMessageArrived() 실행
    client.connect({
                onSuccess:onConnect, // 브로커로부터 접속 응답 시 onConnect() 실행
    });
}

// 브로커로의 접속이 성공할 때 호출되는 함수
function onConnect() {
        connectionFlag = true; // 연결 상태로 설정
   	client.subscribe("authResult");
   	client.subscribe("ultrasonic");
}
function onConnectionLost() {
        if(connectionFlag != true) { // 연결되지 않은 경우
        	document.getElementById("tabTitle").innerHTML = "(연결안됨)책상 대시보드";
	}
                return false;
}
	
function subscribe(topic) {
        if(connectionFlag != true) { // 연결되지 않은 경우
                alert("연결되지 않았음");
                return false;
        }
	client.subscribe(topic);
}

function unsubscribe(topic) {
    if(connectionFlag != true) return;
    client.unsubscribe(topic, null);
}

function publish(topic, msg) {
        if(connectionFlag != true) { // 연결되지 않은 경우
                alert("연결되지 않았음");
                return false;
        }
        client.send(topic, msg, 0, false);
        return true;
}


// 메시지가 도착할 때 호출되는 함수
function onMessageArrived(msg) { // 매개변수 msg는 도착한 MQTT 메시지를 담고 있는 객체
   try{ console.log("MSG ARRIVED:", msg.destinationName, msg.payloadString);
    if(msg.destinationName === 'authResult'){
	if(msg.payloadString === 'success'){
		showResult('success');
	}
	else if(msg.payloadString === 'fail'){
		showResult('fail');
	}
	else if(msg.payloadString.split(':')[0] === 'Book title'){
		changeBookTitle(msg.payloadString.trim().split(':')[1]);	
	}
	else if(msg.payloadString.split(':')[0] === 'reject'){
                //아무것도 안함			
	}
	else if(msg.payloadString === 'sitting_Authed'){
                subscribe("seat/state");
		showResult('sitting_Authed');
	}
	else if(msg.payloadString === 'sitting_notAuthed'){
		showResult('sitting_not');
	}
	else if(msg.payloadString === 'away_Authed'){
                unsubscribe("seat/state");
		showResult('away_Authed');
	}
	else if(msg.payloadString === 'away_notAuthed'){
		showResult('away_not');
	}
    }
    else if(msg.destinationName=== 'ultrasonic'){
       addChartData0(parseFloat(msg.payloadString));
    }
    else if(msg.destinationName === 'light'){
       addChartData1(parseFloat(msg.payloadString));
    }
    else if(msg.destinationName === 'shadowOnBook'){
       pageFlipCount(msg.payloadString); 
    }
    else if(msg.destinationName === 'seat/state'){
       changeSittingState(msg.payloadString); 
    }
    else {
	console.log(`${msg.destinationName}|${payload}`);
	}
} catch(e){
	console.error("onMessageArrived Error:", e);
}
}

function showResult(authState) {
     if(authState === 'success'){
	document.getElementById("viewerAuthSpan").innerHTML = "인증성공";
    }
     else if(authState === 'fail') {
	 document.getElementById("viewerAuthSpan").innerHTML = "인증실패";
     }
     else if(authState === 'sitting_Authed') {
	 document.getElementById("masterAuthSpan").innerHTML = "인증성공";
	 document.getElementById("useState").innerHTML = "사용중";
     }
     else if(authState === 'sitting_not') {
	 document.getElementById("masterAuthSpan").innerHTML = "인증실패";
     }
     else if(authState === 'away_Authed') {
	 document.getElementById("masterAuthSpan").innerHTML = "인증성공";
	 document.getElementById("useState").innerHTML = "사용안함";
	 document.getElementById("sittingState").innerHTML = ""; 
     }
     else if(authState === 'away_not') {
	 document.getElementById("masterAuthSpan").innerHTML = "인증실패";
     }
}

function changeBookTitle(title) {
	document.getElementById("titleHead").innerHTML = title;
}

function pageFlipCount(cnt){
	const reading = document.getElementById("shadowCount");
	timeAndCnt = cnt.split(",");
	time = timeAndCnt[0];
	page = timeAndCnt[1];
	readingLog.push(`${page} (${time})`); 

	if (readingLog.length > 10) {
		readingLog.shift();
	}
	reading.innerHTML = readingLog.join("<br>");
}
function changeSittingState(state){
	document.getElementById("sittingState").innerHTML = state; 
}
