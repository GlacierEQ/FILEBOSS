class WaterfallMemory(BaseMemory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add(self, event: Event):
        pass
