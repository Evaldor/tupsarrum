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
                logger.info(f"==== {state['current_node']} for session {state['user']}")

                research_history = []
                pre_prompt = """
                    Ты аналитик службы поддержки пользователей со специализацией в лингвистике, литературе и поэзии. 
                    В сообщении пользователь написал фразу которую хочет перевести а так же указал жанр и контекст фразы для повышения качества перевода.
                    Твоя задача - выделить из сообщения фразу для перевода, описание контекста, описание жанра. по возможности не добавляя от себя ничего а только используя то что написал пользователь.
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
                #response = self.llm_general.invoke(research_history )
                #assistant_message = response.content

                assistant_message = self.LLMManager.call(research_history,1.3,"deepseek-chat",True)

                cleaned_text = re.sub(r'^```json\s*|\s*```$', '', assistant_message, flags=re.DOTALL)

                '''
                    из json возвращенного в качестве ответа извлекаем данные
                    пример:
                    '```json\n{\n    "phrase_ru": "я мечтаю о твоих восторженных глазах",\n    "context": "обращение мужчины к возлюбленной женщине",\n    "genre": "любовная лирика, личные письма"\n}\n```'
                    
                    '''
                try:
                    parsed_json = json.loads(cleaned_text)
                except json.JSONDecodeError as e:
                    logger.info(f"Error while parsing json: {assistant_message} for user {state['user']} Error text: {e}")

                return {
                    "phrase_ru": parsed_json.get("phrase_ru", ""),
                    "context": parsed_json.get("context", ""),
                    "genre": parsed_json.get("genre", "")
                }

        graph = StateGraph(ConversationState)

        graph.add_node("analyse_incoming_message", analyse_incoming_message)
    
        graph.set_entry_point("analyse_incoming_message")
        graph.add_edge("analyse_incoming_message", END)
    
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