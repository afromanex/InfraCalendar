class PageDateService:
    """Service for date formatting and normalization.

    Provides utilities for normalizing LLM-extracted date and recurrence data
    for database storage and iCalendar format compatibility.
    """

    @staticmethod
    def format_date(date_obj):
        """Convert dict or string date to ISO string format with year validation.
        
        Handles:
        - Dict with year/month/day keys
        - Human-readable strings like "Saturday, February 14, 2026"
        - ISO strings (passed through)
        
        If the year results in a date more than 1 year in the past, 
        adjusts to the next occurrence of that month/day.
        """
        from datetime import datetime, timedelta
        from dateutil import parser as dtparser
        
        # Handle dict format
        if isinstance(date_obj, dict):
            year = date_obj.get("year")
            month = date_obj.get("month", 1)
            day = date_obj.get("day", 1)
            
            if year:
                # Validate the date isn't too far in the past
                try:
                    parsed_date = datetime(year, month, day)
                    now = datetime.now()
                    
                    # If date is more than 1 year in the past, it's likely wrong
                    if parsed_date < now - timedelta(days=365):
                        # Use current or next year instead
                        year = now.year
                        # Check if this month/day has already passed this year
                        candidate = datetime(year, month, day)
                        if candidate < now - timedelta(days=30):  # If >30 days ago, use next year
                            year = now.year + 1
                
                except ValueError:
                    # Invalid date, return as-is
                    pass
                
                return f"{year:04d}-{month:02d}-{day:02d}"
        
        # Handle string format (e.g., "Saturday, February 14, 2026")
        elif isinstance(date_obj, str):
            # If already in ISO format (YYYY-MM-DD), return as-is
            if len(date_obj) == 10 and date_obj[4] == '-' and date_obj[7] == '-':
                return date_obj
            
            # Try to parse human-readable date strings
            try:
                parsed_date = dtparser.parse(date_obj)
                # Apply same year validation
                now = datetime.now()
                if parsed_date < now - timedelta(days=365):
                    year = now.year
                    candidate = parsed_date.replace(year=year)
                    if candidate < now - timedelta(days=30):
                        year = now.year + 1
                    parsed_date = parsed_date.replace(year=year)
                
                return parsed_date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                # If parsing fails, return as-is
                return date_obj
        
        return date_obj
    
    @staticmethod
    def format_location(location_obj):
        """Convert dict location to string format.
        
        If location is a dict with 'name' and/or 'address', combine them.
        Otherwise return as-is.
        """
        if isinstance(location_obj, dict):
            name = location_obj.get("name", "")
            address = location_obj.get("address", "")
            
            if name and address:
                return f"{name}, {address}"
            elif name:
                return name
            elif address:
                return address
            else:
                return None
        return location_obj
    
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
