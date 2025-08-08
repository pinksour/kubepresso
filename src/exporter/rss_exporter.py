import os
from flask import Flask, Response
from prometheus_client import CollectorRegistry, Gauge, generate_latest
from utils.rss import fetch_rss

# ────────────────────────────────────────────────
# RSS Exporter (Prometheus-compatible)
# ────────────────────────────────────────────────

# √ 정의
#   RSS 기사 수를 Prometheus로 전달하는 Exporter 서버.
#   Flask 기반으로 /metrics 경로에서 메트릭을 expose함.
#
# √ 동작 흐름
#   1. ENV에서 TARGET (ex: mk_economy, hk_it) 값을 읽어옴
#   2. TARGET에 따라 RSS 피드 URL 분기 처리
#   3. fetch_rss()를 통해 기사 목록 수집
#   4. 기사 수(len)을 Gauge 메트릭으로 생성
#   5. /metrics에서 Prometheus가 scrape할 수 있도록 노출
#
# √ 활용 예시
#   >> mk_economy → https://www.mk.co.kr/rss/50000001/
#   >> hk_it       → https://www.hankyung.com/feed/it
#
# √ 환경변수 필요
#   >> TARGET: mk_economy | hk_it (컨테이너 시작 시 지정)
#   >> ex) docker run -e TARGET=mk_economy ...
#
# √ 참고 사항
#   >> 단일 메트릭으로도 여러 RSS 피드를 구분해서 기록 가능 (label 사용)
#   >> FastAPI로 교체 가능하나, 메트릭 노출만 고려 시 Flask로 충분
#   >> metrics 포맷은 Prometheus scrape 규격을 따름
# ────────────────────────────────────────────────

# Create Flask Application
app = Flask(__name__)

# 환경변수에서 대상 RSS를 결정
TARGET = os.getenv("TARGET")

# Create Prometheus Metrics Registry
registry = CollectorRegistry()

# RSS 기사 수를 기록할 Gauge 메트릭 생성
rss_guage = Gauge(
	"rss_item_count",		# Metrics Name
	"Number of RSS Items",		# Context
	["target"],			# Label
	registry=registry
)

# Prometheus Gauge Metrics
# 정의: 특정 시점의 값을 나타냄 (ex. 기사 수)
# 이유: 수집한 RSS 기사 수를 Promethues로 export 하기 위해 사용
# 확장성: target 외에도 category, source 등 추가 라벨 구성 가능
# 대체제: Counter는 누적 수치를 나타냄으로 부적합
# rss_gauge = Gauge('rss_articles_total', 'Number of RSS articles collected', ['target'])

# Prometheus Metrics Route
# 정의: /metrics URL 접근 시 Prometheus가 수집할 데이터 제공
# 이유: Prometheus scrape 대상은 반드시 /metrics에서 expose 되어야 함
# 확장성: 여러 메트릭 노출 가능 (error count, latency 등)
# 대체제: FastAPI 사용 가능하나, 단순 메트릭 노출 시 Flask로도 충분
@app.route("/metrics")
def metrics():
	"""
		Prometheus가 주기적으로 수집할 메트릭 엔드포인트
		TARGET 값에 따라 각기 다른 RSS URL을 조회
		기사 수를 Prometheus 메트릭으로 리턴
	"""

	# TARGET 분기 처리
	if TARGET == "mk_economy":	url = "https://www.mk.co.kr/rss/50000001/"
	elif TARGET == "hk_it":		url = "https://www.hankyung.com/feed/it"
	else: return Response("Invalid TARGET", status=500)

	# RSS 기사 수집
	items = fetch_rss(url)

	# 메트릭 값 설정 (라벨: target)
	rss_gauge.labels(target=TARGET).set(len(items))

	# Prometheus format 반환
	return Response(generate_latest(registry), mimetype='text/plain')

# RSS Collector가 기사 수를 POST로 전송하는 Endpoint
# 정의: Worker Node 또는 외부 수집기가 메트릭 값을 전송하는 API
# 이유: Master Node에서 Exporter를 운영하고, Worker Node에서 직접 접근하지 않기 위함
# 확장성: source, timestamp 등을 함께 전송하는 형태로 확장 가능
# 대체제: Pushgateway 활용 가능하지만, Pull 기반 구조 선호 시 이 방식이 더 적절
#@app.route('/report', methods=['POST'])
#def report():
#	try:
#		content = request.json
#		target = content.get('target')
#		count = content.get('count')
#
#		if target and isinstance(count, int):
#			rss_gauge.labels(target=target).set(count)
#			return {'status': 'ok'}, 200
#		else:
#			return {'status': 'error', 'reason': 'invalid data'}, 400
#
#	except Exception as e:
#		return {'status': 'error', 'reason': str(e)}, 500

# Run Flask Server
# 정의: Exporter는 독립 실행형으로 메트릭을 제공하는 HTTP Server 형태로 동작
# 이유: Prometheus는 주기적으로 HTTP로 scrape 하므로 서버가 반드시 필요
# 확장성: 0.0.0.0 설정을 통해 클러스터 내 서비스로 접근 가능하게 함
# 대체제: Gunicorn, uvicorn 등으로 Production 최적화 가능
if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
