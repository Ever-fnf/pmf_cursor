🎯 **데이터 분석 Streamlit 대시보드 프로젝트 모음 리포지토리**

이 리포지토리는 다양한 분석 목적의 Streamlit 앱들을 한 곳에서 관리하기 위해 구성되었습니다.  
각 앱은 별도의 폴더로 구성되어 있으며, 독립적으로 실행 및 배포가 가능합니다.  
Cursor AI를 활용하여 만든 대시보드입니다.  

---

## 📁 프로젝트 구조
pmf_cursor/  
├── ga4/ # GA4 트래픽 분석 대시보드  
│ ├── streamlit_ga4.py  
│ └── requirements.txt  
├── titanic/ # Titanic 생존 시각화 대시보드  
│ ├── streamlit_titanic.py  
│ └── requirements.txt  
├── .gitignore  
└── README.md  

---

## 📊 배포된 앱 링크

- 🔗 [GA4 트래픽 분석 대시보드](https://pmf-ga4.streamlit.app/)
- 🔗 [Titanic 시각화 대시보드](https://pmf-titanic2.streamlit.app/)

---

## 🚀 사용 방법

각 앱 폴더에서 아래 명령으로 실행 가능합니다.

```bash
# 예시: GA4
cd ga4
pip install -r requirements.txt
streamlit run streamlit_ga4.py


