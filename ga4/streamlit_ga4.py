import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
import io

# 페이지 설정
st.set_page_config(
    page_title="GA4 데이터 분석 대시보드",
    page_icon="📊",
    layout="wide"
)

# 제목
st.title('GA4 데이터 분석 대시보드 📊')

def convert_df_to_csv(df):
    """데이터프레임을 CSV 문자열로 변환합니다."""
    return df.to_csv(index=False).encode('utf-8-sig')  # UTF-8 with BOM for Excel compatibility

def create_download_button(data, file_name, button_text):
    """다운로드 버튼을 생성합니다."""
    csv = convert_df_to_csv(data)
    st.download_button(
        label=f"📥 {button_text}",
        data=csv,
        file_name=file_name,
        mime='text/csv'
    )

def display_kpi_metrics(df):
    """주요 KPI 지표를 계산하고 표시합니다."""
    # 구매 전환 관련 데이터 계산
    purchase_data = df[df['event_name'] == 'purchase']
    total_purchases = purchase_data['users'].sum()
    
    # 최대 구매 발생일 계산
    if not purchase_data.empty:
        max_purchase_date = purchase_data.groupby('date')['users'].sum().idxmax()
        max_purchase_count = purchase_data.groupby('date')['users'].sum().max()
    else:
        max_purchase_date = None
        max_purchase_count = 0
    
    # 채널별 전환율 계산
    channel_pageviews = df[df['event_name'] == 'page_view'].groupby('source_medium')['users'].sum()
    channel_purchases = df[df['event_name'] == 'purchase'].groupby('source_medium')['users'].sum()
    
    # 전환율 계산을 위해 데이터프레임 생성
    channel_conversion = pd.DataFrame({
        'pageviews': channel_pageviews,
        'purchases': channel_purchases
    }).fillna(0)  # NaN 값을 0으로 채움
    
    # 전환율 계산
    channel_conversion['conversion_rate'] = (
        channel_conversion['purchases'] / channel_conversion['pageviews'] * 100
    ).round(2)
    
    # 전환율이 가장 높은 채널 찾기 (0으로 나누기 방지)
    channel_conversion = channel_conversion[channel_conversion['pageviews'] > 0]  # 페이지뷰가 0인 채널 제외
    if not channel_conversion.empty:
        best_channel_idx = channel_conversion['conversion_rate'].idxmax()
        best_channel = {
            'source_medium': best_channel_idx,
            'conversion_rate': channel_conversion.loc[best_channel_idx, 'conversion_rate']
        }
    else:
        best_channel = {
            'source_medium': "데이터 없음",
            'conversion_rate': 0
        }
    
    # KPI 메트릭 표시
    st.markdown("### 📈 핵심 성과 지표")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="총 전환 수",
            value=f"{total_purchases:,}",
            help="총 purchase 이벤트 발생 횟수"
        )
    
    with col2:
        st.metric(
            label="최고 전환율 채널",
            value=f"{best_channel['source_medium']}",
            delta=f"{best_channel['conversion_rate']:.1f}%",
            help="방문자 대비 구매 전환율이 가장 높은 채널"
        )
    
    with col3:
        if max_purchase_date:
            st.metric(
                label="최대 구매 발생일",
                value=max_purchase_date.strftime('%Y-%m-%d'),
                delta=f"{max_purchase_count:,}건",
                help="하루 동안 가장 많은 구매가 발생한 날짜"
            )
        else:
            st.metric(
                label="최대 구매 발생일",
                value="데이터 없음",
                delta="0건"
            )
    
    st.markdown("---")  # 구분선 추가

# 데이터 로딩 함수
@st.cache_data
def load_data(uploaded_file):
    """CSV 파일을 로드하고 기본적인 전처리를 수행합니다."""
    df = pd.read_csv(uploaded_file)
    
    # 필수 컬럼 확인
    required_columns = ['date', 'source_medium', 'sessions', 'users', 'new_users', 
                       'device_category', 'event_name', 'step']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"CSV 파일에 다음 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
        st.write("필요한 컬럼:")
        for col in required_columns:
            st.write(f"- {col}")
        st.stop()
    
    # 날짜 컬럼 변환
    try:
        df['date'] = pd.to_datetime(df['date'])
    except Exception as e:
        st.error("날짜 형식이 올바르지 않습니다. YYYY-MM-DD 형식인지 확인해주세요.")
        st.stop()
    
    return df

