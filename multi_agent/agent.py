from .agents.coordinator import coordinator
# from .agents.researcher import researcher
# from .agents.reviewer import reviewer
# from .agents.writer import writer
from .agents.trendAnalyzer import trendAnalyzer
from .tools.run_files import cleanup_old_runs

cleanup_old_runs()

root_agent = coordinator
