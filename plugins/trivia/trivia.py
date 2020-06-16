import html
import random
from typing import Dict, Any, Union, List
from typing import List

import time

import utils
from bot.base import InlineKeyboardMarkup, InlineKeyboardButton
from bot.base import MessageHandlerBase, BotBase
from data import Message, ChatState, CallbackQuery, Chat
from textformatting import TextFormatter, MessageStyle

CATEGORIES: Dict[str, str] = {
    'any': 'Any',
    '9': 'General Knowledge',
    '10': 'Entertainment: Books',
    '11': 'Entertainment: Film',
    '12': 'Entertainment: Music',
    '13': 'Entertainment: Musicals & Theatres',
    '14': 'Entertainment: Television',
    '15': 'Entertainment: Video Games',
    '16': 'Entertainment: Board Games',
    '17': 'Science & Nature',
    '18': 'Science: Computers',
    '19': 'Science: Mathematics',
    '20': 'Mythology',
    '21': 'Sports',
    '22': 'Geography',
    '23': 'History',
    '24': 'Politics',
    '25': 'Art',
    '26': 'Celebrities',
    '27': 'Animals',
    '28': 'Vehicles',
    '29': 'Entertainment: Comics',
    '30': 'Science: Gadgets',
    '31': 'Entertainment: Japanese Anime & Manga',
    '32': 'Entertainment: Cartoon & Animations'}


class TriviaQuestion(object):
    def __init__(self):
        self.category: str = ''
        self.type: str = ''
        self.difficulty: str = ''
        self.question: str = ''
        self.correct_answer: str = ''
        self.incorrect_answers: List[str] = []

    @staticmethod
    def from_json(json_object: Dict) -> 'TriviaQuestion':
        res: TriviaQuestion = TriviaQuestion()
        res.category = json_object['category']
        res.type = json_object['type']
        res.difficulty = json_object['difficulty']
        res.question = html.unescape(json_object['question'])
        res.correct_answer = json_object['correct_answer']
        res.incorrect_answers = json_object['incorrect_answers']
        return res


class AnswerArrangement(object):
    def __init__(self):
        self.answers: List[str] = []
        self.correct_answer_index: int = 0

    @staticmethod
    def generate_random_from_question(question: TriviaQuestion):
        res: AnswerArrangement = AnswerArrangement()
        r: List[str] = [a for a in question.incorrect_answers]
        random.shuffle(r)
        i: int = random.randint(0, len(r))
        r.insert(i, question.correct_answer)
        res.answers = r
        res.correct_answer_index = i
        return res