# 퍼널 단계 정의
FUNNEL_STEPS = ['page_view', 'login', 'view_item', 'add_to_cart', 'begin_checkout', 'purchase']

def create_funnel_chart(filtered_df):
    """퍼널 차트를 생성합니다."""
    # 기본 퍼널 데이터 계산
    funnel_data = []
    prev_users = None
    prev_step = None
    
    for step in FUNNEL_STEPS:
        step_users = filtered_df[filtered_df['event_name'] == step]['users'].sum()
        conversion_from_start = (step_users / filtered_df[filtered_df['event_name'] == FUNNEL_STEPS[0]]['users'].sum() * 100).round(1)
        
        # 이전 단계 대비 전환율 계산
        step_to_step_rate = None
        if prev_users is not None and prev_users > 0:
            step_to_step_rate = (step_users / prev_users * 100).round(1)
        
        # 통합된 메트릭 라벨 생성 (2줄로 구성)
        main_metrics = f"{step_users:,.0f}명 (전체 대비 {conversion_from_start:.1f}%)"
        step_conversion = f"이전 단계 전환율: {step_to_step_rate:.1f}%" if step_to_step_rate is not None else ""
        
        funnel_data.append({
            'step': step,
            'users': step_users,
            'conversion_from_start': conversion_from_start,
            'step_to_step_rate': step_to_step_rate,
            'main_metrics': main_metrics,
            'step_conversion': step_conversion
        })
        
        prev_users = step_users
        prev_step = step
    
    funnel_df = pd.DataFrame(funnel_data)
    
    # 기본 막대 차트
    bars = alt.Chart(funnel_df).mark_bar().encode(
        y=alt.Y('step:N', 
                sort=FUNNEL_STEPS,
                title='퍼널 단계'),
        x=alt.X('users:Q',
                title='사용자 수'),
        tooltip=[
            alt.Tooltip('step:N', title='단계'),
            alt.Tooltip('users:Q', title='사용자 수', format=','),
            alt.Tooltip('conversion_from_start:Q', title='전체 전환율', format='.1f'),
            alt.Tooltip('step_to_step_rate:Q', title='이전 단계 대비 전환율', format='.1f')
        ]
    )
    
    # 주요 메트릭 텍스트 (사용자 수 + 전체 전환율)
    main_metrics_text = alt.Chart(funnel_df).mark_text(
        align='left',
        baseline='middle',
        dx=5,  # 막대 끝에서 약간 띄움
        fontSize=11,
        fontWeight='bold'  # 텍스트를 진하게 표시
    ).encode(
        y=alt.Y('step:N', sort=FUNNEL_STEPS),
        x='users:Q',
        text='main_metrics'
    )
    
    # 이전 단계 전환율 텍스트 (두 번째 줄)
    conversion_text = alt.Chart(funnel_df[funnel_df['step_to_step_rate'].notna()]).mark_text(
        align='left',
        baseline='middle',
        dx=5,  # 막대 끝에서 약간 띄움
        dy=12,  # 첫 번째 텍스트보다 아래에 배치
        fontSize=10,
        color='#666666'  # 진한 회색으로 설정
    ).encode(
        y=alt.Y('step:N', sort=FUNNEL_STEPS),
        x='users:Q',
        text='step_conversion'
    )
    
    # 차트 결합
    final_chart = (bars + main_metrics_text + conversion_text).properties(
        width=800,  # 너비 증가하여 긴 텍스트 수용
        height=min(len(funnel_df) * 70, 500)  # 각 단계별 높이 증가
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=13
    ).configure_view(
        strokeWidth=0
    )
    
    # 데이터 다운로드를 위한 DataFrame 생성
    download_df = pd.DataFrame({
        '단계': funnel_df['step'],
        '사용자 수': funnel_df['users'],
        '전체 대비 전환율(%)': funnel_df['conversion_from_start'],
        '이전 단계 대비 전환율(%)': funnel_df['step_to_step_rate']
    })
    
    # 다운로드 버튼 생성
    create_download_button(
        download_df,
        '퍼널_분석_데이터.csv',
        '퍼널 분석 데이터 다운로드'
    )
    
    return final_chart

