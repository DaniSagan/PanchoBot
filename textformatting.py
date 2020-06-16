from enum import Enum
from typing import List


class MessageStyle(Enum):
    NONE = 0
    MARKDOWN = 1
    HTML = 2


class TextBase(object):

    def __init__(self, text: str):
        self.text: str = text

    def format(self, style: MessageStyle):
        raise NotImplementedError()


class NormalText(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle):
        return self.text


class BoldText(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle) -> str:
        if style == MessageStyle.MARKDOWN:
            return f'*{self.text}*'
        elif style == MessageStyle.HTML:
            return f'<b>{self.text}</b>'
        else:
            return self.text


class ItalicText(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle) -> str:
        if style == MessageStyle.MARKDOWN:
            return f'_{self.text}_'
        elif style == MessageStyle.HTML:
            return f'<i>{self.text}</i>'
        else:
            return self.text


class InlineCode(TextBase):
    def __init__(self, text: str):
        super().__init__(text)

    def format(self, style: MessageStyle) -> str:
        if style == MessageStyle.MARKDOWN:
            return f'`{self.text}`'
        elif style == MessageStyle.HTML:
            return f'<code>{self.text}</code>'
        else:
            return self.text


class TextFormatter(object):
    def __init__(self):
        self.items: List[TextBase] = []

    @staticmethod
    def instance() -> 'TextFormatter':
        return TextFormatter()

    def normal(self, text) -> 'TextFormatter':
        self.items.append(NormalText(text))
        return self

    def new_line(self) -> 'TextFormatter':
        self.items.append(NormalText('\n'))
        return self

    def bold(self, text) -> 'TextFormatter':
        self.items.append(BoldText(text))
        return self

    def italic(self, text) -> 'TextFormatter':
        self.items.append(ItalicText(text))
        return self

    def inline_code(self, text) -> 'TextFormatter':
        self.items.append(InlineCode(text))
        return self

    def append(self, other: 'TextFormatter') -> 'TextFormatter':
        self.items.extend(other.items)
        return self

    def format(self, style: MessageStyle) -> str:
        res: str = ''
        item: TextBase
        for item in self.items:
            res += item.format(style)
        return res