class TriviaMessageHandler(MessageHandlerBase):
    @staticmethod
    def get_help() -> TextFormatter:
        res: TextFormatter = TextFormatter()
        res.italic('\U00002328 Trivia').new_line().normal('Get a random trivia question.').new_line().new_line()
        res.italic('\U00002328 Trivia category').new_line().italic('\U00002328 Trivia c').new_line().normal(
            'Choose category for the question.')
        return res

    def process_message(self, message: Message, bot: BotBase, chat_state: ChatState = None) -> None:
        if chat_state is not None:
            self.process_answer(message, bot, chat_state)
        else:
            self.process_new_question(message, bot)

    def process_callback_query(self, callback_query: CallbackQuery, bot: BotBase, chat_state: ChatState = None) -> None:
        if chat_state is None:
            pass
        else:
            if chat_state.data['action'] == 'question':
                try:
                    given_answer_idx: int = int(callback_query.data) - 1
                    answers: AnswerArrangement = chat_state.data['answers']
                    if given_answer_idx == answers.correct_answer_index:
                        bot.send_message(callback_query.message.chat, 'Correct!!', MessageStyle.NONE)
                    else:
                        bot.send_message(callback_query.message.chat,
                                         'WRONG. The answer was:\n{k}. {a}'.format(k=answers.correct_answer_index + 1,
                                                                                   a=answers.answers[
                                                                                       answers.correct_answer_index]),
                                         MessageStyle.NONE)
                    bot.answer_callback_query(callback_query.id_callback_query)
                    callback_query.message.chat.remove_chat_state()
                except Exception as ex:
                    raise RuntimeError(f'Could not process answer: {str(ex)}')
            elif chat_state.data['action'] == 'choose_category':
                id_category: str = callback_query.data
                self.send_question(callback_query.message.chat, bot, id_category)

    def process_new_question(self, message: Message, bot: BotBase):
        words: List[str] = message.text.split(' ')
        if words[0].lower() == 'trivia':
            if len(words) == 1:
                # json_obj = utils.get_url_json('https://opentdb.com/api.php', {'amount': '1'})
                json_obj = utils.get_url_json('https://opentdb.com/api.php?amount=1')
                question: TriviaQuestion = TriviaQuestion.from_json(json_obj['results'][0])
                answers: AnswerArrangement = AnswerArrangement.generate_random_from_question(question)
                keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup.from_str_list(
                    [str(k + 1) for k in range(len(answers.answers))])
                bot.send_message_with_inline_keyboard(message.chat,
                                                      self.get_question_str(question, answers),
                                                      MessageStyle.NONE,
                                                      keyboard)

                state: ChatState = ChatState()
                state.current_handler_name = self.handler_name
                state.chat_id = message.chat.id_chat
                state.last_time = time.time()
                state.data['action'] = 'question'
                state.data['question'] = question
                state.data['answers'] = answers
                message.chat.save_chat_state(state)
            elif len(words) == 2:
                if words[1].lower() in ('category', 'c'):
                    keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup()
                    for category_key in sorted(CATEGORIES):
                        button = InlineKeyboardButton()
                        button.text = CATEGORIES[category_key]
                        button.callback_data = category_key
                        keyboard.inline_keyboard.append([button])
                    msg: str = 'Select category:'
                    bot.send_message_with_inline_keyboard(message.chat, msg, MessageStyle.NONE, keyboard)

                    state: ChatState = ChatState()
                    state.current_handler_name = self.handler_name
                    state.chat_id = message.chat.id_chat
                    state.last_time = time.time()
                    state.data['action'] = 'choose_category'
                    message.chat.save_chat_state(state)

    def send_question(self, chat: Chat, bot: BotBase, id_category: str = None):
        if id_category is None:
            json_obj = utils.get_url_json('https://opentdb.com/api.php?amount=1')
        else:
            json_obj = utils.get_url_json(f'https://opentdb.com/api.php?amount=1&category={id_category}')
        question: TriviaQuestion = TriviaQuestion.from_json(json_obj['results'][0])
        answers: AnswerArrangement = AnswerArrangement.generate_random_from_question(question)
        keyboard: InlineKeyboardMarkup = InlineKeyboardMarkup.from_str_list(
            [str(k + 1) for k in range(len(answers.answers))])
        bot.send_message_with_inline_keyboard(chat,
                                              self.get_question_str(question, answers),
                                              MessageStyle.NONE,
                                              keyboard)

        state = ChatState()
        state.current_handler_name = self.handler_name
        state.chat_id = chat.id_chat
        state.last_time = time.time()
        state.data['action'] = 'question'
        state.data['question'] = question
        state.data['answers'] = answers
        chat.save_chat_state(state)

    def process_answer(self, message: Message, bot: BotBase, chat_state: ChatState) -> None:
        try:
            given_answer_idx: int = int(message.text) - 1
            answers: AnswerArrangement = chat_state.data['answers']
            if given_answer_idx == answers.correct_answer_index:
                bot.send_message(message.chat, 'Correct!!', MessageStyle.NONE)
            else:
                bot.send_message(message.chat,
                                 'WRONG. The answer was:\n{k}. {a}'.format(k=answers.correct_answer_index + 1,
                                                                           a=answers.answers[
                                                                               answers.correct_answer_index]),
                                 MessageStyle.NONE)
            message.chat.remove_chat_state()
        except Exception as ex:
            raise RuntimeError(f'Could not process answer: {str(ex)}')

    def get_question_str(self, question: TriviaQuestion, answers: AnswerArrangement) -> str:
        i: int
        q: str
        answer_str: str = '\n'.join([f'{i + 1}. {q}' for i, q in enumerate(answers.answers)])
        return f'{question.question}\n\n{answer_str}'
