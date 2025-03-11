import discord
import random
from typing import List, Tuple

class LoadingAnimations:
    """Provides loading animations for various bot operations"""
    
    # Collection of shopping-themed loading GIF URLs
    LOADING_GIFS = [
        "https://media.giphy.com/media/cnzP4cmBsiOrccg20V/giphy.gif?cid=ecf05e47547niosrdb8lxlkr98hsxzc3hve1m6e5gr324dzv&ep=v1_gifs_search&rid=giphy.gif&ct=g",  
        "https://media.giphy.com/media/6xEEzPgehze0DBsyX6/giphy.gif?cid=790b76115nqwbytrqi5tynhh40jv39lppynig6e3fggyeily&ep=v1_gifs_search&rid=giphy.gif&ct=g",  
        "https://media.giphy.com/media/jAYUbVXgESSti/giphy.gif?cid=790b7611haak20n6f1d7jh0ftj7bf2dwzli7jsnbtyw2visa&ep=v1_gifs_search&rid=giphy.gif&ct=g",  
        "https://media.giphy.com/media/hL9q5k9dk9l0wGd4e0/giphy.gif?cid=ecf05e47cejsw6c05cpelhomki6t9elliitxnzq3utltezlo&ep=v1_gifs_search&rid=giphy.gif&ct=g",  
        "https://media.giphy.com/media/KG4PMQ0jyimywxNt8i/giphy.gif?cid=790b76115gjsapbjk3fowzsttedc5rdpcrb8e71jziiz29w6&ep=v1_gifs_search&rid=giphy.gif&ct=g"   
    ]
    
    # Different operations can have specific GIFs
    OPERATION_GIFS = {
        "search": [
            "https://media.giphy.com/media/HdkzWcDvoRmLmkrWOt/giphy.gif?cid=790b76110dxwv5lkkgeftrisbm2pb8zrxvufc6n20yffsf4c&ep=v1_gifs_search&rid=giphy.gif&ct=g"   
        ],
        "profile": [ 
            "https://media.giphy.com/media/3oKIPEqDGUULpEU0aQ/giphy.gif?cid=790b76112npqu5fetp6pdepqsh3ynmafgo9trlxdyu1rag4a&ep=v1_gifs_search&rid=giphy.gif&ct=g"  
        ],
        "surprise": [  
            "https://media.giphy.com/media/1fZSFCEtRQ1gLKAeGv/giphy.gif?cid=790b7611wo9yy5qo7nsi4sx2fyvkbhaocpaebi989xfarrj5&ep=v1_gifs_search&rid=giphy.gif&ct=g"  
        ]
    }
    
    @staticmethod
    def get_loading_embed(operation: str = None, message: str = None) -> Tuple[discord.Embed, str]:
        """Returns an embed with a loading animation for the specified operation"""
        
        # Select operation-specific or generic loading GIF
        if operation and operation in LoadingAnimations.OPERATION_GIFS:
            gif_url = random.choice(LoadingAnimations.OPERATION_GIFS[operation])
        else:
            gif_url = random.choice(LoadingAnimations.LOADING_GIFS)
            
        # Create default messages if none provided
        if not message:
            messages = {
                "search": "🔍 **Searching for products...**",
                "profile": "📊 **Analyzing your shopping profile...**",
                "surprise": "✨ **Finding something special for you...**"
            }
            message = messages.get(operation, "⏳ **Working on it...**")
            
        # Create the embed
        embed = discord.Embed(
            description=message,
            color=discord.Color.blue()
        )
        embed.set_image(url=gif_url)
        
        return embed, gif_url 

    @staticmethod
    async def update_loading_status(ctx, status_message, operation, messages, delay=3.0):
        """Updates the loading message periodically to show progress"""
        import asyncio
        
        for i, message in enumerate(messages):
            if i > 0:  # Skip the first message as it's already displayed
                try:
                    loading_embed, _ = LoadingAnimations.get_loading_embed(operation, message)
                    await status_message.edit(embed=loading_embed)
                    await asyncio.sleep(delay)
                except Exception as e:
                    print(f"Failed to update loading status: {e}")
                    break 