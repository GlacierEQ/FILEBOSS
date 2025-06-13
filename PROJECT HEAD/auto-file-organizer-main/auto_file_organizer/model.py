# ----------------------- CONFIG STRUCTURE ---------------------------
class Config:
    def __init__(self, sort_by='type', depth=1, exceptions=None):
        self.sort_by = sort_by
        self.depth = depth
        self.exceptions = exceptions if exceptions else []
