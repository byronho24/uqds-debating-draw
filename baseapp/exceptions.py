class NotEnoughJudgesException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class NotEnoughAttendancesException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class CannotFindWorkingConfigurationException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class NotEnoughRoomsException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)