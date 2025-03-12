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
        await interaction.response.defer(ephemeral=True)
        
        try:
            create_reaction(self.db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="wishlist")
            await interaction.followup.send("Added to your wishlist!", ephemeral=True)
        except Exception as e:
            print(f"Wishlist error: {e}")
            try:
                await interaction.followup.send(f"Error adding to wishlist", ephemeral=True)
            except:
                pass

    @discord.ui.button(label="Dislike", style=discord.ButtonStyle.danger, emoji="👎")
    async def on_dislike_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            create_reaction(self.db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="dislike")
            await interaction.followup.send("You disliked this item.", ephemeral=True)
        except Exception as e:
            print(f"Dislike error: {e}")
            try:
                await interaction.followup.send(f"Error recording your dislike", ephemeral=True)
            except:
                pass