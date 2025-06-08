import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from discord.ext import commands
from discord import Embed

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Kontext und Fragezähler
conversations = {}
question_limits = {}

# Prompts laden
with open("prompts.json", "r", encoding="utf-8") as f:
    PROMPTS = json.load(f)

# Mapping von Zeugen zu Emojis
WITNESS_EMOJIS = {
    "laura": "🧹",
    "dodo": "🤖",
    "marco": "🌿",
    "derrick": "🍳",
    "henry": "🎩"
}

# Bild-URLs
CHARACTER_IMAGES = {
    "laura": "https://media.discordapp.net/attachments/1381337778608144587/1381338128954163370/unblurimageai_unblur_ChatGPT_Image_May_30_2025_11_58_16_AM.png",
    "henry": "https://media.discordapp.net/attachments/1381337778608144587/1381338191335919646/unblurimageai_unblur_ChatGPT_Image_May_30_2025_11_53_16_AM.png",
    "derrick": "https://media.discordapp.net/attachments/1381337778608144587/1381338248206356510/unblurimageai_unblur_ChatGPT_Image_May_30_2025_11_46_19_AM.png",
    "marco": "https://media.discordapp.net/attachments/1381337778608144587/1381338295958503557/unblurimageai_unblur_ChatGPT_Image_May_30_2025_11_41_34_AM.png",
    "dodo": "https://media.discordapp.net/attachments/1381337778608144587/1381338345917124839/unblurimageai_unblur_face-swap.png"
}

MAX_QUESTIONS = 10

def register_witness_command(bot: commands.Bot, name: str):
    @bot.command(name=name)
    async def witness_command(ctx, *, message: str):
        group_id = ctx.channel.id
        witness = name.lower()

        # Initialisierung
        if group_id not in conversations:
            conversations[group_id] = {}
            question_limits[group_id] = {}

        if witness not in conversations[group_id]:
            conversations[group_id][witness] = [
                {"role": "system", "content": PROMPTS[witness]}
            ]
            question_limits[group_id][witness] = 0

        # Fragenlimit prüfen
        if question_limits[group_id][witness] >= MAX_QUESTIONS:
            await ctx.send(f"❌ Ihr habt das Fragenlimit für {witness.capitalize()} erreicht.")
            return

        # Verlauf updaten
        conversations[group_id][witness].append({"role": "user", "content": message})

        # Antwort von OpenAI holen
        try:
            response = client.chat.completions.create(
                model=model,
                messages=conversations[group_id][witness]
            )
            reply = response.choices[0].message.content.strip()

            conversations[group_id][witness].append({"role": "assistant", "content": reply})
            question_limits[group_id][witness] += 1

            remaining = MAX_QUESTIONS - question_limits[group_id][witness]
            emoji = WITNESS_EMOJIS.get(witness, "❓")
            image_url = CHARACTER_IMAGES.get(witness)

            # Bild senden (vor der Antwort)
            if image_url:
                await ctx.send(image_url)

            embed = Embed(title=f"{emoji} {witness.capitalize()} sagt:", description=reply, color=0xAAAAFF)
            await ctx.send(embed=embed)
            await ctx.send(f"ℹ️ Noch **{remaining}** Frage(n) übrig für {witness.capitalize()}.")

        except Exception as e:
            await ctx.send(f"⚠️ Fehler bei der KI-Antwort: {str(e)}")


# Alle Zeugenbefehle registrieren
def setup_ki_dialog(bot):
    for witness in PROMPTS.keys():
        register_witness_command(bot, witness)