def create_users_chart(filtered_df):
    """신규/기존 사용자 차트를 생성합니다."""
    # 일별 사용자 집계
    users_df = filtered_df.groupby('date').agg({
        'users': 'sum',
        'new_users': 'sum'
    }).reset_index()
    
    users_df['returning_users'] = users_df['users'] - users_df['new_users']
    users_df['new_users_ratio'] = (users_df['new_users'] / users_df['users'] * 100).round(1)
    
    # 신규 사용자 비율의 통계값 계산
    ratio_mean = users_df['new_users_ratio'].mean()
    ratio_std = users_df['new_users_ratio'].std()
    users_df['is_significant'] = abs(users_df['new_users_ratio'] - ratio_mean) > (1.5 * ratio_std)
    users_df['significant_label'] = users_df.apply(
        lambda x: f"신규 유입 급증 ({x['new_users_ratio']:.1f}%)" if x['is_significant'] else "", 
        axis=1
    )
    
    # 1. 누적 막대 차트 데이터 준비
    users_melted = pd.melt(
        users_df,
        id_vars=['date'],
        value_vars=['new_users', 'returning_users'],
        var_name='user_type',
        value_name='count'
    )
    users_melted['user_type'] = users_melted['user_type'].map({
        'new_users': '신규 사용자',
        'returning_users': '기존 사용자'
    })
    
    # 누적 막대 차트
    bar_chart = alt.Chart(users_melted).mark_bar().encode(
        x=alt.X('date:T', title='날짜'),
        y=alt.Y('count:Q', title='사용자 수'),
        color=alt.Color('user_type:N', 
                       scale=alt.Scale(domain=['신규 사용자', '기존 사용자'],
                                     range=['#1f77b4', '#ff7f0e']),
                       title='사용자 유형'),
        tooltip=[
            alt.Tooltip('date:T', title='날짜'),
            alt.Tooltip('user_type:N', title='유형'),
            alt.Tooltip('count:Q', title='사용자 수', format=',')
        ]
    ).properties(
        title='일별 신규/기존 사용자 수',
        height=300
    )
    
    # 2. 신규 사용자 비율 라인 차트
    line_base = alt.Chart(users_df).encode(
        x=alt.X('date:T', title='날짜')
    )
    
    # 기준선 (평균)
    mean_line = line_base.mark_rule(
        strokeDash=[4, 4],
        stroke='gray',
        opacity=0.5
    ).encode(
        y=alt.Y(
            datum=ratio_mean,
            title='신규 사용자 비율 (%)'
        )
    )
    
    # 비율 라인
    ratio_line = line_base.mark_line(
        color='red'
    ).encode(
        y=alt.Y('new_users_ratio:Q',
                title='신규 사용자 비율 (%)',
                scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('date:T', title='날짜'),
            alt.Tooltip('new_users_ratio:Q', title='신규 사용자 비율', format='.1f')
        ]
    )
    
    # 유의한 포인트 표시
    significant_points = line_base.mark_point(
        color='red',
        size=100
    ).encode(
        y=alt.Y('new_users_ratio:Q'),
        opacity=alt.condition(
            'datum.is_significant == true',
            alt.value(1),
            alt.value(0)
        )
    )
    
    # 유의한 포인트 레이블
    text_labels = line_base.mark_text(
        align='left',
        baseline='bottom',
        dx=5,
        dy=-5,
        fontSize=11
    ).encode(
        y=alt.Y('new_users_ratio:Q'),
        text='significant_label',
        opacity=alt.condition(
            'datum.is_significant == true',
            alt.value(1),
            alt.value(0)
        )
    )
    
    ratio_chart = (ratio_line + mean_line + significant_points + text_labels).properties(
        title=f'신규 사용자 비율 추이 (평균: {ratio_mean:.1f}%)',
        height=300
    )
    
    # 데이터 다운로드를 위한 DataFrame 생성
    download_df = pd.DataFrame({
        '날짜': users_df['date'],
        '전체 사용자': users_df['users'],
        '신규 사용자': users_df['new_users'],
        '재방문 사용자': users_df['returning_users'],
        '신규 사용자 비율(%)': users_df['new_users_ratio']
    })
    
    # 다운로드 버튼 생성
    create_download_button(
        download_df,
        '사용자_유형_분석_데이터.csv',
        '사용자 유형 분석 데이터 다운로드'
    )
    
    return bar_chart, ratio_chart

