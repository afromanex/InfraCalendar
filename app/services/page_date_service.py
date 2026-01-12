class PageDateService:
    """Service for date formatting and normalization.

    Provides utilities for normalizing LLM-extracted date and recurrence data
    for database storage and iCalendar format compatibility.
    """

    @staticmethod
    def format_date(date_obj):
        """Convert dict date to ISO string format."""
        if isinstance(date_obj, dict):
            year = date_obj.get("year")
            month = date_obj.get("month", 1)
            day = date_obj.get("day", 1)
            if year:
                return f"{year:04d}-{month:02d}-{day:02d}"
        return date_obj
    
    @staticmethod
    def format_rrule(rrule_obj):
        """Convert dict rrule to iCalendar RRULE string, but filter out likely LLM hallucinations."""
        if isinstance(rrule_obj, dict):
            # Ignore generic DAILY rules without count/until - likely LLM inference
            freq = rrule_obj.get("freq", "").upper()
            interval = rrule_obj.get("interval")
            count = rrule_obj.get("count")
            until = rrule_obj.get("until")
            
            # Filter out generic DAILY/WEEKLY rules without end conditions
            if freq in ["DAILY", "WEEKLY"] and interval == 1 and not count and not until:
                return None
            
            parts = []
            if freq:
                parts.append(f"FREQ={freq}")
            if interval and interval != 1:
                parts.append(f"INTERVAL={interval}")
            if count:
                parts.append(f"COUNT={count}")
            if until:
                parts.append(f"UNTIL={until}")
            return ";".join(parts) if parts else None
        return rrule_obj


__all__ = ["PageDateService"]
