import copy
from abc import ABC, abstractmethod
from typing import List

import openai

from RAGchain.schema import Passage


class BaseLLM(ABC):
    """

    This class represents a LLM base class.
    It supports chat history and stream feature. Plus, it supports custom prompts, too.

    Attributes:
    - stream_end_token (str): The token used to indicate the end of a stream. Returns this token when stream is end.

    """
    stream_end_token: str = '<|endofstream|>'

    def __init__(self):
        """Initializes the LLM instance with a retrieval module."""
        self.chat_history: List[dict] = []
        self.chat_offset: int = 6

    @abstractmethod
    def ask(self,
            query: str,
            passages: List[Passage],
            stream: bool = False,
            *args, **kwargs) -> tuple[str, List[Passage]]:
        """
        Ask a question to the LLM model and get answer and used passages.
        :param query: question
        :param passages: passages to use for answering the question
        :param stream: if stream is true, use stream feature. Default is False.
        :param args: optional parameter for openai api llm
        :param kwargs: optional parameter for openai api llm

        :return answer: The answer to the question that llm generated.
        :return passages: The list of passages used to generate the answer.
        """
        pass

    @classmethod
    def generate_chat(cls, messages: List[dict], model: str,
                      stream: bool = False,
                      stream_func: callable = None,
                      *args, **kwargs) -> str:
        """
        Call chat_completion api at remote LLM server and return the answer.
        If stream is true, run stream_func for each response.
        And return cls.stream_end_token when stream is end.
        """
        response = openai.ChatCompletion.create(*args, **kwargs,
                                                model=model,
                                                messages=messages,
                                                stream=stream)
        answer: str = ''
        if stream:
            for chunk in response:
                if len(chunk["choices"]) > 0:
                    content = chunk["choices"][0].get("delta", {}).get("content")
                    if content is not None:
                        stream_func(content)
                        answer += content
            stream_func(cls.stream_end_token)
        else:
            answer = response["choices"][0]["message"]["content"]
        return answer

    @classmethod
    def generate(cls, prompt: str, model: str,
                 stream: bool = False,
                 stream_func: callable = None,
                 *args, **kwargs) -> str:
        """
        Call completion api at remote LLM server and return the answer.
        If stream is true, run stream_func for each response.
        And return cls.stream_end_token when stream is end.
        """
        response = openai.Completion.create(
            model=model,
            prompt=prompt,
            stream=stream,
            *args, **kwargs
        )
        answer: str = ''
        if stream:
            for event in response:
                if len(event['choices']) > 0:
                    text = event['choices'][0]['text']
                    stream_func(text)
                    answer += text
            stream_func(cls.stream_end_token)
        else:
            answer = response["choices"][0]["text"]
        return answer

    def add_chat_history(self, query: str, answer: str):
        """
        Adds a query and its corresponding answer to the chat history.
        """
        self.chat_history.append({"role": "user", "content": query})
        self.chat_history.append({"role": "assistant", "content": answer})

    def clear_chat_history(self):
        """
        Clears the chat history and returns a copy of the cleared history.
        """
        store_chat_history = copy.deepcopy(self.chat_history)
        self.chat_history.clear()
        return store_chat_history
