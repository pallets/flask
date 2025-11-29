"""
Cron expression parser for scheduling tasks
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Set
from .exceptions import CronParseError


class CronParser:
    """Parse and validate cron expressions"""
    
    # Cron字段: 分 时 日 月 周
    FIELD_NAMES = ['minute', 'hour', 'day', 'month', 'weekday']
    FIELD_RANGES = {
        'minute': (0, 59),
        'hour': (0, 23), 
        'day': (1, 31),
        'month': (1, 12),
        'weekday': (0, 6)  # 0=Monday, 6=Sunday
    }
    
    MONTH_NAMES = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    
    WEEKDAY_NAMES = {
        'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 
        'fri': 4, 'sat': 5, 'sun': 6
    }
    
    def __init__(self, expression: str):
        """Initialize cron parser with expression"""
        self.expression = expression.strip()
        self.fields = {}
        self._parse()
    
    def _parse(self):
        """Parse cron expression"""
        parts = self.expression.split()
        
        if len(parts) != 5:
            raise CronParseError(f"Invalid cron expression '{self.expression}': expected 5 fields, got {len(parts)}")
        
        for i, (field_name, part) in enumerate(zip(self.FIELD_NAMES, parts)):
            self.fields[field_name] = self._parse_field(field_name, part)
    
    def _parse_field(self, field_name: str, field_value: str) -> Set[int]:
        """Parse individual cron field"""
        min_val, max_val = self.FIELD_RANGES[field_name]
        result = set()
        
        # 处理逗号分隔的多个值
        for part in field_value.split(','):
            result.update(self._parse_field_part(field_name, part.strip(), min_val, max_val))
        
        return result
    
    def _parse_field_part(self, field_name: str, part: str, min_val: int, max_val: int) -> Set[int]:
        """Parse field part (handles ranges, steps, wildcards)"""
        # 处理通配符
        if part == '*':
            return set(range(min_val, max_val + 1))
        
        # 处理步长 (*/5, 1-10/2)
        if '/' in part:
            base, step = part.split('/', 1)
            try:
                step = int(step)
                if step <= 0:
                    raise ValueError("Step must be positive")
            except ValueError as e:
                raise CronParseError(f"Invalid step value in '{part}': {e}")
            
            if base == '*':
                values = set(range(min_val, max_val + 1))
            else:
                values = self._parse_field_part(field_name, base, min_val, max_val)
            
            return {v for v in values if (v - min_val) % step == 0}
        
        # 处理范围 (1-5)
        if '-' in part:
            start, end = part.split('-', 1)
            try:
                start_val = self._parse_single_value(field_name, start, min_val, max_val)
                end_val = self._parse_single_value(field_name, end, min_val, max_val)
                if start_val > end_val:
                    raise ValueError("Range start must be <= end")
                return set(range(start_val, end_val + 1))
            except ValueError as e:
                raise CronParseError(f"Invalid range in '{part}': {e}")
        
        # 处理单个值
        try:
            return {self._parse_single_value(field_name, part, min_val, max_val)}
        except ValueError as e:
            raise CronParseError(f"Invalid value in '{part}': {e}")
    
    def _parse_single_value(self, field_name: str, value: str, min_val: int, max_val: int) -> int:
        """Parse single value (handles numeric and named values)"""
        # 尝试解析数字
        try:
            num_val = int(value)
            if min_val <= num_val <= max_val:
                return num_val
            else:
                raise ValueError(f"Value {num_val} out of range [{min_val}, {max_val}]")
        except ValueError:
            pass
        
        # 尝试解析名称 (月份或星期)
        if field_name == 'month':
            lower_value = value.lower()
            if lower_value in self.MONTH_NAMES:
                return self.MONTH_NAMES[lower_value]
        elif field_name == 'weekday':
            lower_value = value.lower()
            if lower_value in self.WEEKDAY_NAMES:
                return self.WEEKDAY_NAMES[lower_value]
        
        raise ValueError(f"Invalid value '{value}' for field {field_name}")
    
    def get_next_run_time(self, from_time: Optional[datetime] = None) -> datetime:
        """Get next execution time after from_time"""
        if from_time is None:
            from_time = datetime.now()
        
        # 从下一秒开始检查
        next_time = from_time.replace(microsecond=0) + timedelta(seconds=1)
        
        # 限制最大搜索时间（避免无限循环）
        max_iterations = 366 * 24 * 60  # 一年内的分钟数
        iterations = 0
        
        while iterations < max_iterations:
            if self._matches_time(next_time):
                return next_time
            
            next_time += timedelta(minutes=1)
            iterations += 1
        
        raise CronParseError("Could not find next run time within reasonable timeframe")
    
    def _matches_time(self, dt: datetime) -> bool:
        """Check if datetime matches cron expression"""
        # 转换星期 (datetime weekday: 0=Monday, cron weekday: 0=Monday)
        weekday = dt.weekday()
        
        return (
            dt.minute in self.fields['minute'] and
            dt.hour in self.fields['hour'] and
            dt.day in self.fields['day'] and
            dt.month in self.fields['month'] and
            weekday in self.fields['weekday']
        )
    
    def __str__(self):
        return self.expression