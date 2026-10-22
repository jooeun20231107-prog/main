import io
from datetime import date
from html import escape
from eventon_space import make_layout_image

def build_report(data,p,author='',company=''):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,Table,TableStyle
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.lib.pagesizes import A4
    pdfmetrics.registerFont(UnicodeCIDFont('HYSMyeongJo-Medium'))
    styles=getSampleStyleSheet()
    body=ParagraphStyle('KR',fontName='HYSMyeongJo-Medium',fontSize=9,leading=14,spaceAfter=6)
    title=ParagraphStyle('KT',parent=body,fontSize=19,leading=27,textColor=colors.HexColor('#2563eb'),spaceAfter=12)
    heading=ParagraphStyle('KH',parent=body,fontSize=12,leading=18,spaceBefore=12,spaceAfter=7)
    def P(s,style=body):return Paragraph(escape(str(s)).replace('\n','<br/>'),style)
    out=io.BytesIO();doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=17*mm,rightMargin=17*mm,topMargin=17*mm,bottomMargin=17*mm)
    story=[P('Event ON · 행사 공간 설계 보고서',title),P(data['name'],heading),P(f"작성: {author} · 소속: {company or '미입력'} · 작성일: {date.today().isoformat()}"),P('1. 행사 개요',heading)]
    items=[('유형·목적',data.get('event_type','')+' / '+data.get('purpose','')),('장소·형태',data.get('venue','')+' / '+data.get('venue_shape','')),('일정',f"{data.get('event_date')}부터 {data.get('duration_days',1)}일 / {data.get('start_time')}–{data.get('end_time')}"),('방문객·분위기',f"총 {int(data['visitors']):,}명 / {data.get('mood')} / {data.get('age')}"),('공간 치수',f"{p['width']:g} × {p['depth']:g} m / {data.get('inside')}"),('예산·입장료',f"{int(data.get('budget',0)):,}원 / {data.get('ticket')} {int(data.get('ticket_price',0)):,}원"),('추가 요청',data.get('extra') or '없음')]
    rows=[[P(a),P(b)] for a,b in items];tbl=Table(rows,colWidths=[32*mm,144*mm]);tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#eff6ff')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#dbe3ef')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));story.append(tbl)
    story.append(P('2. 자동 배치 설계도',heading));image=make_layout_image(data,p=p);story.append(Image(image,width=176*mm,height=117*mm,kind='proportional'))
    story.append(P('3. 배치안 및 공간 지표',heading));m=p['metrics']
    for text in [f"선택 배치: {p['strategy']}",f"입구 접근 연결: {m['connected']} / {m['facilities']}개 시설",f"수요 가중 평균 접근 거리: {m['weighted_distance']} m",f"의료센터 평균 접근 거리: {m['medical_distance'] if m['medical_distance'] is not None else '산출 불가'} m",f"주요 시설 평균 이격: {m['busy_separation']} m",f"시설 점유율: {m['facility_area_pct']}% / 경로 중복 비율: {m['shared_route_pct']}%"]:story.append(P(text))
    story.append(P('4. 시설별 설계 정보',heading))
    for z in p['zones']:story.append(P(f"{z['name']}: 중심 ({z['x']:g}, {z['y']:g}) m / {z['w']:g} × {z['h']:g} m / 가정 방문 선호 {z['share']*100:.1f}% / 입구 경로 {z.get('route_distance','없음')} m"))
    story.append(P('5. 운영 검토 및 분석 가정',heading))
    story.append(P('공연장·푸드존·체험부스 주변 대기 구역을 구분하고, 입구 안내와 응급 접근 경로를 유지하도록 현장 운영 계획을 세워야 합니다. 예산은 입력한 계획 금액이며 자동 견적을 산출하지 않습니다.'))
    for warning in p['warnings']:story.append(P('확인 필요: '+warning))
    story.append(P('자동 배치는 기하 조건과 시설 선호 가중치 기반 휴리스틱입니다. 학습된 AI 모델이 아닙니다. 방문 선호는 실제 방문 확률을 검증한 값이 아니며, 경로 중복 비율은 가중 수요 합계가 0.6을 넘는 최단경로 셀의 비율입니다. 의료 평균 거리는 도달 가능한 시설만 포함하므로 미연결 시설도 별도로 확인해야 합니다.'))
    story.append(P('화면의 이동 시뮬레이션은 개별 가상 에이전트의 목적·속도·체류·감속·회피를 표현합니다. 표시 인원은 총 방문객 또는 실측 체류 인원과 다릅니다. 브라우저 실행 중의 체류 분포 및 이동 기록은 이 PDF나 프로젝트에 저장되지 않습니다.'))
    story.append(P('※ 실측 도면·고정 장애물·출입구 폭·안전 기준 검토가 필요합니다. 본 자료는 실제 혼잡 예측, 대피 검증, 안전 인증을 대체하지 않습니다. 사용자 추가 요청은 보고서에 기록되며 자연어 요청을 자동으로 공간 제약으로 해석하지 않습니다.'))
    def footer(c,doc):
        c.setFont('HYSMyeongJo-Medium',8);c.setFillColor(colors.HexColor('#64748b'));c.drawString(17*mm,10*mm,'Event ON · 기획용 설계 초안');c.drawRightString(193*mm,10*mm,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer);return out.getvalue()
