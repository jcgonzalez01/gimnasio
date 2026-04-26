
import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from app.services.hikvision import HikvisionISAPI

print(f"HikvisionISAPI mro: {HikvisionISAPI.__mro__}")
print(f"open_door defined in: {HikvisionISAPI.open_door.__qualname__}")

import inspect
print(f"open_door source file: {inspect.getsourcefile(HikvisionISAPI.open_door)}")
