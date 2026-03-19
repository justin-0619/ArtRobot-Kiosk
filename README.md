원하는 모양을 고르면 로봇이 그려주는 키오스크 프로그램을 개발.
요약보고서를 통한 사용자(고객)에 대한 분석이 가능하게 기능을 추가.

ui는 pyqt5를 통해 제작, 통신은 모드버스 TCP를 사용, 로봇은 두산협동로봇을 사용


프로그램을 실행하면 메인화면으로 시작
<img width="1079" height="1919" alt="메인" src="https://github.com/user-attachments/assets/ce2e1736-1691-4bf0-ab0a-2574aea22d20" />

메인화면을 터치하면 사용자가 원하는 모양을 선택 가능한 페이지로 전환되며 원하는 모양을 선택 후 그리기 시작 버튼을 터치
<img width="1079" height="1919" alt="그림 고르는 페이지" src="https://github.com/user-attachments/assets/a6ded0a3-ed67-4235-af18-e8ae48dd9c18" />

로봇이 신호를 받고 원하는 모양을 그리기 시작, 실시간으로 화면에 그림이 그려지는 것을 간단하게 확인 가능
<img width="1079" height="1919" alt="대기 페이지_최신" src="https://github.com/user-attachments/assets/f28a4185-9a8a-4bcc-94f4-34c97318678a" />

그림이 완성되면 아래와 같은 화면이 뜨고 처음으로 버튼을 터치하면 다시 메인화면으로 복귀
<img width="1079" height="1919" alt="마무리" src="https://github.com/user-attachments/assets/5c395d1a-0c3b-48f0-989c-78558580baee" />

날짜별 요약보고서를 생성하는 기능 (총 가동 횟수, 해당 날짜에 가장 많이 그린 모양, 가장 많이 이용한 시간대, 모양별 그린 횟수)
-> 이를 통해 사용자(고객)에 대한 데이터 분석이 가능. 사용자들이 가장 선호하는 모양, 고객이 가장 몰리는 시간등
<img width="296" height="251" alt="미술로봇 보고서" src="https://github.com/user-attachments/assets/89f7d07a-4e45-441c-a2dd-424aa5087d30" />

간단하게 로봇과의 통신 및 로봇 티칭, 프로그램 개발에 대해 공부를 하였음