def create_purchase_trend_chart(filtered_df):
    """구매 추이 차트를 생성합니다."""
    # 구매 이벤트 데이터 집계
    purchase_df = filtered_df[filtered_df['event_name'] == 'purchase'].groupby('date')['users'].sum().reset_index()
    
    if len(purchase_df) == 0:
        return alt.Chart().mark_text().encode(
            text=alt.value('구매 데이터가 없습니다.')
        ).properties(
            width=600,
            height=300
        )
    
    # 최대값 찾기
    max_point = purchase_df.loc[purchase_df['users'].idxmax()]
    max_date_str = max_point['date'].strftime('%Y-%m-%d')
    max_users = int(max_point['users'])
    
    max_df = pd.DataFrame([{
        'date': max_point['date'],
        'users': max_users
    }])
    
    # 기본 라인 차트
    base = alt.Chart(purchase_df).encode(
        x=alt.X('date:T',
                title='날짜',
                axis=alt.Axis(
                    format='%Y-%m-%d',
                    labelAngle=0,  # 날짜 라벨을 수평으로
                    labelOverlap=False,  # 라벨 겹침 방지
                    labelPadding=10,  # 라벨 여백 추가
                    tickCount=5,  # 표시할 틱 개수 조정
                    titlePadding=20  # 축 제목 여백
                )),
        y=alt.Y('users:Q',
                title='구매 사용자 수',
                axis=alt.Axis(
                    labelPadding=10,  # 라벨 여백 추가
                    titlePadding=20,  # 제목 여백 추가
                    offset=10  # 축과 차트 사이 여백
                )),
        tooltip=[
            alt.Tooltip('date:T', title='날짜', format='%Y-%m-%d'),
            alt.Tooltip('users:Q', title='구매 사용자 수', format=',')
        ]
    ).properties(
        width=600,
        height=400  # 높이 증가
    )
    
    # 라인
    line = base.mark_line()
    
    # 일반 포인트
    points = base.mark_circle(size=60)
    
    # 최대값 포인트 강조
    max_point = alt.Chart(max_df).mark_circle(
        color='red',
        size=200,
        opacity=1
    ).encode(
        x=alt.X('date:T'),
        y=alt.Y('users:Q'),
        tooltip=[
            alt.Tooltip('date:T', title='최다 구매 발생일', format='%Y-%m-%d'),
            alt.Tooltip('users:Q', title='구매 사용자 수', format=',')
        ]
    )
    
    # 최대값 레이블 추가
    max_label = alt.Chart(max_df).mark_text(
        align='left',
        baseline='bottom',
        dx=5,
        dy=-10,
        fontSize=11,
        fontWeight='bold'
    ).encode(
        x='date:T',
        y='users:Q',
        text=alt.value(f"{max_users:,}")
    )
    
    # 차트 결합
    final_chart = (line + points + max_point + max_label).properties(
        title={
            "text": ["일별 구매 사용자 수 추이", f"최다 구매일: {max_date_str} ({max_users:,}명)"],
            "subtitle": [""],  # 부제목을 별도 라인으로 분리
            "align": "left",
            "anchor": "start",
            "fontSize": 16,
            "dy": 20,  # 제목 위치 조정
            "offset": 20  # 제목과 차트 사이 여백
        }
    ).configure_view(
        strokeWidth=0  # 테두리 제거
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=12,
        grid=True  # 그리드 추가
    )
    
    # 데이터 다운로드를 위한 DataFrame 생성
    download_df = pd.DataFrame({
        '날짜': purchase_df['date'],
        '구매 사용자 수': purchase_df['users']
    })
    
    # 다운로드 버튼 생성
    create_download_button(
        download_df,
        '구매_추이_데이터.csv',
        '구매 추이 데이터 다운로드'
    )
    
    return final_chart

