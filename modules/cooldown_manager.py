from time import time

class CooldownManager:
    def __init__(self, cooldown_seconds=30):
        self.channel_last_called = {}
        self.cooldown_seconds = cooldown_seconds
        self.last_searched_query = {}
    
    def should_call_llm(self, channel_id):
        """Returns True if enough time has passed since last LLM call for this channel."""
        now = time()
        if channel_id in self.channel_last_called:
            last_called = self.channel_last_called[channel_id]
            if now - last_called < self.cooldown_seconds:
                return False
        self.channel_last_called[channel_id] = now
        return True
    
    def is_duplicate_query(self, channel_id, query):
        """Check if this is the same query as the last one for this channel."""
        is_duplicate = self.last_searched_query.get(channel_id) == query
        if not is_duplicate:
            self.last_searched_query[channel_id] = query
        return is_duplicate
