import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit 페이지 설정
st.set_page_config(page_title="Titanic 데이터 시각화 대시보드", layout="wide")

# 제목
st.title("🚢 Titanic 데이터 시각화 대시보드")
st.markdown("---")

# 데이터 생성 함수
@st.cache_data
def generate_titanic_data():
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate random data for 500 passengers
    n_passengers = 500
    
    # Generate gender data (Male: 65%, Female: 35%)
    sex = np.random.choice(['Male', 'Female'], size=n_passengers, p=[0.65, 0.35])
    
    # Generate age data (normal distribution with mean=29, std=14, clipped between 0 and 80)
    age = np.clip(np.random.normal(29, 14, n_passengers), 0, 80).round().astype(int)
    
    # Generate passenger class data (1st: 20%, 2nd: 30%, 3rd: 50%)
    pclass = np.random.choice([1, 2, 3], size=n_passengers, p=[0.2, 0.3, 0.5])
    
    # Generate embarkation port data (S: Southampton, C: Cherbourg, Q: Queenstown)
    embarked = np.random.choice(['C', 'Q', 'S'], size=n_passengers, p=[0.2, 0.1, 0.7])
    
    # Generate fare data based on passenger class
    fare = np.zeros(n_passengers)
    for i in range(n_passengers):
        if pclass[i] == 1:
            fare[i] = np.random.normal(80, 20)  # Higher fare for 1st class
        elif pclass[i] == 2:
            fare[i] = np.random.normal(40, 10)  # Medium fare for 2nd class
        else:
            fare[i] = np.random.normal(20, 5)   # Lower fare for 3rd class
    fare = np.clip(fare, 5, 150).round(2)  # Clip fares between 5 and 150
    
    # Generate survival data based on gender, age, and class
    survival_prob = np.zeros(n_passengers)
    for i in range(n_passengers):
        base_prob = 0.3  # Base survival probability
        
        # Women had higher survival rates
        if sex[i] == 'Female':
            base_prob += 0.3
        
        # Higher class had better survival rates
        if pclass[i] == 1:
            base_prob += 0.2
        elif pclass[i] == 2:
            base_prob += 0.1
            
        # Children and elderly had different survival rates
        if age[i] < 15:
            base_prob += 0.1
        elif age[i] > 60:
            base_prob -= 0.1
            
        survival_prob[i] = np.clip(base_prob, 0.1, 0.9)
    
    survived = np.random.binomial(1, survival_prob)
    
    # Create DataFrame
    df = pd.DataFrame({
        'Sex': sex,
        'Age': age,
        'Pclass': pclass,
        'Embarked': embarked,
        'Fare': fare,
        'Survived': survived
    })
    
    return df

# 데이터 생성
df = generate_titanic_data()

# 데이터 개요
st.subheader("📊 데이터 개요")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("총 승객 수", len(df))
with col2:
    st.metric("생존자 수", df['Survived'].sum())
with col3:
    st.metric("생존율", f"{df['Survived'].mean():.1%}")
with col4:
    st.metric("평균 나이", f"{df['Age'].mean():.1f}세")

# 데이터 미리보기
st.subheader("🔍 데이터 미리보기")
st.dataframe(df.head(10), use_container_width=True)

st.markdown("---")

# 시각화 섹션
st.subheader("📈 데이터 시각화")

# 세 개의 그래프를 하나의 subplot으로 생성
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

# 첫 번째 그래프: 성별별 생존율
survival_by_sex = df.groupby('Sex')['Survived'].mean().reset_index()
sns.barplot(data=survival_by_sex, x='Sex', y='Survived', hue='Sex', palette='viridis', legend=False, ax=ax1)
ax1.set_title('Survival Rate by Gender', fontsize=12, fontweight='bold')
ax1.set_xlabel('Gender', fontsize=10)
ax1.set_ylabel('Survival Rate', fontsize=10)
ax1.set_ylim(0, 1)

# 값 표시
for i, v in enumerate(survival_by_sex['Survived']):
    ax1.text(i, v + 0.02, f'{v:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=9)

# 두 번째 그래프: 나이 분포
sns.histplot(data=df, x='Age', bins=20, kde=True, color='skyblue', ax=ax2)
ax2.set_title('Age Distribution of Passengers', fontsize=12, fontweight='bold')
ax2.set_xlabel('Age', fontsize=10)
ax2.set_ylabel('Frequency', fontsize=10)
ax2.axvline(df['Age'].mean(), color='red', linestyle='--', 
            label=f'Mean: {df["Age"].mean():.1f} years')
ax2.legend(fontsize=8)

# 세 번째 그래프: Pclass별 요금 평균
fare_by_class = df.groupby('Pclass')['Fare'].mean().reset_index()
sns.barplot(data=fare_by_class, x='Pclass', y='Fare', hue='Pclass', palette='Set2', legend=False, ax=ax3)
ax3.set_title('Average Fare by Passenger Class', fontsize=12, fontweight='bold')
ax3.set_xlabel('Passenger Class', fontsize=10)
ax3.set_ylabel('Average Fare ($)', fontsize=10)

# 값 표시
for i, v in enumerate(fare_by_class['Fare']):
    ax3.text(i, v + 1, f'${v:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=9)

plt.tight_layout()
st.pyplot(fig)

# 추가 인사이트
st.markdown("---")
st.subheader("🎯 주요 인사이트")

insight_col1, insight_col2, insight_col3 = st.columns(3)

with insight_col1:
    female_survival = df[df['Sex'] == 'Female']['Survived'].mean()
    male_survival = df[df['Sex'] == 'Male']['Survived'].mean()
    st.info(f"**성별 생존율 차이**\n\n여성: {female_survival:.1%}\n/ 남성: {male_survival:.1%}")

with insight_col2:
    class1_fare = df[df['Pclass'] == 1]['Fare'].mean()
    class3_fare = df[df['Pclass'] == 3]['Fare'].mean()
    st.info(f"**요금 차이**\n\n1등석: {class1_fare:.1f}\n/ 3등석: {class3_fare:.1f}")

with insight_col3:
    young_survival = df[df['Age'] < 15]['Survived'].mean()
    adult_survival = df[(df['Age'] >= 15) & (df['Age'] < 60)]['Survived'].mean()
    st.info(f"**연령별 생존율**\n\n어린이(<15세): {young_survival:.1%}\n/ 성인(15-59세): {adult_survival:.1%}")

# 데이터 다운로드 옵션
st.markdown("---")
st.subheader("💾 데이터 다운로드")

csv = df.to_csv(index=False)
st.download_button(
    label="CSV 파일로 다운로드",
    data=csv,
    file_name='titanic_random_data.csv',
    mime='text/csv'
)
