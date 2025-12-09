from flask import Flask, render_template, request

app = Flask(__name__) # Flask 객체 생성

# 자바스크립트 코드나 이미지 파일 등에 대해
# 브라우저에게 캐시에 저장한 파일을 사용하지 않도록 지시
app.config['SEND_FILE_MAX_AGE_DEFAULT']=0

@app.route('/') # 다음 2라인이 라우팅 테이블에 ['/':home] 형태로 저장하도록 함
def home():
        return render_template('desk.html')

if __name__ == "__main__": # 이 프로그램이 독립적으로 실행되는 경우
        app.run(host='0.0.0.0', port=8080, debug=True) # app.run() 함수 실행

