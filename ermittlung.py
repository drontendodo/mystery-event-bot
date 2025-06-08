import os
import discord
from discord.ext import commands
from discord import ui, Interaction
from dotenv import load_dotenv

load_dotenv()

submission_store = {}
awaiting_motiv = set()
correct_answers = {
    "moerder": os.getenv("RICHTIGER_MOERDER"),
    "tatwaffe": os.getenv("RICHTIGE_TATWAFFE"),
    "tatort": os.getenv("RICHTIGER_TATORT")
}

def setup_ermittlung(bot):

    class ButtonStep(ui.View):
        def __init__(self, category, options):
            super().__init__()
            self.category = category
            for label in options:
                self.add_item(ChoiceButton(label=label, category=category))

    class ChoiceButton(ui.Button):
        def __init__(self, label, category):
            super().__init__(label=label, style=discord.ButtonStyle.primary)
            self.category = category

        async def callback(self, interaction: Interaction):
            channel_id = interaction.channel.id
            if channel_id not in submission_store:
                submission_store[channel_id] = {}
            submission_store[channel_id][self.category] = self.label
            await interaction.response.send_message(f"✅ {self.category.capitalize()} gespeichert: **{self.label}**", ephemeral=True)

            if self.category == "moerder":
                await interaction.channel.send("🔪 Welche Tatwaffe wurde verwendet?", view=ButtonStep("tatwaffe", ["Gartenschere", "Weinflasche", "Kaminhaken", "Messer", "Skulptur"]))
            elif self.category == "tatwaffe":
                await interaction.channel.send("🏛️ Wo fand der Mord statt?", view=ButtonStep("tatort", ["Arbeitszimmer", "Garten", "Küche", "Weinkeller", "Eingangshalle"]))
            elif self.category == "tatort":
                awaiting_motiv.add(channel_id)
                await interaction.channel.send("🧠 Bitte schreibt jetzt euer vermutetes Motiv direkt als Nachricht in diesen Chat.")

    @bot.command()
    async def abgabe(ctx):
        for channel in ctx.guild.text_channels:
            if channel.category and channel.category.name.lower().startswith("ermittlergruppe"):
                submission_store[channel.id] = {}
                if channel.id in awaiting_motiv:
                    awaiting_motiv.remove(channel.id)
                await channel.send("🕵️‍♂️ Wer war eurer Meinung nach der Täter?", view=ButtonStep("moerder", ["Dodo", "Marco", "Derrick", "Henry", "Laura"]))

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        channel_id = message.channel.id
        if channel_id in awaiting_motiv and channel_id in submission_store and "motiv" not in submission_store[channel_id]:
            submission_store[channel_id]["motiv"] = message.content.strip()
            awaiting_motiv.remove(channel_id)

            # Zähle vollständige Abgaben
            total_groups = len([ch for ch in message.guild.text_channels if ch.category and ch.category.name.lower().startswith("ermittlergruppe")])
            submitted = sum(1 for abgabe in submission_store.values() if all(k in abgabe for k in ["moerder", "tatwaffe", "tatort", "motiv"]))
            await message.channel.send(f"✅ Motiv gespeichert.\n📨 Abgabe erhalten! ({submitted}/{total_groups} Gruppen haben die Abgabe bisher abgeschlossen)")

        await bot.process_commands(message)

    @bot.command()
    async def abgabefortschritt(ctx):
        total_groups = len([ch for ch in ctx.guild.text_channels if ch.category and ch.category.name.lower().startswith("ermittlergruppe")])
        submitted = sum(1 for abgabe in submission_store.values() if all(k in abgabe for k in ["moerder", "tatwaffe", "tatort", "motiv"]))
        await ctx.send(f"📊 Abgabefortschritt: {submitted}/{total_groups} Gruppen haben abgegeben.")

    @bot.command()
    async def ende(ctx):
        if not submission_store:
            await ctx.send("❌ Keine Abgaben vorhanden.")
            return

        auswertung = []
        for channel_id, abgabe in submission_store.items():
            punkte = 0
            details = []

            if abgabe.get("moerder") == correct_answers["moerder"]:
                punkte += 4
                details.append("✅ Täter richtig")
            else:
                details.append("❌ Täter falsch")

            if abgabe.get("tatwaffe") == correct_answers["tatwaffe"]:
                punkte += 3
                details.append("✅ Tatwaffe richtig")
            else:
                details.append("❌ Tatwaffe falsch")

            if abgabe.get("tatort") == correct_answers["tatort"]:
                punkte += 5
                details.append("✅ Tatort richtig")
            else:
                details.append("❌ Tatort falsch")

            if "motiv" in abgabe:
                punkte += 2
                details.append("💬 Motiv abgegeben")
            else:
                details.append("🕳️ Kein Motiv angegeben")

            channel = bot.get_channel(channel_id)
            auswertung.append((punkte, channel.name, details, channel))

        auswertung.sort(reverse=True, key=lambda x: x[0])

        for platz, (punkte, name, infos, channel) in enumerate(auswertung, start=1):
            gesamt = "🏑 **Ermittlungs-Auswertung** 🏑\n\n"
            gesamt += "🎉 Herzlichen Glückwunsch! Ihr habt das Mystery Event erfolgreich abgeschlossen!\n\n"
            gesamt += f"🧲 Eure Ermittlergruppe hat **{punkte} Punkte** erzielt!\n"
            gesamt += f"📌 Ihr seid damit auf dem **{platz}. Platz**!\n\n"

            gesamt += "📊 **Punkteübersicht:**\n"
            gesamt += "\n".join(f"- {i}" for i in infos)
            gesamt += "\n\n🏆 **Rangliste:**\n"

            for p, (pts, n, _, _) in enumerate(auswertung, start=1):
                fett = f"**{n}**" if n == name else n
                mark = " ← das seid ihr!" if n == name else ""
                gesamt += f"{p}. Platz - {pts} Punkte: {fett}{mark}\n"

            await channel.send(gesamt)

