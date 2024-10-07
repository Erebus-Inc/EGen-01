from pydantic import BaseModel
from typing import Optional

class processRequest(BaseModel):
    fileID : str
    chunk_size : Optional[int] = 100
    overlap_size : Optional[int] = 20
    # user actions
    do_reset : Optional[int] = 0