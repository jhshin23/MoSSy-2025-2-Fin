let connectionFlag = false;
let client = null; // MQTT 클라이언트의 역할을 하는 Client 객체를 가리키는 전역변수
const CLIENT_ID = "client-"+Math.floor((1+Math.random())*0x10000000000).toString(16) // 사용자 ID 랜덤 생성
let readingLog = [];
function connect() { // 브로커에 접속하는 함수
    if(connectionFlag == true)
    	return; // 현재 연결 상태이므로 다시 연결하지 않음
    const port = 9001 // mosquitto를 웹소켓으로 접속할 포트 번호
    let broker = document.getElementById("broker").textContent;
    client = new Paho.MQTT.Client(broker, Number(port), CLIENT_ID);
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
        // 성공 실패를 뷰어 인증요청에 대해 표시 
	if(msg.payloadString === 'success'){
		showResult('success');
	}
	else if(msg.payloadString === 'fail'){
		showResult('fail');
	}
        // 책 제목 변경 인증 요청 성공. 책제목을 변경 
	else if(msg.payloadString.split(':')[0] === 'Book title'){
		changeBookTitle(msg.payloadString.trim().split(':')[1]);	
	}
        // 실패하면 아무 변화 없음
	else if(msg.payloadString.split(':')[0] === 'reject'){
                //아무것도 안함			
	}
        // 착석 시작 버튼으로 인증 시작, 성공 시 착석상태 구독, 표시
	else if(msg.payloadString === 'sitting_Authed'){
                subscribe("seat/state");
		showResult('sitting_Authed');
	}
        // 착석 시작 버튼으로 인증 시작, 실패 시 인증 실패 표시
	else if(msg.payloadString === 'sitting_notAuthed'){
		showResult('sitting_not');
	}
        // 떠나기 버튼으로 인증 시작, 성공 시 착석상태 구독해제, 사용중지표시
	else if(msg.payloadString === 'away_Authed'){
                unsubscribe("seat/state");
		showResult('away_Authed');
	}
        // 떠나기 버튼으로 인증 시작, 실패 시 인증 실패 표시 
	else if(msg.payloadString === 'away_notAuthed'){
		showResult('away_not');
	}
    }
    // 초음파, 조도, 센서 측정값, 착석상태, 플립 판정을 브라우저에 표시
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
    // 디버그용
    else {
	console.log(`${msg.destinationName}|${payload}`);
	}
} catch(e){
	console.error("onMessageArrived Error:", e);
}
}

// 인증 결과, 책상 사용 여부를 표시
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

// 책 제목 변경
function changeBookTitle(title) {
	document.getElementById("titleHead").innerHTML = title;
}

// 책장 넘김을 최근 10개까지 표시
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

// 착석 상태를 표시
function changeSittingState(state){
	document.getElementById("sittingState").innerHTML = state; 
}
