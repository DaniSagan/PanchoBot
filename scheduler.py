import sched
import threading
from typing import List

import time

from data import Task


class TaskExecutor(object):
    def execute_task(self, task: Task):
        raise NotImplementedError()


class Scheduler(object):
    def __init__(self, executor: TaskExecutor):
        self.tasks = []  # type: List[Task]
        self.executor = executor  # type: TaskExecutor

    def initialize(self, tasks: List[Task]):
        for task in tasks:
            self.add_task(task)

    def add_task(self, task: Task):
        next_execution = task.schedule.next_execution()  # type: int
        if next_execution is not None:
            s = sched.scheduler(time.time, time.sleep)
            s.enter(next_execution - time.time(), 1, self.on_task_execution, (task,))
            t = threading.Thread(target=s.run)
            t.start()

    def on_task_execution(self, task: Task):
        self.executor.execute_task(task)
        task.schedule.last_execution = time.time()
        self.add_task(task)
