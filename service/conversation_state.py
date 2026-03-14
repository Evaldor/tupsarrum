from typing import List, TypedDict

class Message(TypedDict):
    role: str
    content: str

class Word(TypedDict):
    order_no: int
    word: str
    word_type: str
    word_characteristics: str
    reasoning: str

class ConversationState(TypedDict):
    
    # Входные данные
    user: str  # логин пользователя из telegram
    incoming_message: str # Входящее сообщение

    # ЭТАП 0: Анализ обращения
    phrase_ru: str # Фраза на русском для перевода
    context: str # контекст фразы, для более точного смылового перевода
    genre: str # жанр фразы, лирика быт, молитвы, гимны итп

    # ЭТАП 1: Деталиализация жанра и контекста
    context_detailed: str # Расширенный контекст для анализа
    genre_detailed: str # Расширенный жанр для анализа

    # ЭТАП 2: АНАЛИЗ ИСХОДНОГО ТЕКСТА И КОНТЕКСТА
    step3_analysis_history: List[Message] # История сообщений при исследовании этапа 1
    phrase_structure_ru: List[Word] # структура фразы соответствующая нормам аккадского, на русском
    step3_reasoning: str # Развёрнутый ответ на вопрос этапа 1 "почему?"

    # Технический раздел
    final_answer: List[str] # ответ на вопрос
    current_node: str # текущий узел
