# 🤖 Art Robo: 도형 그리기 협동로봇 키오스크

원하는 모양을 선택하면 **두산 협동로봇**이 실시간으로 그림을 그려주는 키오스크 프로그램입니다. 
PyQt5를 활용한 UI와 Modbus TCP 통신을 기반으로 제작되었습니다.

---

## 📱 주요 화면 구성

| 메인 화면 | 도형 선택 | 그리기 대기 |
| :---: | :---: | :---: |
| <img src="https://github.com/user-attachments/assets/ce2e1736-1691-4bf0-ab0a-2574aea22d20" width="250"> | <img src="https://github.com/user-attachments/assets/a6ded0a3-ed67-4235-af18-e8ae48dd9c18" width="250"> | <img src="https://github.com/user-attachments/assets/f28a4185-9a8a-4bcc-94f4-34c97318678a" width="250"> |
| 터치 시 시작 | 5종의 도형 선택 가능 | 실시간 진행률 표시 |

| 완료 및 복귀 | 데이터 분석 보고서 |
| :---: | :---: |
| <img src="https://github.com/user-attachments/assets/5c395d1a-0c3b-48f0-989c-78558580baee" width="250"> | <img src="https://github.com/user-attachments/assets/89f7d07a-4e45-441c-a2dd-424aa5087d30" width="350"> |
| 메인으로 복귀 기능 | 날짜별 이용 현황 요약 |

---

## 🛠 주요 기능 및 기술 스택

### 1. 사용자 중심 UI/UX
- **Framework:** `PyQt5`
- 사용자가 직관적으로 도형을 선택하고 로봇의 상태를 확인할 수 있는 인터페이스 제공

### 2. 로봇 제어 및 통신
- **Protocol:** `Modbus TCP`
- **Robot:** `Doosan Robotics (협동로봇)`
- Modbus 신호를 통해 로봇의 좌표 데이터 및 동작 시퀀스 제어

### 3. 데이터 분석 (Business Intelligence)
- 일일 가동 횟수 및 인기 도형 통계 생성
- 시간대별 방문객 유동성 분석 기능을 통해 운영 효율성 제고

---

## ✍️ 학습 내용
- 로봇 티칭 및 좌표 시스템 이해
- Modbus TCP를 이용한 외부 기기(PC-Robot) 통신 구현
- 데이터 로그 기반의 요약 보고서 자동화 로직 개발
