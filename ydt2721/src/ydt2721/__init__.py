"""
YDT 2721 卫星链路计算软件

根据中华人民共和国通信行业标准 YD/T 2721-2014
《地球静止轨道卫星固定业务的链路计算方法》实现
"""

__version__ = "1.0.0"
__author__ = "编程新"

from .calculator import complete_link_budget, LinkBudgetResult
from .output import (
    MarkdownReportGenerator,
    ExcelReportGenerator,
    JSONExporter,
    PDFReportGenerator,
)

__all__ = [
    "complete_link_budget",
    "LinkBudgetResult",
    "MarkdownReportGenerator",
    "ExcelReportGenerator",
    "JSONExporter",
    "PDFReportGenerator",
]
