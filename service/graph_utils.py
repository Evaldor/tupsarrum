import inspect
import json
import re
import logging_config  # Must be first
import logging
from typing import Literal
from langgraph.graph import StateGraph, END
from conversation_state import ConversationState
from llm_utils import LLMManager


logger = logging.getLogger(__name__)

class GraphManager:

    def __init__(self):
        self.LLMManager = LLMManager()

    def create_message_graph(self):

        def analyse_incoming_message(state: ConversationState):
            """
            ЭТАП 0: Анализ обращения
            выделяем из сообщения фразу для перевода и описание контекста и жанра
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"{state['current_node']} for session {state['user']}")

            research_history = []
            pre_prompt = """
                Ты аналитик службы поддержки пользователей со специализацией в лингвистике, литературе и поэзии. 
                В сообщении пользователь написал фразу которую хочет перевести а так же указал жанр и контекст фразы 
                для повышения качества перевода. 
                Твоя задача - выделить из сообщения фразу для перевода, описание контекста, описание жанра, 
                по возможности не добавляя от себя ничего а только используя то что написал пользователь.
                Отвечая используй русский язык.
                Верни ответ строго в формате json:
                {
                    "phrase_ru": "фраза на русском языке которую пользователю требуется перевести"б
                    "context": "описание контекста фразы для более точного перевода",
                    "genre": "жанр фразы, например, лирика, молитвы, гимны итп"
                }
                """
            # Добавляем системное сообщение
            research_history.append({"role": "system", "content": pre_prompt})
            # Добавляем сообщение пользователя в историю
            research_history.append({"role": "user", "content": state['incoming_message']})

            assistant_message = self.LLMManager.call(research_history,0.8,"deepseek-reasoner",True)

            try:
                parsed_json = json.loads(assistant_message)
            except json.JSONDecodeError as e:
                logger.error(f"Error while parsing json: {assistant_message} for user {state['user']} Error text: {e}")

            return {
                "phrase_ru": parsed_json.get("phrase_ru", ""),
                "context": parsed_json.get("context", ""),
                "genre": parsed_json.get("genre", "")
            }
        
        def research_context_and_genre(state: ConversationState):
            """
            ЭТАП 1: определяем детали контекста и жанра
            для лучшего перевода надо более подробно описать пользовательский запрос, который как правило упрощенный
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"{state['current_node']} for session {state['user']}")

            research_history = []
            pre_prompt = """
                Ты ассириолог который в совершенстве знает аккадский и ассиро-вавилонскую клинопись конца средневавилонского периода, 
                на рубеже катастрофы бронзового века. Ты знаешь множество текстов того периода, перевеенных с клинописных табличек, разбираешься
                в жанрах, литературе и особенностях письменного творечства того периода на ближнем востоке.
                Кроме того ты разбираешься в литературе и истории литературы в целом.
                Твоя задача:
                в полученном сообщении json:
                {
                    "phrase_ru": "фраза на русском языке которую пользователю требуется перевести"б
                    "context": "описание контекста фразы для более точного перевода",
                    "genre": "жанр фразы, например, лирика, молитвы, гимны итп"
                }
                1. ты должен проанилизировать "context"(контекст) и дать его расширенное описание. Опиши участников обстоятельства и смысловые тонкости их взаимодействия.
                анализируй контекст с учетом "genre"(жанра) и самой фразой для перевода. Давай расширенное описание контекста так, как буд-то ты пытаешься помочь переводчику
                правильно определить нюансы и тонкости фразы и подобрать верный перевод.
                2. ты должен проанилизировать "genre"(жанр) и дать его расширенное описание. Опиши жанр фразы, а так же какому жанру из существовавших в ассиро-вавилонской 
                клинописи конца средневавилонского периода современный жанр лучше соотвествует,анализируй жанр с учетом "context"(контекста) и самой фразой для перевода. 
                Давай расширенное описание жанра так, как буд-то ты пытаешься помочь переводчику

                Отвечая используй русский язык.

                Верни ответ строго в формате json:
                {
                    "context_detailed": "детализированное и адаптированное описание контекста фразы для более точного перевода, не более чем один или два абзаца текста",
                    "genre_detailed": "детализированное и адаптированное описание жанра фразы, например, лирика, молитвы, гимны итп, не более чем один или два абзаца текста"
                }
               """
            # Добавляем системное сообщение
            research_history.append({"role": "system", "content": pre_prompt})

            # Добавляем сообщение пользователя в историю
            data = {
                "phrase_ru": state["phrase_ru"],
                "context": state["context"],
                "genre": state["genre"]
            }
            request_json = json.dumps(data, ensure_ascii=False, indent=2)

            research_history.append({"role": "user", "content": request_json})

            assistant_message = self.LLMManager.call(research_history,1.5,"deepseek-reasoner",True)

            try:
                parsed_json = json.loads(assistant_message)
            except json.JSONDecodeError as e:
                logger.error(f"Error while parsing json: {assistant_message} for user {state['user']} Error text: {e}")

            return {
                "context_detailed": parsed_json.get("context_detailed", ""),
                "genre_detailed": parsed_json.get("genre_detailed", "")
            }
        
        def build_phrase_structure(state: ConversationState):
            """
            ЭТАП 2: Построение структуры фразы
            построение структуры фразы, порядка слов и прочее, для подготовки к подбору слов и дальнейшему переводу
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"{state['current_node']} for session {state['user']}")

            research_history = []
            pre_prompt = """
                Ты ассириолог который в совершенстве знает аккадский и ассиро-вавилонскую клинопись конца средневавилонского периода, 
                на рубеже катастрофы бронзового века. 
                Ты занимаешься переводом с русского языка на аккадский средне-вавилонского периода.
                Ты строишь фразы и проверяешь то что сделал по учебнику Huehnergard John 2011 - A Grammar of Akkadian 3rd edition. 

                Твоя задача:
                в полученном сообщении json:
                {
                    "phrase_ru": "фраза на русском языке которую пользователю требуется перевести",
                    "context_detailed": "описание контекста фразы для более точного перевода",
                    "genre_detailed": "жанр фразы, например, лирика, молитвы, гимны итп"
                }

                возьми из него фразу на русском языке "phrase_ru" и построй фразу на аккадском языке, 
                таким образом чтобы слова были русские, но их порядок и структура соответствовали аккадским языковым нормам и синтаксису,
                делая то проверяй себя по учебнику Huehnergard John 2011 - A Grammar of Akkadian 3rd edition.
                Это очень важно, построй грамматическую конструкцию итоговой фразы строго по языковым нормам 
                ассиро-вавилонского диалекта аккадского языка средневавилонского периода.
                Сверь спорные моменты по KEY TO A GRAMMAR OF AKKADIAN (Huehnergard, 2013), чтобы убедиться в правильности выполнения упражнений (если применимо).

                Вот основные правила построения предложений в аккадском языке (на основе грамматических стандартов ORACC, соответствующих средневавилонскому периоду):

                    1. Базовый порядок слов (SOV): Глагол всегда стоит в конце предложения. Правильная последовательность: Подлежащее → Дополнение → Глагол. (Пример: Собака человека укусила).

                    2. Позиция прилагательного: Прилагательное ставится после существительного, которое оно описывает, и полностью согласуется с ним в роде, числе и падеже.

                    3. Позиция определения (генитив): Определение (родительный падеж) всегда стоит после определяемого слова. Используется либо status constructus, либо предлог ša.

                    4. Позиция наречий и частиц: Наречия и отрицания (ul, lā) ставятся непосредственно перед словом, к которому относятся (чаще всего перед глаголом).

                    5. Именное предложение: Предложение может быть построено без глагола. В таком случае подлежащее и именное сказуемое (оба в именительном падеже) просто стоят рядом (как в русском "он — царь").

                    6. Придаточные определительные: Вводятся местоимением ša. Глагол внутри такого придаточного предложения обязательно стоит в форме субъюнктива.

                    7. Условные предложения: Начинаются с šumma ("если"). В условии глагол отрицается частицей lā, а в главном следствии — частицей ul.

                    8. Связь частей предложения: Для соединения предложений (в значении "и (затем)") к первому глаголу присоединяется суффикс -ma.

                Строя фразу на аккадском языке, делай это так, чтобы она соответствовала контексту "context_detailed"

                Строя фразу на аккадском языке, делай это так, чтобы она соответствовала жанру "genre_detailed"

                в качестве ответа верни грамматическую конструкцию итоговой фразы разбитую на составные части.

                Отвечая используй русский язык.

                Порядок слов в "phrase_structure_ru", структура фразы и прочее должны соответствовать аккадским языковым нормам и синтаксису, 
                как это описано в Huehnergard John 2011 - A Grammar of Akkadian 3rd edition

                Этап самопроверки, построив фразу проверь в ней:
                    ○ Порядок слов (обычно SOV).
                    ○ Падежи существительных (именительный, родительный, винительный).
                    ○ Времена и наклонения глаголов (претерит, перфект, презенс, статив, ветив/прогибитив и т.д.).
                    ○ Суффиксы (притяжательные, объектные).
                    ○ Для каждой грамматической формы, которую ты используешь, обратись к учебнику Huehnergard John. 2011. A Grammar of Akkadian (3rd edition). Найди соответствующий параграф и убедись, что форма построена верно. Особое внимание удели парадигмам спряжения и склонения.
                    ○ Сверь спорные моменты по KEY TO A GRAMMAR OF AKKADIAN (Huehnergard, 2013), чтобы убедиться в правильности выполнения упражнений (если применимо).

                Верни ответ строго в формате json, где каждый элемент - то часть фразы:
                {
                    
                    "phrase_structure_ru":[
                        {
                            "order_no": "порядковый номер слова в фразе",
                            "word": "часть грамматической конструкции, слово или предлог",
                            "word_type": "тип слова, например, существительное, прилагательное, глагол, предлог, союз итп",
                            "word_characteristics": "характеристики слова, например, род, число, наклонение, падеж, любая особенность этой части грамматической конструкции которая может быть полезна для перевода на аккадский",
                            "word_reasoning": "объяснение почему ты предлагаешь именно такой вариант для этого элемента"
                        }
                    ],
                    "phrase_reasonong": "объяснение почему ты предлагаешь именно такую структуру в целом с точки зрения праил аккадского языка"
                }
                """
            # Добавляем системное сообщение
            research_history.append({"role": "system", "content": pre_prompt})

            # Добавляем сообщение пользователя в историю
            data = {
                "phrase_ru": state["phrase_ru"],
                "context_detailed": state["context_detailed"],
                "genre_detailed": state["genre_detailed"]
            }
            request_json = json.dumps(data, ensure_ascii=False, indent=2)

            research_history.append({"role": "user", "content": request_json})

            assistant_message = self.LLMManager.call(research_history,1.3,"deepseek-reasoner",True)

            try:
                parsed_json = json.loads(assistant_message)
            except json.JSONDecodeError as e:
                logger.error(f"Error while parsing json: {assistant_message} for user {state['user']} Error text: {e}")

            return {
                "step2_analysis_history": research_history,
                "phrase_structure_ru": parsed_json.get("phrase_structure_ru", []),
                "step2_reasoning": parsed_json.get("phrase_reasonong", "")
            }

        def work_with_vacabulares(state: ConversationState):
            """
            ЭТАП 3: ЛЕКСИЧЕСКИЙ ПОДБОР (СЛОВАРИ)
            подбираем подходящие слова по словарям
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"{state['current_node']} for session {state['user']}")

            pre_prompt = """Ты ассириолог который в совершенстве знает аккадский и ассиро-вавилонскую клинопись конца средневавилонского периода, 
                на рубеже катастрофы бронзового века. Ты занимаешься переводом с русского языка на аккадский средне-вавилонского периода.

                Твоя задача:
                для полученного сообщениия в формате json:
                {
                    "phrase_accadian_structure_ru": "фраза на русском языке построенная по правилам аккадского языка",
                    "context_detailed": "описание контекста фразы для более точного перевода",
                    "genre_detailed": "жанр фразы, например, лирика, молитвы, гимны итп",
                    "word": "слово для которого надо подобрать варианты перевода"
                    "word_type": "тип слова, например, существительное, прилагательное, глагол, предлог, союз итп"
                    "word_characteristics": "характеристики слова, например, род, число, наклонение, падеж, любая особенность этой части грамматической конструкции которая может быть полезна для перевода на аккадский"
                    "word_reasoning: "объяснение почему ты предлагаешь именно такой вариант для этого элемента"
                }

                Выполнить действия:
                Для каждого слова из фразы для перевода подбери не более чем 3 (очень важно подобрать не более чем 3 варианта) наиболее подходящих значений по словарям, 
                с обоснованием какой из них больше подходит в связи с контекстом("context_detailed") и жанром("genre_detailed")

                В первую очередь используй Black, Jeremy; George, Andrew; Postgate, Nicholas. A Concise Dictionary of Akkadian (CDA). Он даст основное значение и отсылки.

                Для углубленной проверки значений, контекстов употребления и особенно для подтверждения, что слово существовало именно в средневавилонский период, 
                обратись к Chicago Assyrian Dictionary (CAD). Найди соответствующую статью и убедись, что среди цитат есть примеры из средневавилонских текстов.

                Ищи подходящие слова по всем томам CAD (очень важно брать не только первый попавшийся вариант, но искать по всем частям CAD)
                , для того чтобы подобрать наиболее подходящий под контекст("context_detailed") и жанр("genre_detailed") вариант

                Фиксация: Для каждого аккадского слова в транслитерации укажи, из какого словаря и на какую статью ты опираешься.

                Отвечая используй русский язык.

                Верни ответ строго в формате json, где каждый элемент - то часть фразы:
                {
                    "relevant_accadian_words":[
                        {
                            "word_accadian": "аккадское слово ассировавилонского диалекта, средневавилонского периода, записанное транслитерацией, слоговой записью",
                            "word_accadian_meaning": "описание значения слова по аккадскому словарю",
                            "veight": "Значение от 0 до 100, обозначающее на сколько относительно других вариантов это слово подходит в качестве перевода, чем больше тем лучше подходит",
                            "vacabulary_source": "Ссылка на словарь, с указанием раздела, откуда взято аккадское слово"
                            "reasoning_accadian": "объяснение почему ты выбрал этот вариант"
                        }
                    ]
                }
                """

            phrase_accadian_structure_ru = ""
            phrase_structure_ru = state['phrase_structure_ru']
            
            for word in phrase_structure_ru:
                phrase_accadian_structure_ru = phrase_accadian_structure_ru +" "+word["word"]

            # Выполняем подбор для каждого слова из фразы
            for word in phrase_structure_ru:
                research_history = []
                # Добавляем системное сообщение
                research_history.append({"role": "system", "content": pre_prompt})

                data = {
                    "phrase_accadian_structure_ru": phrase_accadian_structure_ru,
                    "context_detailed": state["context_detailed"],
                    "genre_detailed": state["genre_detailed"],
                    "word": word['word'],
                    "word_type": word['word_type'],
                    "word_characteristics": word['word_characteristics'],
                    "word_reasoning": word['word_reasoning']
                }
                request_json = json.dumps(data, ensure_ascii=False, indent=2)

                research_history.append({"role": "user", "content": request_json})

                assistant_message = self.LLMManager.call(research_history,1.3,"deepseek-reasoner",True)

                try:
                    parsed_json = json.loads(assistant_message)
                except json.JSONDecodeError as e:
                    logger.error(f"Error while parsing json: {assistant_message} for user {state['user']} Error text: {e}")

                word["relevant_accadian_words"] = parsed_json.get("relevant_accadian_words", [])

            return {
                "phrase_structure_ru": phrase_structure_ru,
                "phrase_accadian_structure_ru": phrase_accadian_structure_ru
            }

        def prepare_result(state: ConversationState):
            """
            ФИНАЛ: Подготовка результата
            собираем всю цепочку в ответ
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"{state['current_node']} for session {state['user']}")

            answer_queue = []
            answer_queue.append(f"Фраза для перевода: {state['phrase_ru']}")
            answer_queue.append(f"Если углубиться в контекст, то: {state['context_detailed']}")
            answer_queue.append(f"Если углубиться в жанр, то: {state['genre_detailed']}")
            answer_queue.append(f"Адаптированная для перевода структура фразы: {state['phrase_structure_ru']}")
            answer_queue.append(f"сделал так потому что: {state['step2_reasoning']}")
            answer_queue.append(f"я подобрал следующий слова для перевода каждого элемента")
            for word in state['phrase_structure_ru']:
                answer_queue.append(f"Слово № {word['order_no']} {word['word']}")
                answer_queue.append(f"Варианты перевода: {word['relevant_accadian_words']}")
            answer_queue.append(f"Перевод готов!")
            return {
                "final_answer": answer_queue
            }

        graph = StateGraph(ConversationState)

        graph.add_node("analyse_incoming_message", analyse_incoming_message)
        graph.add_node("research_context_and_genre", research_context_and_genre)
        graph.add_node("build_phrase_structure", build_phrase_structure)
        graph.add_node("work_with_vacabulares", work_with_vacabulares)
        
        graph.add_node("prepare_result", prepare_result)

        graph.set_entry_point("analyse_incoming_message")
        graph.add_edge("analyse_incoming_message", "research_context_and_genre")
        graph.add_edge("research_context_and_genre", "build_phrase_structure")
        graph.add_edge("build_phrase_structure", "work_with_vacabulares")
        graph.add_edge("work_with_vacabulares", "prepare_result")
        graph.add_edge("prepare_result", END)
    
        return graph.compile()

    '''
    def create_message_graph(self):
        """Create a langgraph graph for processing messages."""
        def get_state(state: ConversationState):
            logger.info(f"get_state for session {state['user']}")
            return state
        
        def jump_to_state_node(state: ConversationState) -> Literal['get_user_context', 'get_domain_context','domain_research_summarize','domain_context_ask_user','get_analytics_research','analytics_research_summarize','analytics_research_ask_user']:
            """
            Если ранее существовал созданный state переходим на ноду где остановился пользователь
            """
            if "current_node" not in state:
                state['current_node'] = "get_user_context" # создаем стейт с следующей нодой чтобы в следующий раз был переход на неё

            logger.info(f"==== jump_to_state_node {state['current_node']}  for session {state['user']}")
            return state['current_node'] 

        def get_user_context(state: ConversationState):
            """
            Имитирует получение информации о пользователе из внешних систем.
            В будущем — вызов API HR или профильного сервиса.
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            self.redis_manager.save_state(state['user'], state)
            return {
                    "position": "Ведущий аналитик",
                    "department": "Команда маркетинга и b2c"
                }
        
        def get_domain_context(state: ConversationState):
            """
            итерация исследования доменов и контекста обращения
            При первой итерации добавляет системный промт для LLM.
            Необходимо будет сделать рефакторинг, т.к. в реальном сценарии общение с пользователем 
            происходит не в диалоговом окне а путем отправки сообщений по каналу коммуникации
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            self.redis_manager.save_state(state['user'], state)
            research_history = []
            if 'domain_research_history' in state:
                research_history = state['domain_research_history']
            
            if len(research_history) == 0:
                pre_prompt = """
                    Ты системный аналитик в финтехе, определи запрос пользователя достаточен 
                    для того чтобы понять в какой предметной области находится то что требуется сделать чтобы 
                    удовлетворить его запрос?
                    Если информации достаточно - верни утвердительный ответ и запиши определение предметной области
                    Если информации не достаточно или нет уверенности в конкретном запросе сформулируй уточняющий 
                    вопрос с объяснением почему ты его задаешь.
                    """
                # Добавляем системное сообщение
                research_history.append({"role": "system", "content": pre_prompt})

            # Добавляем сообщение пользователя в историю
            research_history.append({"role": "user", "content": state['incoming_message']})

            # Отправляем запрос с полной историей
            """
            так же тут будет необходимо предусмотреть шаги которые заполнят списки:
                relevant_domains: List[str]  # Выявленные релевантные бизнес-домены (например, ["финансы", "маркетинг"])
                relevant_sub_domains: List[str]  # Выявленные релевантные поддомены (например, ["касса", "шопы"])
                relevant_services: List[str]  # Релевантные сервисы системы (например, ["SERV-1230", "SERV-1002"])
                relevant_components: List[str]  # Релевантные компоненты системы (например, ["COM-740", "COM-442"])
                relevant_repos: List[str]  # Релевантные репозитории системы (например, ["bi/datalake", "bi/nastro])
                relevant_bussines_terms: List[str]  # Важные бизнес-термины из запроса
                relevant_persons: List[str]  # Список ответственных лиц
            """
            response = self.llm_general.invoke(research_history)
            assistant_message = response.content
            # Добавляем ответ ассистента в историю
            research_history.append({"role": "assistant", "content": assistant_message})

            checking_prompt = """
                    Определи достаточно ли информации о бизнес доменах и контексте 
                    и верни в качестве ответа один символ:
                    0 - если не достаточно
                    1 - если достаточно
                    """
            
            checking_thread = []
            checking_thread.append({"role": "system", "content": checking_prompt})
            checking_thread.append({"role": "user", "content": assistant_message})
            response = self.llm_general.invoke(checking_thread)
            if response.content == '1\n':
                research_is_enough = True
            else:
                research_is_enough = False

            iteration = 0
            if "domain_research_iteration" in state:
                iteration = state['domain_research_iteration']+1
            else:
                iteration = 1
            return {
                "domain_research_history": research_history,
                "domain_research_iteration": iteration,
                "current_reply": assistant_message,
                "domain_research_is_enough": research_is_enough
            }
        
        def domain_research_is_enough(state: ConversationState) -> Literal['is_enough', 'is_not_enough']:
            """
            Условный переход: мы уже достаточно разобрались в контексте или нет. можем ли перейти уже к аналитике
            Защита от бесконечного цикла, по счетчику итераций.
            """
            current = inspect.currentframe().f_code.co_name
            logger.info(f"==== {current} for session {state['user']}")

            if state['domain_research_is_enough']:
                return "is_enough"
            elif state['domain_research_iteration'] >= state['domain_research_max_iterations']:
                return "is_enough"
            else:
                return "is_not_enough"

        def domain_research_summarize(state: ConversationState):
            """
            Генерация финального отчёта по доменному анализу.
            Обобщает весь диалог для передачи на следующий этап.
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            self.redis_manager.save_state(state['user'], state)

            prompt = """
                    обобщи весь диалог и напиши его краткое резюме так чтобы  в первой части были коротко сформулированы все запросы пользователя 
                    а во второй осталась в основном информация о принадлежности темы вопросов к доменным областям
                    """
            history = state['domain_research_history']
            history.append({"role": "user", "content": prompt})
            response = self.llm_general.invoke(history)
            assistant_message = response.content

            return {
                "current_node":"domain_research_summarize",
                "domain_research_final_report": assistant_message,
                "current_reply": assistant_message,
            }
        
        def domain_context_ask_user(state: ConversationState):
            """
            Задать вопрос пользователю с уточнением
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            state['current_node'] = "get_domain_context"
            self.redis_manager.save_state(state['user'], state)
            return state
        
        def get_analytics_research(state: ConversationState):
            """
            Анализ кодовой базы: какие компоненты, репозитории, действия нужны?
            На первой итерации использует итог доменного анализа, для сужения списка поиска. 
            скорее всего шаги по анализу репозиториев надо будет вынести в отдельные итераторы.
            Далее — диалог с пользователем через уточняющие вопросы.
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            self.redis_manager.save_state(state['user'], state)
            research_history = []
            if 'analytics_research_history' in state:
                research_history = state['analytics_research_history']

            if len(research_history) == 0:
                pre_prompt = """
                    Ты инженер данных в финтехе, посоветуй в каких компонентах стемы надо сделать операции и какие, 
                    для того чтобы дать пользователю то что он хочет?
                    Если информации достаточно - верни утвердительный ответ и запиши перечень репозиториев артефактов и действий которые
                    необходимо предпринять чтобы решить запрос пользователя.
                    Если информации не достаточно или нет уверенности в конкретном запросе сформулируй уточняюащий 
                    вопрос с объяснением почему ты его задаешь.
                    """
                research_history.append({"role": "system", "content": pre_prompt})
                research_history.append({"role": "user", "content": state['domain_research_final_report']})
            else:
                research_history.append({"role": "user", "content": state['incoming_message']})

            """
            TODO проходим по документациям и репозиториями и формируем общий ответ
            """
            """
            TODO реализуем поиск ответственного лица analytics_research_responsible_person: str #контакт ответственного за вопрос
            """

            # Отправляем запрос с полной историей
            response = self.llm_coder.invoke(research_history)
            assistant_message = response.content

            # Добавляем ответ ассистента в историю
            research_history.append({"role": "assistant", "content": assistant_message})

            checking_prompt = """
                    Определи достаточно ли информации чтобы ответить пользователю на его вопросы 
                    и верни в качестве ответа один символ:
                    0 - если не достаточно
                    1 - если достаточно
                    """
            
            checking_thread = []
            checking_thread.append({"role": "system", "content": checking_prompt})
            checking_thread.append({"role": "user", "content": assistant_message})
            response = self.llm_general.invoke(checking_thread)
            if response.content == '1\n':
                research_is_enough = True
            else:
                research_is_enough = False

            iteration = 0
            if "analytics_research_iteration" in state:
                iteration = state['analytics_research_iteration']+1
            else:
                iteration = 1

            return {
                "analytics_research_history": research_history,
                "analytics_research_iteration": iteration,
                "current_reply": assistant_message,
                "analytics_research_is_enough": research_is_enough
            }

        def analytics_research_is_enough(state: ConversationState) -> Literal['is_enough', 'is_not_enough']:
            """
            Условный переход: мы уже ответили на вопрос пользователя и можем вернуть ответ?
            Защита от бесконечного цикла, по счетчику итераций.
            """
            current = inspect.currentframe().f_code.co_name
            logger.info(f"==== {current} for session {state['user']}")

            if state['analytics_research_is_enough']:
                return "is_enough"
            elif state['analytics_research_iteration'] >= state['analytics_research_max_iterations']:
                return "is_enough"
            else:
                return "is_not_enough"

        def analytics_research_summarize(state: ConversationState):
            """
            Генерация финального отчёта по аналитике задачи.
            Обобщает весь диалог для передачи на следующий этап.
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            self.redis_manager.save_state(state['user'], state)

            prompt = """
                    обобщи весь диалог и напиши развернутый ответ на запрос пользователя, какие действия в кодовой базе(аналитика, разработка) нужно предпринять чтобы дать ответ
                    объясни те действия которые ты предлагаешь.
                    """
            history = state['analytics_research_history']
            history.append({"role": "user", "content": prompt})
            response = self.llm_general.invoke(history)
            assistant_message = response.content

            return {
                "current_node":"analytics_research_summarize",
                "analytics_research_final_report": assistant_message,
                "current_reply": assistant_message,
            }
        
        def analytics_research_ask_user(state: ConversationState):
            """
            Задать вопрос пользователю с уточнением для исследования
            """
            state['current_node'] = inspect.currentframe().f_code.co_name
            logger.info(f"==== {state['current_node']} for session {state['user']}")
            state['current_node'] = "get_analytics_research"
            self.redis_manager.save_state(state['user'], state)
            return state

        graph = StateGraph(ConversationState)

        graph.add_node("get_state", get_state)
        graph.add_node("jump_to_state_node", jump_to_state_node)
        graph.add_node("get_user_context", get_user_context)
        graph.add_node("get_domain_context", get_domain_context)
        graph.add_node("domain_research_summarize",domain_research_summarize)
        graph.add_node("domain_context_ask_user",domain_context_ask_user)
        graph.add_node("get_analytics_research", get_analytics_research)
        graph.add_node("analytics_research_summarize", analytics_research_summarize)
        graph.add_node("analytics_research_ask_user",analytics_research_ask_user)

        graph.set_entry_point("get_state")
        graph.add_conditional_edges(
            "get_state",
            jump_to_state_node,
            {
                "get_user_context": "get_user_context",
                "get_domain_context": "get_domain_context",
                "domain_research_summarize": "domain_research_summarize",
                "domain_context_ask_user": "domain_context_ask_user",
                "get_analytics_research": "get_analytics_research",
                "analytics_research_summarize": "analytics_research_summarize",
                "analytics_research_ask_user": "analytics_research_ask_user"
            }
        )
        graph.add_edge("get_user_context","get_domain_context")
        graph.add_conditional_edges(
            "get_domain_context",
            domain_research_is_enough,
            {
                "is_enough": "domain_research_summarize",
                "is_not_enough": "domain_context_ask_user"
            }
        )
        graph.add_edge("domain_research_summarize", "get_analytics_research")
        graph.add_conditional_edges(
            "get_analytics_research",
            analytics_research_is_enough,
            {
                "is_enough": "analytics_research_summarize",
                "is_not_enough": "analytics_research_ask_user"
            }
        )
        graph.add_edge("analytics_research_summarize", "analytics_research_ask_user")
        
        graph.add_edge("domain_context_ask_user", END)
        graph.add_edge("analytics_research_ask_user", END)
        '''