from dataclasses import dataclass
import datetime


@dataclass(frozen=True)
class Const():
    DT_FMT: str = "%Y%m%d%H%M%S"


class Util():

    @staticmethod
    def get_exe_dt_str() -> str:
        exe_dt = datetime.datetime.now()
        exe_dt_str = exe_dt.strftime(Const.DT_FMT)
        return exe_dt_str


if __name__ == "__main__":
    print(Util.get_exe_dt_str())