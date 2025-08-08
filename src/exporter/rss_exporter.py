from flask import Flask, Response, request
from prometheus_client import Gauge, generate_latest

# Create Flask Application
app = Flask(__name__)

# Prometheus Gauge Metrics
# 정의: 특정 시점의 값을 나타냄 (ex. 기사 수)
# 이유: 수집한 RSS 기사 수를 Promethues로 export 하기 위해 사용
# 확장성: target 외에도 category, source 등 추가 라벨 구성 가능
# 대체제: Counter는 누적 수치를 나타냄으로 부적합
rss_gauge = Gauge('rss_articles_total', 'Number of RSS articles collected', ['target'])

# Prometheus Metrics Route
# 정의: /metrics URL 접근 시 Prometheus가 수집할 데이터 제공
# 이유: Prometheus scrape 대상은 반드시 /metrics에서 expose 되어야 함
# 확장성: 여러 메트릭 노출 가능 (error count, latency 등)
# 대체제: FastAPI 사용 가능하나, 단순 메트릭 노출 시 Flask로도 충분
@app.route('/metrics')
def metrics():
	return Response(generate_latest(), mimetype='text/plain')

# RSS Collector가 기사 수를 POST로 전송하는 Endpoint
# 정의: Worker Node 또는 외부 수집기가 메트릭 값을 전송하는 API
# 이유: Master Node에서 Exporter를 운영하고, Worker Node에서 직접 접근하지 않기 위함
# 확장성: source, timestamp 등을 함께 전송하는 형태로 확장 가능
# 대체제: Pushgateway 활용 가능하지만, Pull 기반 구조 선호 시 이 방식이 더 적절
@app.route('/report', methods=['POST'])
def report():
	try:
		content = request.json
		target = content.get('target')
		count = content.get('count')

		if target and isinstance(count, int):
			rss_gauge.labels(target=target).set(count)
			return {'status': 'ok'}, 200
		else:
			return {'status': 'error', 'reason': 'invalid data'}, 400

	except Exception as e:
		return {'status': 'error', 'reason': str(e)}, 500

# Run Flask Server
# 정의: Exporter는 독립 실행형으로 메트릭을 제공하는 HTTP Server 형태로 동작
# 이유: Prometheus는 주기적으로 HTTP로 scrape 하므로 서버가 반드시 필요
# 확장성: 0.0.0.0 설정을 통해 클러스터 내 서비스로 접근 가능하게 함
# 대체제: Gunicorn, uvicorn 등으로 Production 최적화 가능
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