def create_event_analysis_charts(filtered_df, selected_event):
    """선택된 이벤트에 대한 분석 차트들을 생성합니다."""
    event_df = filtered_df[filtered_df['event_name'] == selected_event]
    
    # 두 열 레이아웃 생성
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(f"{selected_event} 이벤트의 소스/매체 분포")
        
        # 소스/매체 분포 데이터 준비 (전체 데이터 사용)
        source_dist = event_df.groupby('source_medium')['users'].sum().reset_index()
        total_users = source_dist['users'].sum()
        source_dist['percentage'] = (source_dist['users'] / total_users * 100).round(1)
        # 퍼센트 기호를 포함한 텍스트 컬럼 추가
        source_dist['percentage_label'] = source_dist['percentage'].apply(lambda x: f"{x:.1f}%")
        
        # 수평 막대 차트 생성
        bars = alt.Chart(source_dist).mark_bar().encode(
            y=alt.Y('source_medium:N',
                   sort=alt.EncodingSortField(field='users', op='sum', order='descending'),
                   title='소스/매체'),
            x=alt.X('users:Q', 
                   title='사용자 수'),
            tooltip=[
                alt.Tooltip('source_medium:N', title='소스/매체'),
                alt.Tooltip('users:Q', title='사용자 수', format=','),
                alt.Tooltip('percentage:Q', title='비율', format='.1f')
            ]
        )
        
        # 비율(%) 텍스트 레이블 추가
        text = alt.Chart(source_dist).mark_text(
            align='left',
            baseline='middle',
            dx=5,  # 막대 끝에서 약간 띄워서 표시
            fontSize=11
        ).encode(
            y=alt.Y('source_medium:N',
                   sort=alt.EncodingSortField(field='users', op='sum', order='descending')),
            x='users:Q',
            text='percentage_label'  # 미리 포맷팅된 텍스트 사용
        )
        
        # 차트 결합
        source_chart = (bars + text).properties(
            # 전체 소스/매체를 표시할 수 있도록 충분한 높이 확보
            height=min(len(source_dist) * 50, 800)  # 각 막대의 높이를 50px로 증가하고 최대 800px로 확장
        ).configure_axis(
            labelFontSize=11,  # 축 레이블 폰트 크기
            titleFontSize=12   # 축 제목 폰트 크기
        )
        
        # 차트 표시
        st.altair_chart(source_chart, use_container_width=True)
        
        # 총계 표시
        st.markdown(f"<h4 style='text-align: center; color: #1f77b4;'>총 {total_users:,}명</h4>", unsafe_allow_html=True)
    
    with col2:
        st.subheader(f"{selected_event} 이벤트의 기기유형 분포")
        
        # 기기 분포 데이터 준비
        device_dist = event_df.groupby('device_category')['users'].sum().reset_index()
        total_users = device_dist['users'].sum()
        device_dist['percentage'] = (device_dist['users'] / total_users * 100).round(1)
        device_dist['label'] = device_dist.apply(
            lambda x: f"{x['device_category']} ({x['percentage']:.1f}%)", axis=1
        )
        
        # 기본 파이 차트 (라벨 없이)
        pie = alt.Chart(device_dist).mark_arc(outerRadius=100).encode(
            theta=alt.Theta(field='users', type='quantitative', stack=True),
            color=alt.Color(
                'device_category:N',
                title='기기 유형',
                scale=alt.Scale(scheme='category10')
            ),
            tooltip=[
                alt.Tooltip('device_category:N', title='기기'),
                alt.Tooltip('users:Q', title='사용자 수', format=','),
                alt.Tooltip('percentage:Q', title='비율', format='.1f')
            ]
        )
        
        # 바깥쪽 레이블 (모든 기기 유형에 대해 동일하게 적용)
        text = alt.Chart(device_dist).mark_text(
            radius=120,  # 파이 차트 바깥쪽으로 고정 거리
            size=12,    # 텍스트 크기 증가
            align='left',
            baseline='middle',
            dx=8        # 약간 오른쪽으로 이동
        ).encode(
            theta=alt.Theta(
                field='users',
                type='quantitative',
                stack=True,
                sort='descending'
            ),
            text='label',
            color=alt.value('black')  # 텍스트 색상 통일
        )
        
        # 중앙 텍스트를 위한 데이터
        center_df = pd.DataFrame([{'text': f'총 {total_users:,}명'}])
        
        # 중앙 텍스트 (단순화)
        center_text = alt.Chart(center_df).mark_text(
            fontSize=14,
            fontWeight='bold',
            align='center',
            baseline='middle'
        ).encode(
            text='text:N'
        )
        
        # 차트 결합 및 표시
        device_chart = (pie + text + center_text).properties(
            width=350,  # 차트 크기 증가
            height=350
        ).configure_view(
            strokeWidth=0  # 테두리 제거
        )
        
        st.altair_chart(device_chart, use_container_width=True)

