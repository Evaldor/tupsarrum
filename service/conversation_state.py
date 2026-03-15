from typing import List, TypedDict

class Message(TypedDict):
    role: str
    content: str

class WordAccadian(TypedDict):
    veight: int
    word_accadian: str
    word_accadian_meaning: str
    vacabulary_source: str
    reasoning_accadian: str

class Word(TypedDict):
    order_no: int
    word: str
    word_type: str
    word_characteristics: str
    word_reasoning: str
    relevant_accadian_words: List[WordAccadian]

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
    step2_analysis_history: List[Message] # История сообщений при исследовании этапа 1
    phrase_structure_ru: List[Word] # структура фразы соответствующая нормам аккадского, на русском
    step2_reasoning: str # Развёрнутый ответ на вопрос этапа 2 "почему?"

    # ЭТАП 3: ЛЕКСИЧЕСКИЙ ПОДБОР (СЛОВАРИ)
    step3_lexcon_history: List[Message] # История сообщений при исследовании этапа 1
    phrase_accadian_structure_ru: str

    # Технический раздел
    final_answer: List[str] # ответ на вопрос
    current_node: str # текущий узел
