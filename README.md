<div align=center>
  <img width="300" alt="image" src="https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/30303c20-4f89-492a-82e6-075ad82a9c51">
</div>

## 목차

- [목차](#목차)
- [기획배경](#기획배경)
- [개발기간](#개발기간)
- [주요 자료](#주요-자료)
- [주요 기능](#주요-기능)
- [팀 구성](#팀-구성)
- [서비스 아키텍쳐](#서비스-아키텍쳐)
- [Tech Stack](#tech-stack)
- [ERD](#erd)
- [Link](#link)

## 기획배경

- 오늘날 갈수록 심각해지는 환경오염에 따라 친환경에 대한 사회적인 관심이 높아지고 있습니다.
- 하지만 막상 어떻게 친환경을 실생활에서 실천할 수 있는지 알지 못하는 경우가 많습니다.
- 이러한 문제에 대하여 환경 캠페인 생성/참여 & 캠페인에 펀딩하기를 주요 기능으로, 친환경 상품 쇼핑 등의 부가 기능들을 가진 웹사이트를 통해 사용자들의 친환경 캠페인 참여 또는 친환경 제품 사용을 독려하고 환경에 대한인식을 재고시키고자 했습니다.

<br>

## 개발기간

- 2023/06/05 ~ 2023/07/10 (5주)

<br>

## 주요 자료

- [Notion 기획안](https://bedecked-block-34c.notion.site/EcoCanvas-19d4c100c18a408b8eb647d7201828d0?pvs=4)
- [발표영상](https://www.youtube.com/watch?v=UAir6u-uY8o)
- [Wireframe](https://www.figma.com/file/Jh0ZRKqUuXPomqyxCVQMzr/Untitled?type=design&node-id=0-1&t=kZSkorEHGW2sxhpQ-0)
- [홍보 브로셔](https://nasal-slug-513.notion.site/Eco-Canvas-dde4d75bc17c49a4885a1815a6fdf820?pvs=4)

<br>

## 주요 기능

### 회원가입, 로그인, 마이페이지

![Login](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/2847800d-e226-464e-a02b-03d777f85b97)

### 캠페인

![Campaign](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/49adb3ff-661a-4f86-a2a7-973ed8e5d4ba)

### 펀딩

![Funding](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/5443cadd-5c49-4633-9657-55a774ee2d30)

### 쇼핑

![Shop](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/a85600eb-0c96-4b08-b5b5-c340fe642a27)

### 채팅, 백오피스

![Chat](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/6a17da00-c86b-4e84-83f0-d3519f9134c6)

### 알림

![Alarm](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/26b84c62-c3ee-4506-a247-d6a0fc2e3be8)

<br>

## 팀 구성

|  이름  | 담당 기능                                                                 |
| :----: | :------------------------------------------------------------------------ |
| 박지홍 | 채팅, 백오피스, 배포, 백엔드/프론트, 프로젝트 방향성 & 전반적인 기능 검수 |
| 송지명 | 부팀장, git repository 담당, 펀딩 & 쇼핑 결제 기능, 백엔드/프론트         |
| 이주한 | 팀장, 구글 소셜 로그인, 자료 관리(readme 초안, notion 관리)               |
| 장소은 | 프로젝트 주제 & 아이디어, 카카오 소셜 로그인, 쇼핑 기능, 백엔드/프론트    |
| 최준영 | 캠페인 기능 전반, 캠페인 모델링 수정, readme 관리, 백엔드/프론트          |

<br>

## 서비스 아키텍쳐

![service_architecture](https://github.com/nueeng/EcoCanvas-Backend/assets/127704498/ea42ab94-d921-4d80-9e50-2666d85e3b39)

## Tech Stack

### Back-End

> <img src="https://img.shields.io/badge/python 3.9.10-3776AB?style=for-the-badge&logo=python&logoColor=white"> <img src="https://img.shields.io/badge/django 4.2.2-092E20?style=for-the-badge&logo=django&logoColor=white"> <img src="https://img.shields.io/badge/django rest framework 3.14.0-092E20?style=for-the-badge&logo=django&logoColor=white">

### Front-End

> <img src="https://img.shields.io/badge/html 5-E34F26?style=for-the-badge&logo=html5&logoColor=white"> <img src="https://img.shields.io/badge/css 3-1572B6?style=for-the-badge&logo=css3&logoColor=white"> <img src="https://img.shields.io/badge/javascript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=white"> <img src="https://img.shields.io/badge/react-61DAFB?style=for-the-badge&logo=react&logoColor=white">

### Server

> <img src="https://img.shields.io/badge/AMAZON EC2-FFE900?style=for-the-badge&logo=amazon&logoColor=black"> <img src="https://img.shields.io/badge/AMAZON S3-569A31?style=for-the-badge&logo=amazons3&logoColor=black"> <img src="https://img.shields.io/badge/DOCKER 20.10.12-3D97FF?style=for-the-badge&logo=docker&logoColor=white"> <img src="https://img.shields.io/badge/DOCKER COMPOSE 2.11.2-3D97FF?style=for-the-badge&logo=docker&logoColor=white"> <img src="https://img.shields.io/badge/GUNICORN-2BB530?style=for-the-badge&logo=gunicorn&logoColor=white"> <img src="https://img.shields.io/badge/NGINX 1.23.2 -2F9624?style=for-the-badge&logo=nginx&logoColor=white"> <img src="https://img.shields.io/badge/daphne-303030?style=for-the-badge&logo=daphne&logoColor=white"> <img src="https://img.shields.io/badge/redis 7.0.7-FF1F1F?style=for-the-badge&logo=redis&logoColor=white"> <img src="https://img.shields.io/badge/jenkins -D24939?style=for-the-badge&logo=jenkins&logoColor=white"> <img src="https://img.shields.io/badge/amazon rds -527FFF?style=for-the-badge&logo=amazonrds&logoColor=white">

### Management

> <img src="https://img.shields.io/badge/github-181717?style=for-the-badge&logo=github&logoColor=white"> <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">

### Database

> <img src="https://img.shields.io/badge/mysql -4479A1?style=for-the-badge&logo=mysql&logoColor=white">

<br>

## [ERD](https://www.erdcloud.com/d/rcy9tc32bPmgHN6gn)

<br>

## Link

### [Front-end Repository](https://github.com/Songjimyung/EcoCanvas-Frontend)

### [배포 사이트](https://www.ecocanvas.net)
