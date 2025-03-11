import discord
from discord.ui import View
from discord.ext import commands
from views.shopping_item_view import ShoppingItemView
import requests
from bs4 import BeautifulSoup
import requests
from io import BytesIO
from PIL import Image


def get_preview_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to find Open Graph image tag first
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image['content']:
            return og_image['content']

        # If no Open Graph image, try to find a regular image tag
        image_tag = soup.find('img')
        if image_tag and image_tag.has_attr('src'):
                # Handle relative URLs
            if image_tag['src'].startswith('http'):
                image_url = image_tag['src']
            else:
                from urllib.parse import urljoin
                image_url = urljoin(url, image_tag['src'])
            return image_url

        return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None
    except Exception as e:
            print(f"An error occurred: {e}")
            return None


async def recommended_item_embed(ctx: commands.Context | None, message: discord.Message | None,
                                 item_name: str, price: str, link: str,
                                 query_id: str, rec_item_id: str, image_url: str = None):
    """
    Sends an embed with a shopping item view.
    """
    
    print("Beginning recommended item embed")
    # Create an embed
    embed = discord.Embed(
        title=item_name,
        url=link,  # Make the title clickable
        description=f"**Price:** {price}",  # Move price to description for cleaner look
        color=discord.Color.brand_green()  # Use a more appealing color
    )
    
    # Add link as a field with better formatting
    formatted_link = f"[Click to view item]({link})"
    embed.add_field(name="Product Link", value=formatted_link, inline=False)
    
    # Try to get image URL from the link if no image_url is provided
    print("Getting image from URL")
    if not image_url and link:
        image_url = get_preview_image(link)
        print(f"Image URL: {image_url}")
    
    # Add image to embed if image_url is available
    print("Adding image to embed")
    if image_url:
        embed.set_image(url=image_url)
    
    
    # Add timestamp for freshness
    embed.timestamp = discord.utils.utcnow()

    view = ShoppingItemView(query_id, rec_item_id)
    
    # Send the embed with the buttons
    if ctx:
        await ctx.send(embed=embed, view=view)
    else:
        await message.channel.send(embed=embed, view=view)