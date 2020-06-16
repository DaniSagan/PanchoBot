import sched
import threading
from sched import scheduler
from threading import Thread
from typing import List

import time

from data import Task


class TaskExecutor(object):
    def execute_task(self, task: Task) -> None:
        raise NotImplementedError()


class Scheduler(object):
    def __init__(self, executor: TaskExecutor):
        self.tasks: List[Task] = []
        self.executor: TaskExecutor = executor

    def initialize(self, tasks: List[Task]) -> None:
        for task in tasks:
            self.add_task(task)

    def add_task(self, task: Task) -> None:
        next_execution: int = task.schedule.next_execution()
        if next_execution is not None:
            s: scheduler = sched.scheduler(time.time, time.sleep)
            s.enter(next_execution - time.time(), 1, self.on_task_execution, (task,))
            t: Thread = threading.Thread(target=s.run)
            t.start()

    def on_task_execution(self, task: Task) -> None:
        self.executor.execute_task(task)
        task.schedule.last_execution = time.time()
        self.add_task(task)
