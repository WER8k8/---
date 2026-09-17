import inspect
import re

from app.services.hermes.executors import ExecutorRegistry
import app.services.hermes.planner_service as ps

src = inspect.getsource(ps)
driven = set(re.findall(r'executor="([a-z_]+)"', src))
registered = set(ExecutorRegistry.list_executors())
undriven = sorted(registered - driven)
print("REGISTERED:", sorted(registered))
print("DRIVEN in L1 templates:", sorted(driven))
print("UNDRIVEN:", undriven)