from typing import List, TypedDict

class Message(TypedDict):
    role: str
    content: str

class Word(TypedDict):
    word: str
    function: str

class ConversationState(TypedDict):
    
    # Входные данные
    user: str  # логин пользователя из telegram
    incoming_message: str # Входящее сообщение

    # ЭТАП 0: Анализ обращения
    phrase_ru: str # Фраза на русском для перевода
    context: str # контекст фразы, для более точного смылового перевода
    genre: str # жанр фразы, лирика быт, молитвы, гимны итп
  
    # ЭТАП 1: АНАЛИЗ ИСХОДНОГО ТЕКСТА И КОНТЕКСТА
    step1_analysis_history: List[Message] # История сообщений при исследовании этап 1
    context_detailed: str # Расширенный контекст для анализа
    genre_detailed: str # Расширенный жанр для анализа
    phrase_ru_prepared: list[Word]
    step1_reasoning: str # Развёрнутый ответ на вопрос этапа 1 "почему?"
    step1_answer: str # Ответ на вопрос этапа 1


    current_node: str # текущий узел