# 파일 업로더
uploaded_file = st.file_uploader("GA4 데이터 파일을 업로드하세요 (CSV)", type=['csv'])

if uploaded_file is not None:
    # 데이터 로드
    df = load_data(uploaded_file)
    
    # KPI 메트릭 표시
    display_kpi_metrics(df)
    
    # 글로벌 필터 - 사이드바에 배치
    with st.sidebar:
        st.header("분석 조건 설정 🎯")
        
        # 1. 날짜 범위 선택
        st.subheader("1. 날짜 범위")
        date_range = st.slider(
            "분석 기간을 선택하세요",
            min_value=df['date'].min().date(),
            max_value=df['date'].max().date(),
            value=(df['date'].min().date(), df['date'].max().date())
        )
        
        # 2. 소스/매체 선택
        st.subheader("2. 소스/매체")
        source_mediums = sorted(df['source_medium'].unique())
        selected_sources = st.multiselect(
            "소스/매체를 선택하세요 (미선택 시 전체)",
            options=source_mediums,
            default=[]
        )
        
        # 3. 기기 유형 선택
        st.subheader("3. 기기 유형")
        device_categories = sorted(df['device_category'].unique())
        selected_device = st.radio(
            "기기 유형을 선택하세요",
            options=['전체'] + list(device_categories)
        )
    
    # 필터 적용
    mask = (df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])
    if selected_sources:
        mask = mask & (df['source_medium'].isin(selected_sources))
    if selected_device != '전체':
        mask = mask & (df['device_category'] == selected_device)
    
    filtered_df = df[mask]
    
    # 메인 컨텐츠
    if len(filtered_df) > 0:
        # 1. 퍼널 분석
        st.subheader("1️⃣ 퍼널 분석")
        funnel_chart = create_funnel_chart(filtered_df)
        st.altair_chart(funnel_chart, use_container_width=True)
        
        # 2. 신규/기존 사용자 분석
        st.subheader("2️⃣ 신규/기존 사용자 분석")
        bar_chart, ratio_chart = create_users_chart(filtered_df)
        
        col1, col2 = st.columns(2)
        with col1:
            st.altair_chart(bar_chart, use_container_width=True)
        with col2:
            st.altair_chart(ratio_chart, use_container_width=True)
        
        # 3. 구매 전환 집중 날짜
        st.subheader("3️⃣ 구매 전환 집중 날짜")
        purchase_chart = create_purchase_trend_chart(filtered_df)
        st.altair_chart(purchase_chart, use_container_width=True)
        
        # 4. 행동 탐색 섹션
        st.subheader("4️⃣ 행동 탐색")
        selected_event = st.selectbox(
            "분석할 이벤트를 선택하세요",
            options=FUNNEL_STEPS
        )
        
        create_event_analysis_charts(filtered_df, selected_event)
    else:
        st.warning("선택한 조건에 해당하는 데이터가 없습니다. 필터 조건을 조정해 주세요.")
else:
    st.info("GA4 데이터 파일(CSV)을 업로드해 주세요.")
