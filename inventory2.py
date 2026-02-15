import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="재고 관리 자동화 시스템", layout="wide")

st.title("📦 비즈니스 재고 관리 시스템")

# --- [기능 1] 엑셀 템플릿 생성 함수 ---
def create_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # 시트 1: 현재재고
        stock_data = pd.DataFrame({
            "제품명": ["센소다인", "파로돈탁스", "폴리덴트 의치 세정제"],
            "현재수량": [0, 0, 0]
        })
        stock_data.to_excel(writer, sheet_name='현재재고', index=False)
        
        # 시트 2: 샘플링실적
        history_data = pd.DataFrame({
            "주차": ["1주차", "2주차", "3주차"] * 3,
            "제품명": ["센소다인"]*3 + ["파로돈탁스"]*3 + ["폴리덴트 의치 세정제"]*3,
            "대학병원샘플링": [0] * 9,
            "클리닉샘플링": [0] * 9
        })
        history_data.to_excel(writer, sheet_name='샘플링실적', index=False)
    return output.getvalue()

# --- [기능 2] 메인 화면 다운로드 섹션 ---
st.subheader("📌 단계 1: 양식 다운로드 및 작성")
col1, col2 = st.columns([1, 3])
with col1:
    template_file = create_template()
    st.download_button(
        label="📥 엑셀 템플릿 받기",
        data=template_file,
        file_name="inventory_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="이 버튼을 눌러 양식을 다운로드하세요!"
    )
with col2:
    st.write("<- 왼쪽 버튼을 눌러 엑셀을 받고 내용을 채워주세요.")

st.divider() # 구분선

# --- [기능 3] 데이터 입력 및 분석 ---
st.subheader("📌 단계 2: 정보 입력 및 파일 업로드")

conf_count = st.number_input("이번 달 예정 학회 건수 (숫자만 입력)", min_value=0, value=0)
uploaded_file = st.file_uploader("작성 완료된 엑셀 파일을 여기에 끌어다 놓으세요", type=['xlsx'])

if uploaded_file:
    try:
        df_stock = pd.read_excel(uploaded_file, sheet_name='현재재고')
        df_history = pd.read_excel(uploaded_file, sheet_name='샘플링실적')

        results = []
        target_products = ["센소다인", "파로돈탁스", "폴리덴트 의치 세정제"]

        for prod in target_products:
            curr_row = df_stock[df_stock['제품명'] == prod]
            if curr_row.empty: continue
            current_inv = curr_row['현재수량'].values[0]

            prod_history = df_history[df_history['제품명'] == prod]
            avg_uni = prod_history['대학병원샘플링'].mean()
            avg_clinic = prod_history['클리닉샘플링'].mean()

            # 수정된 공식: (학회*400) + (대학병원평균*4) + (클리닉평균*4)
            optimal_inv = int((conf_count * 400) + (avg_uni * 4) + (avg_clinic * 4))

            status = "✅ 정상" if current_inv >= optimal_inv else "🚨 재고 부족"
            
            results.append({
                "제품명": prod,
                "현재 재고": current_inv,
                "적정 재고": optimal_inv,
                "상태": status,
                "필요 발주량": max(0, optimal_inv - current_inv)
            })

        st.subheader("📊 최종 분석 리포트")
        report_df = pd.DataFrame(results)
        
        # 강조 표시
        def highlight_alert(val):
            return 'background-color: #ffcccc' if val == "🚨 재고 부족" else ''

        st.table(report_df.style.applymap(highlight_alert, subset=['상태']))

    except Exception as e:
        st.error(f"오류 발생: 템플릿 시트 이름이나 컬럼명이 변경되었는지 확인해주세요. ({e})")
