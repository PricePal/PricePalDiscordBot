from discord.ui import View
import discord
from db.database import SessionLocal
from db.repositories import create_reaction

class ShoppingItemView(View):
    """
    A view for a shopping item.
    """
    
    def __init__(self, query_id: str, rec_item_id: str):
        super().__init__(timeout=180)  # Extended timeout to 3 minutes
        self.query_id = query_id
        self.rec_item_id = rec_item_id
        self.db = SessionLocal()
        
    def on_timeout(self):
        self.db.close()
        return super().on_timeout()

    @discord.ui.button(label="Add to Wishlist", style=discord.ButtonStyle.success, emoji="❤️")
    async def on_wishlist_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Defer the response right away to buy more time
            await interaction.response.defer(ephemeral=True)
            
            # Create the reaction in database
            create_reaction(self.db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="wishlist")
            
            # Send the confirmation message
            await interaction.followup.send("Added to your wishlist! Use `!wishlist` to view your saved items.", ephemeral=True)
            
        except discord.errors.NotFound:  # Handle interaction timeout
            # Interaction has expired, can't respond to it
            print(f"Interaction timed out for wishlist item {self.rec_item_id}")
        except discord.errors.DiscordServerError:
            # Server error from Discord
            try:
                await interaction.followup.send("Discord server error. Please try again later.", ephemeral=True)
            except:
                pass
        except discord.errors.HTTPException as e:
            print(f"HTTP Exception in wishlist button: {e.code} - {e.text}")
            try:
                if e.code == 10062:  # Unknown interaction error
                    pass  # Can't respond to timed out interaction
                else:
                    await interaction.followup.send(f"Discord error: {e.text}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"Wishlist error: {e}")
            try:
                # Try to give user feedback if database operation failed
                await interaction.followup.send("Something went wrong adding to your wishlist. Please try again.", ephemeral=True)
            except:
                pass
            finally:
                # Ensure database session is properly handled in case of error
                try:
                    self.db.rollback()
                except:
                    pass

    @discord.ui.button(label="Dislike", style=discord.ButtonStyle.danger, emoji="👎")
    async def on_dislike_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Defer the response right away to buy more time
            await interaction.response.defer(ephemeral=True)
            
            # Create the reaction in database
            create_reaction(self.db, query_id=self.query_id, recommended_item_id=self.rec_item_id, reaction_type="dislike")
            
            # Send the confirmation message
            await interaction.followup.send("You disliked this item. We'll use this to improve your recommendations!", ephemeral=True)
            
        except discord.errors.NotFound:  # Handle interaction timeout
            # Interaction has expired, can't respond to it
            print(f"Interaction timed out for dislike on item {self.rec_item_id}")
        except discord.errors.DiscordServerError:
            # Server error from Discord
            try:
                await interaction.followup.send("Discord server error. Please try again later.", ephemeral=True)
            except:
                pass
        except discord.errors.HTTPException as e:
            print(f"HTTP Exception in dislike button: {e.code} - {e.text}")
            try:
                if e.code == 10062:  # Unknown interaction error
                    pass  # Can't respond to timed out interaction
                else:
                    await interaction.followup.send(f"Discord error: {e.text}", ephemeral=True)
            except:
                pass
        except Exception as e:
            print(f"Dislike error: {e}")
            try:
                # Try to give user feedback if database operation failed
                await interaction.followup.send("Something went wrong recording your dislike. Please try again.", ephemeral=True)
            except:
                pass
            finally:
                # Ensure database session is properly handled in case of error
                try:
                    self.db.rollback()
                except:
                    pass