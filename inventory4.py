import streamlit as st
import pandas as pd
import io

# 페이지 설정
st.set_page_config(page_title="헤일리온 재고 관리 자동화 시스템", layout="wide")

st.title("📦 헤일리온 제품군별 재고 관리 시스템")

# --- [기능 1] 업데이트된 제품 리스트 정의 ---
# 제품별로 그룹화하여 관리하기 쉽게 리스트를 만듭니다.
PRODUCT_LIST = [
    "센소다인 멀티케어 18g",
    "센소다인 멀티케어 14g",
    "센소다인 검케어 14g",
    "파로돈탁스 쿨링민트 18g",
    "파로돈탁스 쿨링민트 14g",
    "파로돈탁스 AGR 14g",
    "폴리덴트 의치용 세정제 6T",
    "폴리덴트 교정기용 세정제 6T"
]

# --- [기능 2] 엑셀 템플릿 생성 함수 (제품 리스트 반영) ---
def create_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 시트 1: 현재재고
        stock_data = pd.DataFrame({
            "제품명": PRODUCT_LIST,
            "현재수량": [0] * len(PRODUCT_LIST)
        })
        stock_data.to_excel(writer, sheet_name='현재재고', index=False)
        
        # 시트 2: 샘플링실적 (3주차 데이터 틀 제공)
        history_rows = []
        for prod in PRODUCT_LIST:
            for week in ["1주차", "2주차", "3주차"]:
                history_rows.append([week, prod, 0, 0])
        
        history_data = pd.DataFrame(history_rows, columns=["주차", "제품명", "대학병원샘플링", "클리닉샘플링"])
        history_data.to_excel(writer, sheet_name='샘플링실적', index=False)
    return output.getvalue()

# --- [기능 3] 메인 화면 레이아웃 ---
st.subheader("📌 단계 1: 양식 다운로드 및 작성")
col1, col2 = st.columns([1, 3])
with col1:
    template_file = create_template()
    st.download_button(
        label="📥 업데이트된 템플릿 받기",
        data=template_file,
        file_name="haleon_inventory_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
with col2:
    st.write("<- 버튼을 눌러 새 제품 리스트가 포함된 엑셀을 받으세요.")

st.divider()

st.subheader("📌 단계 2: 정보 입력 및 파일 업로드")
conf_count = st.number_input("이번 달 예정 학회 건수 (숫자만 입력)", min_value=0, value=0)
uploaded_file = st.file_uploader("작성 완료된 엑셀 파일을 업로드하세요", type=['xlsx'])

if uploaded_file:
    try:
        df_stock = pd.read_excel(uploaded_file, sheet_name='현재재고')
        df_history = pd.read_excel(uploaded_file, sheet_name='샘플링실적')

        results = []

        for prod in PRODUCT_LIST:
            # 현재 재고 데이터 가져오기
            curr_row = df_stock[df_stock['제품명'] == prod]
            if curr_row.empty: continue
            current_inv = curr_row['현재수량'].values[0]

            # 과거 3주 데이터 평균 계산
            prod_history = df_history[df_history['제품명'] == prod]
            avg_uni = prod_history['대학병원샘플링'].mean() if not prod_history.empty else 0
            avg_clinic = prod_history['클리닉샘플링'].mean() if not prod_history.empty else 0

            # 적정재고 공식 적용: (학회*400) + (대학병원평균*4) + (클리닉평균*4)
            optimal_inv = int((conf_count * 400) + (avg_uni * 4) + (avg_clinic * 4))

            status = "✅ 정상" if current_inv >= optimal_inv else "🚨 재고 부족"
            
            results.append({
                "제품명": prod,
                "현재 재고": current_inv,
                "적정 재고": optimal_inv,
                "상태": status,
                "필요 발주량": max(0, optimal_inv - current_inv)
            })

        # 결과 리포트 출력
        st.subheader("📊 최종 분석 리포트")
        report_df = pd.DataFrame(results)
        
        # 상태에 따른 배경색 하이라이트
        def highlight_alert(val):
            return 'background-color: #ffcccc' if val == "🚨 재고 부족" else ''

        st.table(report_df.style.applymap(highlight_alert, subset=['상태']))

        # 부족분 합계 알림
        shortage_items = report_df[report_df['필요 발주량'] > 0]
        if not shortage_items.empty:
            st.error(f"총 {len(shortage_items)}개 품목의 재고가 부족합니다. 발주가 필요합니다.")

    except Exception as e:
        st.error(f"오류가 발생했습니다. 템플릿 양식을 확인해 주세요: {e}")