from datetime import datetime, timedelta

import pandas as pd

from src.tools.schema.adjust_date import AdjustDateInputModel


def adjust_date(**kwargs: AdjustDateInputModel) -> str:
    """
    Description:
        Use this tool to adjust a date based on some number of days in the past or future.

    Examples:
    >>> # Usage Example:
    adjust_date(date="April 10, 2025", delta_days=16)

    >>> # Usage Example:
    adjust_date(date="January 10, 2025", delta_days=-30)

    >>> # Usage Example:
    adjust_date(date="Mar 1, 2024", delta_days=2)

    >>> # Usage Example:
    adjust_date(date="2025-04-17", delta_days=2)

    Returns:
        str: The adjusted date
    """
    date_input = AdjustDateInputModel.model_validate(kwargs)
    for format in date_input.formats:
        try:
            input_date = datetime.strptime(date_input.date, format).date()
            adjusted_date = input_date + timedelta(days=date_input.delta_days)
            return adjusted_date.strftime(format)
        except ValueError:
            continue
    raise ValueError("Could not match to any known format")
