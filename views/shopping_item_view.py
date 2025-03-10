from discord.ui import View
import discord
from db.database import SessionLocal
from db.repositories import create_reaction

class ShoppingItemView(View):
    """
    A view for a shopping item.
    """
    
    def __init__(self, query_id: str, rec_item_id: str):
            super().__init__()
            self.query_id = query_id
            self.rec_item_id = rec_item_id
            self.db = SessionLocal()
        
    def on_timeout(self):
        self.db.close()
        return super().on_timeout()

    @discord.ui.button(label="Add to Wishlist", style=discord.ButtonStyle.success, emoji="❤️")
    async def on_wishlist_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            create_reaction(self.db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="wishlist")
            await interaction.response.send_message("Added to your wishlist!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
            print(f"Wishlist error: {e}")

    @discord.ui.button(label="Dislike", style=discord.ButtonStyle.danger, emoji="👎")
    async def on_dislike_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            create_reaction(self.db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="dislike")
            await interaction.response.send_message("You disliked this item.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: {str(e)}", ephemeral=True)
            print(f"Dislike error: {e}")