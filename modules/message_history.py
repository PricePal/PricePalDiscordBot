class MessageHistory:
    def __init__(self, max_context=5):
        self.recent_messages = {}
        self.max_context = max_context
    
    def add_message(self, channel_id, message_content):
        """Add a message to the history for a channel."""
        if channel_id not in self.recent_messages:
            self.recent_messages[channel_id] = []
            
        self.recent_messages[channel_id].append(message_content)
        if len(self.recent_messages[channel_id]) > self.max_context:
            self.recent_messages[channel_id].pop(0)
    
    def get_context(self, channel_id):
        """Get the message history for a channel."""
        return self.recent_messages.get(channel_id, []) 