"""
YDT 2721 卫星链路计算软件

根据中华人民共和国通信行业标准 YD/T 2721-2014
《地球静止轨道卫星固定业务的链路计算方法》实现
"""

from ._version import __version__
__author__ = "编程新"

from .calculator import complete_link_budget, complete_link_budget_from_input, LinkBudgetResult
from .output import (
    MarkdownReportGenerator,
    ExcelReportGenerator,
    JSONExporter,
    PDFReportGenerator,
    setup_chinese_fonts,
    FontManager,
)

__all__ = [
    "complete_link_budget",
    "complete_link_budget_from_input",
    "LinkBudgetResult",
    "MarkdownReportGenerator",
    "ExcelReportGenerator",
    "JSONExporter",
    "PDFReportGenerator",
    "setup_chinese_fonts",
    "FontManager",
]
