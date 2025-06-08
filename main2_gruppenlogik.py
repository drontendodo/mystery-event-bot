import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random
from ki_dialog import setup_ki_dialog
from ermittlung import setup_ermittlung




load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
setup_ki_dialog(bot)
setup_ermittlung(bot)

user_group_mapping = {}  # Speichert Zuordnung von User-ID zu Gruppennamen

def alphabet_name(index):
    gruppe_namen = [
        "Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta",
        "Eta", "Theta", "Iota", "Kappa", "Lambda", "Mu",
        "Nu", "Xi", "Omikron", "Pi", "Rho", "Sigma",
        "Tau", "Upsilon", "Phi", "Chi", "Psi", "Omega"
    ]
    if index < len(gruppe_namen):
        return gruppe_namen[index]
    else:
        return f"{index + 1}"

@bot.event
async def on_ready():
    print(f"Bot ist online als {bot.user}")

@bot.command()
async def gruppenstart(ctx):
    guild = ctx.guild
    await guild.chunk()
    members = [m for m in guild.members if not m.bot and not m.pending]
    if not members:
        await ctx.send("❌ Keine Teilnehmer gefunden.")
        return

    random.shuffle(members)
    gruppengroesse = 1
    gruppen = [members[i:i + gruppengroesse] for i in range(0, len(members), gruppengroesse)]

    category = await guild.create_category("Ermittlergruppen")

    for idx, gruppe in enumerate(gruppen):
        name = f"ermittlergruppe-{alphabet_name(idx).lower()}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
        }
        text_channel = await guild.create_text_channel(name, category=category, overwrites=overwrites)
        voice_channel = await guild.create_voice_channel(f"{name}-voice", category=category, overwrites=overwrites)

        for member in gruppe:
            await text_channel.set_permissions(member, read_messages=True, send_messages=True)
            await voice_channel.set_permissions(member, connect=True, speak=True, view_channel=True)

            user_group_mapping[member.id] = alphabet_name(idx)

            voice_link = f"https://discord.com/channels/{guild.id}/{voice_channel.id}"
            try:
                await member.send(
                    f"🔎 **Willkommen in der Ermittlergruppe {alphabet_name(idx)}**!\n\n"
                    f"Deine Gruppe hat zwei Dinge:\n"
                    f"- 🎤 **Einen Sprachkanal** → Hier kannst du dich mit deinen Ermittlerkollegen unterhalten.\n"
                    f"- 💬 **Einen Textkanal** → Hier kannst du dich mit den Zeugen unterhalten und ermitteln.\n\n"
                    f"👉 **Besuche zuerst den Sprachkanal:** {voice_link}"
                )
            except discord.Forbidden:
                print(f"❌ Konnte {member.name} keine DM senden.")

        info_text_voice = (
            f"🎙️ Willkommen in **Ermittlergruppe {alphabet_name(idx)}**\n"
            f"Hier könnt ihr euch austauschen und gemeinsam ermitteln.\n"
            f"👉 Der zugehörige Textkanal ist: <#{text_channel.id}>"
        )
        await voice_channel.send(info_text_voice)

        info_text_text = (
            f"👁️‍🗨️ **Willkommen im Ermittlungsraum von Ermittlergruppe {alphabet_name(idx)}**\n\n"
            f"Dieser Kanal ist dafür da, um Zeugen zu befragen.\n"
            f"💡 **Hinweis:** Pro Zeuge hat eure Gruppe nur **10 Fragen**. Sprecht euch ab, welche Fragen ihr stellen wollt.\n\n"
            f"🧍‍♂️ Die Verdächtigen, die ihr befragen könnt, sind:\n"
            f"- 🤖 `dodo`\n"
            f"- 🧹 `laura`\n"
            f"- 🌿 `marco`\n"
            f"- 🍳 `derrick`\n"
            f"- 🎩 `henry`\n\n"
            f"📢 So befragt ihr einen Zeugen. Achtet darauf das Ausrufezeichen vor dem Namen zu setzen:\n"
            f"```\n!laura Was haben Sie in der Nacht gesehen?\n```"
        )
        info_message = await text_channel.send(info_text_text)

        try:
            await info_message.pin()
        except discord.HTTPException as e:
            print(f"⚠️ Konnte Nachricht nicht anpinnen: {e}")

    # ➕ Sondergruppe hinzufügen mit versteckten Rechten
    sonder_name = "ermittlergruppe-sonder"
    verwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False),}
    sonder_text = await guild.create_text_channel(sonder_name, category=category, overwrites=overwrites)
    sonder_voice = await guild.create_voice_channel(f"{sonder_name}-voice", category=category, overwrites=overwrites)
    await sonder_text.send(
    "🛠️ Dies ist der Kanal für manuelle Zuweisungen.\n"
    "Admins können hier Teilnehmer hinzufügen, wenn es bei der Gruppenerstellung Probleme gab.")


@bot.command()
async def gruppenreset(ctx):
    for category in ctx.guild.categories:
        if category.name.lower().startswith("ermittlergruppe"):
            for channel in category.channels:
                await channel.delete()
            await category.delete()
            await ctx.send("🔁 Ermittlergruppen wurden zurückgesetzt.")
            return
    await ctx.send("ℹ️ Keine Ermittlergruppen zum Zurücksetzen gefunden.")

@bot.command()
async def gruppe(ctx):
    gruppe_name = user_group_mapping.get(ctx.author.id)
    if gruppe_name:
        await ctx.send(f"🔍 Du bist in **Ermittlergruppe {gruppe_name}**.")
    else:
        await ctx.send("ℹ️ Du wurdest bisher keiner Ermittlergruppe zugewiesen.")

fertige_user = set()

@bot.command()
async def fertig(ctx):
    user = ctx.author
    fertige_user.add(user.id)
    guild = ctx.guild
    total_users = [m for m in guild.members if not m.bot and not m.pending]
    fertig_anzahl = len(fertige_user)
    gesamt_anzahl = len(total_users)

    await ctx.send(
        f"✅ **{user.display_name} hat die Abschlussprüfung bestanden!** 🎉\n\n"
        f"Wir warten noch auf die anderen Teilnehmer.\n"
        f"🕒 Bitte habe etwas Geduld und chatte solange mit den anderen in der Lobby.\n\n"
        f"👥 **Fortschritt:** {fertig_anzahl} von {gesamt_anzahl} sind bereit."
    )

@bot.command()
@commands.has_permissions(administrator=True)
async def fortschritt(ctx):
    guild = ctx.guild
    total_users = [m for m in guild.members if not m.bot and not m.pending]
    fertig_anzahl = len(fertige_user)
    gesamt_anzahl = len(total_users)
    await ctx.send(f"📊 Fortschritt: **{fertig_anzahl} von {gesamt_anzahl}** Teilnehmer:innen haben `!fertig` eingegeben.")


bot.run(TOKEN)
