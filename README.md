# tupsarrum

ИИ агент переводчик предложений с русского на аккадскую клинопись средневавилонского периода.
## Список сервисов

### service

сервис написанный с использованием langgraph читающий сообщения из бота телеграм от пользователей, проводящий аналитику этих запросов и отсылающий ответы обратно

для визуализации графа установите в vscode LangGraph Visualizer и примените в файле graph_utils.py


## Setup Instructions

```
docker-compose up --build
```

## Local Development Setup

1. docker-compose up --build
2. Остановить контейнер ai-tupsarrum
3. Заполнить параметры в .env в папке service
4. Создать и запустить виртуальное окружение
```
pip install virtualenv
virtualenv venv -p C:\Users\eva\AppData\Local\Programs\Python\Python313\python.exe
venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
```
1. запустить сервис
```
cd service
uvicorn main:app --host 0.0.0.0 --port 8000
```
1. отправить сообщение в бота

### Prerequisites
- Python 3.13 or higher
- pip (Python package installer)
- For AI_dep_secretary: Redis database
