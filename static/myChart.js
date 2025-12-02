
let ctx0 = null;
let ctx1 = null;
let chart0 = null;
let chart1 = null;
let config0 = {
        // type은 차트 종류 지정
        type: 'line', // 라인그래프
        // data는 차트에 출력될 전체 데이터 표현
        data: {
                // labels는 배열로 데이터의 레이블들
                labels: [],
                // datasets 배열로 이 차트에 그려질 모든 데이터 셋 표현. 그래프 1개만 있음
                datasets: [
                        {
                        label: '초음파 센서로부터 측정된 실시간 거리',
                        backgroundColor: 'blue',
                        borderColor: 'rgb(255, 99, 132)',
                        borderWidth: 2,
                        data: [], // 각 레이블에 해당하는 데이터
                        fill : false, // 채우지 않고 그리기
                        yAxisID: 'd'
                        }
                ]
        },
        // 차트의 속성 지정
        options: {
                responsive : false, // 크기 조절 금지
                scales: { // x축과 y축 정보
                        xAxes: [{
                                display: true,
                                scaleLabel: { display: true, labelString: '시간(0.5초)' },
                        }],
                        yAxes: [{
                                id: 'd',
                                position: 'left',
                                display: true,
                                scaleLabel: { display: true, labelString: '거리(cm)' },
                                // 거리 값의 편차가 너무 커서 y축 눈금의 최대 최소를 지정하지 않았음
                        }
                        ]
                }
        }
};

let config1 = {
        // type은 차트 종류 지정
        type: 'line', // 라인그래프
        // data는 차트에 출력될 전체 데이터 표현
        data: {
                // labels는 배열로 데이터의 레이블들
                labels: [],
                // datasets 배열로 이 차트에 그려질 모든 데이터 셋 표현. 그래프 1개만 있음
                datasets: [
                        {
                        label: '조도센서 측정 실시간 조도',
                        backgroundColor: 'blue',
                        borderColor: 'black',
                        borderWidth: 2,
                        data: [], // 각 레이블에 해당하는 데이터
                        fill : false, // 채우지 않고 그리기
                        yAxisID: 'd'
                        }
                ]
        },
        // 차트의 속성 지정
        options: {
                responsive : false, // 크기 조절 금지
                scales: { // x축과 y축 정보
                        xAxes: [{
                                display: true,
                                scaleLabel: { display: true, labelString: '시간(0.1초)' },
                        }],
                        yAxes: [{
                                id: 'd',
                                position: 'left',
                                display: true,
                                scaleLabel: { display: true, labelString: '밝기' },
                        }]
                }
        }

};

let LABEL_SIZE = 20; // 차트에 그려지는 데이터의 개수
let tick0 = 0; // 도착한 데이터의 개수임, tick의 범위는 0에서 99까지만
let tick1 = 0; // 도착한 데이터의 개수임, tick의 범위는 0에서 99까지만

function drawChart() {
        ctx0 = document.getElementById('ultraCanvas').getContext('2d');
        chart0 = new Chart(ctx0, config0);
        ctx1 = document.getElementById('lightCanvas').getContext('2d');
        chart1 = new Chart(ctx1, config1);
        init();
}

function init() { // chart.data.labels의 크기를 LABEL_SIZE로 만들고 0~19까지 레이블 붙이기
        for(let i=0; i<LABEL_SIZE; i++) {
                chart0.data.labels[i] = i;
                chart1.data.labels[i] = i;
        }
        chart0.update();
        chart1.update();
}

function addChartData1(value1) {
        let n = chart1.data.datasets[0].data.length; // 현재 데이터의 개수
        if(n < LABEL_SIZE){ // 현재 데이터 개수가 LABEL_SIZE보다 작은 경우
                chart1.data.datasets[0].data.push(value1);
        }
        else { // 현재 데이터 개수가 LABEL_SIZE를 넘어서는 경우
                // 새 데이터 value 삽입
                chart1.data.datasets[0].data.push(value1); // value를 data[]의 맨 끝에 추가
                chart1.data.datasets[0].data.shift(); // data[]의 맨 앞에 있는 데이터 제거
                // 레이블 삽입
                chart1.data.labels.push(tick1); // tick(인덱스)을 labels[]의 맨 끝에 추가
                chart1.data.labels.shift(); // labels[]의 맨 앞에 있는 값 제거
        }
        tick1++; // 도착한 데이터의 개수 증가
        tick1 %= 100; // tick의 범위는 0에서 99까지만. 100보다 크면 다시 0부터 시작
        chart1.update();
}

function addChartData0(value0) {
        let n = chart0.data.datasets[0].data.length; // 현재 데이터의 개수
        if(n < LABEL_SIZE){ // 현재 데이터 개수가 LABEL_SIZE보다 작은 경우
                chart0.data.datasets[0].data.push(value0);
        }
        else { // 현재 데이터 개수가 LABEL_SIZE를 넘어서는 경우
                // 새 데이터 value 삽입
                chart0.data.datasets[0].data.push(value0); // value를 data[]의 맨 끝에 추가
                chart0.data.datasets[0].data.shift(); // data[]의 맨 앞에 있는 데이터 제거
                // 레이블 삽입
                chart0.data.labels.push(tick0); // tick(인덱스)을 labels[]의 맨 끝에 추가
                chart0.data.labels.shift(); // labels[]의 맨 앞에 있는 값 제거
        }
        tick0++; // 도착한 데이터의 개수 증가
        tick0 %= 100; // tick의 범위는 0에서 99까지만. 100보다 크면 다시 0부터 시작
        chart0.update();
}

function hideshow(id) { // 캔버스 보이기 숨기기
        let canvas =  document.getElementById(id); // canvas DOM 객체 알아내기
        if(canvas.style.display == "none") // canvas 객체가 보이지 않는다면
                canvas.style.display = "inline-block"; // canvas 객체를 보이게 배치
        else
                canvas.style.display = "none" ;  // canvas 객체를 보이지 않게 배치
}

