import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select
import json
import os
import asyncio
import random
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

TORNEOS_FILE = "torneos.json"
RANKING_FILE = "ranking.json"
CONFIG_FILE = "config.json"

# Estados por servidor
server_configs = {}  # {guild_id: {channel_id: ..., message_id: ..., torneo_seleccionado: ...}}
server_torneos = {}  # {guild_id: {torneo_name: {user_id: team_name}}}
server_salas = {}  # {guild_id: {sala_id: {nombre, hora_apertura, hora_cierre, jugadores[], canal_id, mensaje_id}}}

# Ranking global (compartido entre servidores)
ranking = {}

# Diccionario para almacenar tasks de cierre de salas
sala_timers = {}  # {sala_id: [cierre_task, recordatorio_task, contador_task]}

if os.path.exists(RANKING_FILE):
    with open(RANKING_FILE, "r") as f:
        ranking = json.load(f)
else:
    ranking = {}

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)
        server_configs = data.get("configs", {})
        server_torneos = data.get("torneos", {})
        server_salas = data.get("salas", {})
else:
    server_configs = {}
    server_torneos = {}
    server_salas = {}

def guardar_ranking():
    with open(RANKING_FILE, "w") as f:
        json.dump(ranking, f, indent=4)

def guardar_config():
    data = {"configs": server_configs, "torneos": server_torneos, "salas": server_salas}
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def guardar_torneos():
    guardar_config()

def get_server_torneos(guild_id):
    guild_id = str(guild_id)
    if guild_id not in server_torneos:
        server_torneos[guild_id] = {}
        guardar_config()
    return server_torneos[guild_id]

def get_server_config(guild_id):
    guild_id = str(guild_id)
    if guild_id not in server_configs:
        server_configs[guild_id] = {
            "channel_id": None,
            "message_id": None,
            "torneo_seleccionado": None
        }
        guardar_config()
    return server_configs[guild_id]

def get_server_salas(guild_id):
    guild_id = str(guild_id)
    if guild_id not in server_salas:
        server_salas[guild_id] = {}
        guardar_config()
    return server_salas[guild_id]

def readConfig():
    try:
        config_path = path.join(path.dirname(__file__), CONFIG_FILE)
        if path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        return {"configs": {}, "torneos": {}, "salas": {}, "notificaciones_salas": {}}
    except:
        return {"configs": {}, "torneos": {}, "salas": {}, "notificaciones_salas": {}}

def writeConfig(data):
    try:
        config_path = path.join(path.dirname(__file__), CONFIG_FILE)
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except:
        return False

async def logear(mensaje, guild_id):
    config = get_server_config(guild_id)
    if config["channel_id"]:
        channel = bot.get_channel(int(config["channel_id"]))
        if channel:
            await channel.send(mensaje)

# ----------------- MODALES ----------------- #
class UnirseModal(Modal):
    def __init__(self, torneo, guild_id):
        super().__init__(title=f"Unirse al torneo {torneo}")
        self.torneo = torneo
        self.guild_id = str(guild_id)
        self.equipo_input = TextInput(label="Nombre del equipo", placeholder="Ingresa el nombre de tu equipo")
        self.add_item(self.equipo_input)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        user_id = str(interaction.user.id)
        if self.torneo not in torneos:
            torneos[self.torneo] = {}
        torneos[self.torneo][user_id] = self.equipo_input.value
        guardar_torneos()
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=self.equipo_input.value)
        if not role:
            role = await guild.create_role(name=self.equipo_input.value)
            await logear(f'🆕 Se creó el equipo **{self.equipo_input.value}**.', self.guild_id)
        member = guild.get_member(interaction.user.id)
        if member:
            await member.add_roles(role)
        await interaction.response.send_message(f'✅ Te has unido al torneo **{self.torneo}** con el equipo **{self.equipo_input.value}**!', ephemeral=True)
        await logear(f'✅ {interaction.user.name} se unió al torneo {self.torneo} con el equipo {self.equipo_input.value}.', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class CambiarModal(Modal):
    def __init__(self, torneo, guild_id):
        super().__init__(title=f"Cambiar equipo en {torneo}")
        self.torneo = torneo
        self.guild_id = str(guild_id)
        self.equipo_input = TextInput(label="Nuevo equipo", placeholder="Ingresa el nombre del nuevo equipo")
        self.add_item(self.equipo_input)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        user_id = str(interaction.user.id)
        if self.torneo not in torneos or user_id not in torneos[self.torneo]:
            await interaction.response.send_message("❌ No estás inscrito en este torneo.", ephemeral=True)
            return
        guild = interaction.guild
        equipo_actual = torneos[self.torneo][user_id]
        role_actual = discord.utils.get(guild.roles, name=equipo_actual)
        if role_actual:
            member = guild.get_member(interaction.user.id)
            if member:
                await member.remove_roles(role_actual)
        torneos[self.torneo][user_id] = self.equipo_input.value
        guardar_torneos()
        role_nuevo = discord.utils.get(guild.roles, name=self.equipo_input.value)
        if not role_nuevo:
            role_nuevo = await guild.create_role(name=self.equipo_input.value)
            await logear(f'🆕 Se creó el equipo {self.equipo_input.value}.', self.guild_id)
        member = guild.get_member(interaction.user.id)
        if member:
            await member.add_roles(role_nuevo)
        await interaction.response.send_message(f'🔄 Has cambiado de **{equipo_actual}** a **{self.equipo_input.value}**!', ephemeral=True)
        await logear(f'🔄 {interaction.user.name} cambió de {equipo_actual} a {self.equipo_input.value}', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class EliminarUsuarioModal(Modal):
    def __init__(self, torneo, guild_id):
        super().__init__(title=f"Eliminar usuario en {torneo}")
        self.torneo = torneo
        self.guild_id = str(guild_id)
        self.user_input = TextInput(label="ID del usuario", placeholder="ID numérico del usuario")
        self.add_item(self.user_input)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores pueden usar esto.", ephemeral=True)
            return
        user_id = self.user_input.value
        if self.torneo not in torneos or user_id not in torneos[self.torneo]:
            await interaction.response.send_message("❌ Usuario no inscrito en este torneo.", ephemeral=True)
            return
        equipo = torneos[self.torneo][user_id]
        del torneos[self.torneo][user_id]
        guardar_torneos()
        member = interaction.guild.get_member(int(user_id))
        role = discord.utils.get(interaction.guild.roles, name=equipo)
        if member and role:
            await member.remove_roles(role)
        await interaction.response.send_message(f'❌ Usuario eliminado del torneo.', ephemeral=True)
        await logear(f'❌ Usuario {user_id} eliminado de {self.torneo} y del equipo {equipo}', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class EliminarEquipoModal(Modal):
    def __init__(self, torneo, guild_id):
        super().__init__(title=f"Eliminar equipo en {torneo}")
        self.torneo = torneo
        self.guild_id = str(guild_id)
        self.equipo_input = TextInput(label="Nombre del equipo", placeholder="Nombre exacto del equipo")
        self.add_item(self.equipo_input)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores pueden usar esto.", ephemeral=True)
            return
        equipo = self.equipo_input.value
        if self.torneo not in torneos:
            await interaction.response.send_message("❌ Torneo no existe.", ephemeral=True)
            return
        guild = interaction.guild
        eliminados = 0
        for user_id, user_equipo in list(torneos[self.torneo].items()):
            if user_equipo == equipo:
                del torneos[self.torneo][user_id]
                member = guild.get_member(int(user_id))
                role = discord.utils.get(guild.roles, name=equipo)
                if member and role:
                    await member.remove_roles(role)
                eliminados += 1
        guardar_torneos()
        await interaction.response.send_message(f'❌ Equipo **{equipo}** eliminado ({eliminados} miembros removidos).', ephemeral=True)
        await logear(f'❌ Equipo {equipo} eliminado del torneo {self.torneo}', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class FinalizarTorneoModal(Modal):
    def __init__(self, torneo, guild_id):
        super().__init__(title=f"Finalizar torneo {torneo}")
        self.torneo = torneo
        self.guild_id = str(guild_id)
        self.confirmacion = TextInput(label="Escribe 'CONFIRMAR' para finalizar", placeholder="CONFIRMAR")
        self.add_item(self.confirmacion)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores pueden usar esto.", ephemeral=True)
            return
        if self.confirmacion.value != "CONFIRMAR":
            await interaction.response.send_message("❌ Debes escribir 'CONFIRMAR' exactamente.", ephemeral=True)
            return
        if self.torneo not in torneos:
            await interaction.response.send_message("❌ Torneo no existe.", ephemeral=True)
            return
        guild = interaction.guild
        equipos_eliminados = set()
        for user_id, equipo in list(torneos[self.torneo].items()):
            member = guild.get_member(int(user_id))
            role = discord.utils.get(guild.roles, name=equipo)
            if member and role:
                await member.remove_roles(role)
            equipos_eliminados.add(equipo)
        for equipo in equipos_eliminados:
            role = discord.utils.get(guild.roles, name=equipo)
            if role:
                try:
                    await role.delete()
                except:
                    pass
        del torneos[self.torneo]
        guardar_torneos()
        
        # Limpiar selección si era este torneo
        config = get_server_config(self.guild_id)
        if config["torneo_seleccionado"] == self.torneo:
            config["torneo_seleccionado"] = None
            guardar_config()
        
        await interaction.response.send_message(f'✅ Torneo **{self.torneo}** finalizado y roles eliminados.', ephemeral=True)
        await logear(f'✅ Torneo {self.torneo} finalizado. Roles eliminados: {equipos_eliminados}', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class GanarTorneoModal(Modal):
    def __init__(self, torneo, guild_id):
        super().__init__(title=f"Registrar ganador torneo {torneo}")
        self.torneo = torneo
        self.guild_id = str(guild_id)
        self.equipo_input = TextInput(label="Equipo ganador", placeholder="Nombre exacto del equipo")
        self.add_item(self.equipo_input)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores pueden usar esto.", ephemeral=True)
            return
        equipo = self.equipo_input.value
        if equipo in ranking:
            ranking[equipo] += 1
        else:
            ranking[equipo] = 1
        guardar_ranking()
        await interaction.response.send_message(f'🏆 Equipo **{equipo}** registrado como ganador! Total victorias: {ranking[equipo]}', ephemeral=True)
        await logear(f'🏆 Equipo {equipo} ganó el torneo {self.torneo}. Total: {ranking[equipo]}', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class CrearTorneoModal(Modal):
    def __init__(self, guild_id):
        super().__init__(title="Crear Nuevo Torneo")
        self.guild_id = str(guild_id)
        self.nombre_input = TextInput(label="Nombre del torneo", placeholder="Ej: Torneo Navidad 2025")
        self.add_item(self.nombre_input)

    async def on_submit(self, interaction):
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores pueden crear torneos.", ephemeral=True)
            return
        nombre = self.nombre_input.value
        if nombre in torneos:
            await interaction.response.send_message(f"❌ El torneo **{nombre}** ya existe.", ephemeral=True)
            return
        torneos[nombre] = {}
        guardar_torneos()
        await interaction.response.send_message(f'🏆 Torneo **{nombre}** creado exitosamente!', ephemeral=True)
        await logear(f'🏆 Torneo {nombre} creado por {interaction.user.name}', self.guild_id)
        await actualizar_dashboard(interaction.guild)

class CrearSalaModal(Modal):
    def __init__(self, guild_id, channel_id):
        super().__init__(title="Crear Nueva Sala")
        self.guild_id = str(guild_id)
        self.channel_id = channel_id
        self.nombre_input = TextInput(label="Nombre de la Sala", placeholder="Ej: Sala Entrenamiento")
        self.apertura_input = TextInput(label="Hora de Apertura (HH:MM)", placeholder="19:00")
        self.cierre_input = TextInput(label="Hora de Cierre (HH:MM)", placeholder="21:00")
        self.add_item(self.nombre_input)
        self.add_item(self.apertura_input)
        self.add_item(self.cierre_input)

    async def on_submit(self, interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores pueden crear salas.", ephemeral=True)
            return
        
        nombre = self.nombre_input.value
        apertura = self.apertura_input.value
        cierre = self.cierre_input.value
        
        try:
            apertura_h, apertura_m = map(int, apertura.split(':'))
            cierre_h, cierre_m = map(int, cierre.split(':'))
        except:
            await interaction.response.send_message("❌ Formato de hora inválido. Usa HH:MM", ephemeral=True)
            return
        
        sala_id = str(int(datetime.now().timestamp()))
        salas = get_server_salas(self.guild_id)
        salas[sala_id] = {
            "nombre": nombre,
            "hora_apertura": apertura,
            "hora_cierre": cierre,
            "jugadores": [],
            "canal_id": str(self.channel_id),
            "mensaje_id": None
        }
        guardar_config()
        
        # Crear embed con botón
        embed = discord.Embed(title=f"🎮 Sala: {nombre}", color=discord.Color.green())
        embed.description = f"⏰ Apertura: **{apertura}** → Cierre: **{cierre}**\n⏳ Tiempo restante: Calculando..."
        embed.set_footer(text="Haz clic en el botón para unirte")
        
        view = SalaView(sala_id, self.guild_id)
        channel = bot.get_channel(self.channel_id)
        msg = await channel.send(embed=embed, view=view)
        
        salas[sala_id]["mensaje_id"] = str(msg.id)
        guardar_config()
        
        await interaction.response.send_message(f'✅ Sala **{nombre}** creada exitosamente!', ephemeral=True)
        
        # Programar cierre automático
        await programar_cierre_sala(self.guild_id, sala_id, cierre_h, cierre_m, msg.channel)

async def programar_cierre_sala(guild_id, sala_id, cierre_h, cierre_m, channel):
    """Programa cierre automático, recordatorio y contador de una sala"""
    guild_id = str(guild_id)
    salas = get_server_salas(guild_id)
    sala = salas.get(sala_id)
    if not sala:
        return
    
    # Calcular tiempo hasta cierre
    ahora = datetime.now()
    fecha_cierre = datetime.now().replace(hour=cierre_h, minute=cierre_m, second=0, microsecond=0)
    if fecha_cierre <= ahora:
        fecha_cierre = fecha_cierre.replace(day=fecha_cierre.day + 1)  # Próximo día si ya pasó
    
    tiempo_restante = (fecha_cierre - ahora).total_seconds()
    
    # Recordatorio 10 minutos antes
    if tiempo_restante > 600:
        await asyncio.sleep(tiempo_restante - 600)
        try:
            await channel.send(f"⏰ La sala **{sala['nombre']}** cierra en 10 minutos!")
        except:
            pass
    
    # Esperar a cierre
    if tiempo_restante > 0:
        await asyncio.sleep(tiempo_restante)
    
    # Cerrar sala - remover rol Jugador
    guild = bot.get_guild(int(guild_id))
    if guild:
        rol = discord.utils.get(guild.roles, name="Jugador")
        if rol:
            for user_id in sala["jugadores"]:
                try:
                    member = guild.get_member(int(user_id))
                    if member:
                        await member.remove_roles(rol)
                except:
                    pass
        
        # Desactivar botón en el mensaje
        if sala.get("mensaje_id"):
            try:
                msg = await channel.fetch_message(int(sala["mensaje_id"]))
                boton_desactivado = discord.ui.View()
                boton = discord.ui.Button(label="Sala cerrada ⏰", style=discord.ButtonStyle.secondary, disabled=True, custom_id="cerrado")
                boton_desactivado.add_item(boton)
                await msg.edit(view=boton_desactivado)
            except:
                pass
    
    # Eliminar sala
    del salas[sala_id]
    guardar_config()

class SalaView(View):
    def __init__(self, sala_id, guild_id):
        super().__init__(timeout=None)
        self.sala_id = sala_id
        self.guild_id = str(guild_id)
    
    @discord.ui.button(label="Unirse a Sala", style=discord.ButtonStyle.success, emoji="📝", custom_id="unirse_sala")
    async def unirse_sala(self, interaction: discord.Interaction, button: discord.ui.Button):
        salas = get_server_salas(self.guild_id)
        sala = salas.get(self.sala_id)
        
        if not sala:
            await interaction.response.send_message("❌ Sala no encontrada", ephemeral=True)
            return
        
        # Verificar horario
        ahora = datetime.now()
        hora_actual_minutos = ahora.hour * 60 + ahora.minute
        apertura_h, apertura_m = map(int, sala["hora_apertura"].split(':'))
        cierre_h, cierre_m = map(int, sala["hora_cierre"].split(':'))
        apertura_minutos = apertura_h * 60 + apertura_m
        cierre_minutos = cierre_h * 60 + cierre_m
        
        if hora_actual_minutos < apertura_minutos or hora_actual_minutos > cierre_minutos:
            await interaction.response.send_message("❌ La sala está cerrada en este horario ⏰", ephemeral=True)
            return
        
        # Asignar rol
        rol = discord.utils.get(interaction.guild.roles, name="Jugador")
        if not rol:
            rol = await interaction.guild.create_role(name="Jugador")
        
        member = interaction.user
        if member:
            await member.add_roles(rol)
        
        if str(member.id) not in sala["jugadores"]:
            sala["jugadores"].append(str(member.id))
            guardar_config()
        
        await interaction.response.send_message(f"✅ Te uniste a la sala **{sala['nombre']}** 🎮", ephemeral=True)

# ===== NOTIFICACIONES DE SALAS (FREE FIRE) ===== #
class SalasNotificacionesView(View):
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = str(guild_id)
    
    @discord.ui.button(label="Quiero jugar hoy", style=discord.ButtonStyle.green, emoji="🔥", custom_id="quiero_jugar")
    async def quiero_jugar(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = readConfig()
        if not config.get("notificaciones_salas"):
            config["notificaciones_salas"] = {}
        if not config["notificaciones_salas"].get(self.guild_id):
            config["notificaciones_salas"][self.guild_id] = {"jugadores_listos": []}
        
        settings = config["notificaciones_salas"][self.guild_id]
        jugador_data = {
            "user_id": str(interaction.user.id),
            "nombre": interaction.user.name,
            "estado": "confirmado",
            "fecha": datetime.now().isoformat()
        }
        
        # Evitar duplicados
        jugadores_actuales = settings.get("jugadores_listos", [])
        if not any(j["user_id"] == str(interaction.user.id) for j in jugadores_actuales):
            jugadores_actuales.append(jugador_data)
            settings["jugadores_listos"] = jugadores_actuales
            writeConfig(config)
        
        await interaction.response.send_message(f"✅ {interaction.user.mention} ¡Estás anotado para hoy! 🔥", ephemeral=True)
    
    @discord.ui.button(label="Notificarme", style=discord.ButtonStyle.blurple, emoji="🔔", custom_id="notificarme")
    async def notificarme(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = readConfig()
        if not config.get("notificaciones_salas"):
            config["notificaciones_salas"] = {}
        if not config["notificaciones_salas"].get(self.guild_id):
            config["notificaciones_salas"][self.guild_id] = {"jugadores_listos": []}
        
        settings = config["notificaciones_salas"][self.guild_id]
        jugador_data = {
            "user_id": str(interaction.user.id),
            "nombre": interaction.user.name,
            "estado": "notificado",
            "fecha": datetime.now().isoformat()
        }
        
        jugadores_actuales = settings.get("jugadores_listos", [])
        if not any(j["user_id"] == str(interaction.user.id) for j in jugadores_actuales):
            jugadores_actuales.append(jugador_data)
            settings["jugadores_listos"] = jugadores_actuales
            writeConfig(config)
        
        await interaction.response.send_message(f"✅ {interaction.user.mention} ¡Te notificaremos cuando sea! 🔔", ephemeral=True)
    
    @discord.ui.button(label="Scrim Ready", style=discord.ButtonStyle.red, emoji="⚔️", custom_id="scrim_ready")
    async def scrim_ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"⚔️ {interaction.user.mention} está listo para SCRIM!", ephemeral=False)

# ----------------- DASHBOARD ----------------- #
async def generar_embed(guild_id):
    embed = discord.Embed(title="📊 Dashboard de Torneos Interactivo", color=discord.Color.blue())
    torneos = get_server_torneos(guild_id)
    if not torneos:
        embed.description = "No hay torneos activos. Los admins pueden crear uno con el botón **Crear Torneo**."
        return embed
    
    config = get_server_config(guild_id)
    torneo_seleccionado = config.get("torneo_seleccionado")
    
    if torneo_seleccionado and torneo_seleccionado in torneos:
        torneo = torneo_seleccionado
        participantes = torneos[torneo]
        texto = ""
        equipos_dict = {}
        for uid, equipo in participantes.items():
            if equipo not in equipos_dict:
                equipos_dict[equipo] = []
            try:
                user = await bot.fetch_user(int(uid))
                equipos_dict[equipo].append(user.name)
            except:
                equipos_dict[equipo].append(f"ID:{uid}")
        
        for equipo, miembros in sorted(equipos_dict.items()):
            texto += f"**{equipo}** ({len(miembros)})\n"
            for miembro in miembros:
                texto += f"  • {miembro}\n"
        
        if not texto:
            texto = "No hay participantes aún. ¡Únete usando el botón!"
        embed.add_field(name=f"🏆 Torneo: {torneo}", value=texto[:1024], inline=False)
    else:
        texto_torneos = ""
        for torneo, participantes in get_server_torneos(guild_id).items():
            texto_torneos += f"**{torneo}**: {len(participantes)} participantes\n"
        embed.add_field(name="Torneos Activos", value=texto_torneos or "Ninguno", inline=False)
    
    if ranking:
        sorted_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
        texto_ranking = ""
        for idx, (eq, pts) in enumerate(sorted_ranking[:10], 1):
            emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
            texto_ranking += f"{emoji} **{eq}**: {pts} victoria{'s' if pts != 1 else ''}\n"
        embed.add_field(name="🏆 Ranking General (Top 10)", value=texto_ranking, inline=False)
    
    embed.set_footer(text="Usa los botones y el menú para interactuar con los torneos")
    return embed

async def actualizar_dashboard(guild, channel=None):
    config = get_server_config(guild.id)
    
    if not channel:
        channel_id = config.get("channel_id")
        if not channel_id:
            return
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return
    
    embed = await generar_embed(guild.id)
    view = DashboardViewUser(guild.id)
    message_id = config.get("message_id")
    
    if message_id:
        try:
            msg = await channel.fetch_message(int(message_id))
            await msg.edit(embed=embed, view=view)
            return
        except:
            config["message_id"] = None
            guardar_config()
    
    try:
        msg = await channel.send(embed=embed, view=view)
        config["message_id"] = str(msg.id)
        config["channel_id"] = str(channel.id)
        guardar_config()
    except discord.Forbidden:
        pass
    except Exception as e:
        pass

# ----------------- SELECT Y VIEW ----------------- #
class DashboardViewUser(View):
    """Dashboard simplificado para usuarios normales"""
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = str(guild_id)
        
        # Agregar select menu de torneos
        torneos = get_server_torneos(guild_id)
        if torneos:
            options = [discord.SelectOption(label=n, description=f"{len(torneos[n])} participantes") for n in list(torneos.keys())[:25]]
        else:
            options = [discord.SelectOption(label="Sin torneos", description="No hay torneos disponibles")]
        
        select = Select(
            placeholder="Selecciona un torneo",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"select_{guild_id}"
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        try:
            selected_value = interaction.data.get('values', [None])[0] if interaction.data else None
            if not selected_value or selected_value == "Sin torneos":
                await interaction.response.send_message("❌ No hay torneos disponibles.", ephemeral=True)
                return
            config = get_server_config(self.guild_id)
            config["torneo_seleccionado"] = selected_value
            guardar_config()
            await actualizar_dashboard(interaction.guild)
            await interaction.response.send_message(f"✅ Torneo seleccionado: **{selected_value}**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Unirse a Equipo", style=discord.ButtonStyle.green, emoji="➕", custom_id="btn_unirse")
    async def unirse_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero usando el menú desplegable.", ephemeral=True)
            return
        await interaction.response.send_modal(UnirseModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Cambiar Equipo", style=discord.ButtonStyle.blurple, emoji="🔄", custom_id="btn_cambiar")
    async def cambiar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero.", ephemeral=True)
            return
        await interaction.response.send_modal(CambiarModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Actualizar", style=discord.ButtonStyle.gray, emoji="🔃", custom_id="btn_actualizar")
    async def actualizar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await actualizar_dashboard(interaction.guild)
        await interaction.response.send_message("✅ Dashboard actualizado", ephemeral=True)


class DashboardViewAdmin(View):
    """Dashboard completo para administradores - incluye todos los botones"""
    def __init__(self, guild_id):
        super().__init__(timeout=None)
        self.guild_id = str(guild_id)
        
        # Agregar select menu de torneos
        torneos = get_server_torneos(guild_id)
        if torneos:
            options = [discord.SelectOption(label=n, description=f"{len(torneos[n])} participantes") for n in list(torneos.keys())[:25]]
        else:
            options = [discord.SelectOption(label="Sin torneos", description="No hay torneos disponibles")]
        
        select = Select(
            placeholder="Selecciona un torneo",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"select_{guild_id}"
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        try:
            selected_value = interaction.data.get('values', [None])[0] if interaction.data else None
            if not selected_value or selected_value == "Sin torneos":
                await interaction.response.send_message("❌ No hay torneos disponibles.", ephemeral=True)
                return
            config = get_server_config(self.guild_id)
            config["torneo_seleccionado"] = selected_value
            guardar_config()
            await actualizar_dashboard(interaction.guild)
            await interaction.response.send_message(f"✅ Torneo seleccionado: **{selected_value}**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Unirse a Equipo", style=discord.ButtonStyle.green, emoji="➕", custom_id="btn_unirse_admin")
    async def unirse_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero usando el menú desplegable.", ephemeral=True)
            return
        await interaction.response.send_modal(UnirseModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Cambiar Equipo", style=discord.ButtonStyle.blurple, emoji="🔄", custom_id="btn_cambiar_admin")
    async def cambiar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero.", ephemeral=True)
            return
        await interaction.response.send_modal(CambiarModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Actualizar", style=discord.ButtonStyle.gray, emoji="🔃", custom_id="btn_actualizar_admin")
    async def actualizar_btn_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await actualizar_dashboard(interaction.guild)
        await interaction.response.send_message("✅ Dashboard actualizado", ephemeral=True)

    @discord.ui.button(label="Crear Torneo", style=discord.ButtonStyle.green, emoji="🏆", row=2, custom_id="btn_crear")
    async def crear_torneo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores.", ephemeral=True)
            return
        await interaction.response.send_modal(CrearTorneoModal(self.guild_id))

    @discord.ui.button(label="Eliminar Usuario", style=discord.ButtonStyle.red, emoji="👤", row=2, custom_id="btn_elim_usuario")
    async def eliminar_usuario_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores.", ephemeral=True)
            return
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero.", ephemeral=True)
            return
        await interaction.response.send_modal(EliminarUsuarioModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Eliminar Equipo", style=discord.ButtonStyle.red, emoji="👥", row=2, custom_id="btn_elim_equipo")
    async def eliminar_equipo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores.", ephemeral=True)
            return
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero.", ephemeral=True)
            return
        await interaction.response.send_modal(EliminarEquipoModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Finalizar Torneo", style=discord.ButtonStyle.gray, emoji="🏁", row=3, custom_id="btn_finalizar")
    async def finalizar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores.", ephemeral=True)
            return
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero.", ephemeral=True)
            return
        await interaction.response.send_modal(FinalizarTorneoModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="Registrar Ganador", style=discord.ButtonStyle.green, emoji="🏆", row=3, custom_id="btn_ganador")
    async def ganador_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_server_config(self.guild_id)
        torneo_seleccionado = config.get("torneo_seleccionado")
        torneos = get_server_torneos(self.guild_id)
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores.", ephemeral=True)
            return
        if not torneo_seleccionado or torneo_seleccionado not in torneos:
            await interaction.response.send_message("❌ Selecciona un torneo primero.", ephemeral=True)
            return
        await interaction.response.send_modal(GanarTorneoModal(torneo_seleccionado, self.guild_id))

    @discord.ui.button(label="🎮 Crear Sala", style=discord.ButtonStyle.blurple, emoji="🎮", row=4, custom_id="btn_crear_sala")
    async def crear_sala_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Solo administradores.", ephemeral=True)
            return
        await interaction.response.send_modal(CrearSalaModal(self.guild_id, interaction.channel.id))

# ----------------- SLASH COMMANDS ----------------- #
@bot.tree.command(name="dashboard", description="Mostrar dashboard interactivo de torneos")
async def dashboard_cmd(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo administradores pueden usar este comando.", ephemeral=True)
        return
    
    await interaction.response.defer()
    await actualizar_dashboard(interaction.guild, interaction.channel)
    await interaction.followup.send("✅ Dashboard creado! Los botones funcionarán incluso después de reiniciar el bot.", ephemeral=True)

@bot.tree.command(name="ranking", description="Ver el ranking general de equipos")
async def ranking_cmd(interaction: discord.Interaction):
    if not ranking:
        await interaction.response.send_message("📊 No hay datos de ranking aún.", ephemeral=True)
        return
    
    sorted_ranking = sorted(ranking.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(title="🏆 Ranking General de Equipos", color=discord.Color.gold())
    
    texto = ""
    for idx, (equipo, victorias) in enumerate(sorted_ranking[:15], 1):
        emoji = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"{idx}."
        texto += f"{emoji} **{equipo}**: {victorias} victoria{'s' if victorias != 1 else ''}\n"
    
    embed.description = texto
    embed.set_footer(text=f"Total de {len(ranking)} equipos registrados")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="salas", description="Ver salas activas")
async def salas_cmd(interaction: discord.Interaction):
    salas = get_server_salas(interaction.guild_id)
    
    if not salas:
        await interaction.response.send_message("🎮 No hay salas activas actualmente.", ephemeral=True)
        return
    
    embed = discord.Embed(title="🎮 Salas Activas", color=discord.Color.purple())
    
    texto = ""
    for sala_id, sala in salas.items():
        texto += f"**{sala['nombre']}**\n  ⏰ {sala['hora_apertura']} → {sala['hora_cierre']}\n  👥 {len(sala['jugadores'])} jugadores\n\n"
    
    embed.description = texto if texto else "Sin salas activas"
    embed.set_footer(text="Usa el botón 'Crear Sala' en el panel admin para crear una nueva")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="sala", description="Gestión de salas de notificación")
@discord.app_commands.describe(accion="Abrir o cerrar la notificación de salas")
async def sala_cmd(interaction: discord.Interaction, accion: str):
    AUTHORIZED_ROLES = [1441375993855217775, 1441375990776336424]
    user_roles = [role.id for role in interaction.user.roles]
    has_role = any(role_id in user_roles for role_id in AUTHORIZED_ROLES)
    
    if not has_role and not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True)
        return
    
    if accion.lower() == "abrir":
        embed = discord.Embed(
            title="🔥 Notificación de Salas Free Fire",
            description="¿Quieres jugar hoy? ¡Anótate aquí!",
            color=discord.Color.red()
        )
        embed.add_field(name="🔥 Quiero jugar hoy", value="Confirma que estarás disponible", inline=False)
        embed.add_field(name="🔔 Notificarme", value="Recibe una notificación cuando sea hora", inline=False)
        embed.add_field(name="⚔️ Scrim Ready", value="Anuncia que estás listo para un scrim", inline=False)
        
        view = SalasNotificacionesView(interaction.guild_id)
        config = readConfig()
        if not config.get("notificaciones_salas"):
            config["notificaciones_salas"] = {}
        if not config["notificaciones_salas"].get(str(interaction.guild_id)):
            config["notificaciones_salas"][str(interaction.guild_id)] = {"jugadores_listos": []}
        config["notificaciones_salas"][str(interaction.guild_id)]["mensaje_id"] = ""
        writeConfig(config)
        
        msg = await interaction.channel.send(embed=embed, view=view)
        config["notificaciones_salas"][str(interaction.guild_id)]["mensaje_id"] = str(msg.id)
        config["notificaciones_salas"][str(interaction.guild_id)]["canal_id"] = str(interaction.channel.id)
        writeConfig(config)
        
        await interaction.response.send_message(f"✅ Sala de notificaciones abierta!", ephemeral=True)
    
    elif accion.lower() == "cerrar":
        config = readConfig()
        if config.get("notificaciones_salas") and config["notificaciones_salas"].get(str(interaction.guild_id)):
            config["notificaciones_salas"][str(interaction.guild_id)]["jugadores_listos"] = []
        writeConfig(config)
        await interaction.response.send_message(f"✅ Sala de notificaciones cerrada y lista limpiada!", ephemeral=True)
    
    else:
        await interaction.response.send_message("❌ Usa: `/sala abrir` o `/sala cerrar`", ephemeral=True)

@bot.tree.command(name="panel", description="Panel de administración (solo roles autorizados)")
async def panel_cmd(interaction: discord.Interaction):
    AUTHORIZED_ROLES = [1441375993855217775, 1441375990776336424]
    
    user_roles = [role.id for role in interaction.user.roles]
    has_role = any(role_id in user_roles for role_id in AUTHORIZED_ROLES)
    
    if not has_role:
        await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="👑 Panel de Administración",
        description="Controla todos los aspectos de los torneos y salas",
        color=discord.Color.red()
    )
    
    embed.add_field(
        name="🏆 Funciones Disponibles",
        value=(
            "• **Crear Torneos** - Nuevo torneo\n"
            "• **Eliminar Usuario** - Del torneo actual\n"
            "• **Eliminar Equipo** - Equipo completo\n"
            "• **Finalizar Torneo** - Limpiar roles\n"
            "• **Registrar Ganador** - Sumar victoria\n"
            "• **Crear Sala** - Nueva sala con horarios\n"
        ),
        inline=False
    )
    
    embed.set_footer(text="Usa los botones abajo para gestionar todo")
    
    view = DashboardViewAdmin(interaction.guild_id)
    config = get_server_config(interaction.guild_id)
    config["channel_id"] = str(interaction.channel.id)
    guardar_config()
    
    await interaction.response.send_message(embed=embed, view=view)

# ----------------- COMANDOS DE UTILIDAD (PREFIX) ----------------- #
@bot.command()
async def ayuda(ctx):
    embed = discord.Embed(
        title="📋 Comandos del Bot",
        description="Sistema de torneos interactivo con dashboard",
        color=0x00ff00
    )
    
    embed.add_field(
        name="🏆 Slash Commands",
        value=(
            "`/dashboard` - Crear dashboard interactivo (Admin)\n"
            "`/ranking` - Ver ranking general de equipos"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📅 Eventos",
        value=(
            "`/scrim` - Anunciar scrim disponible\n"
            "`/encuesta [tema]` - Crear encuesta con reacciones\n"
            "`/zona` - Avisar cierre de zona"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👥 Equipos",
        value=(
            "`/equipo [número]` - Generar equipos aleatorios\n"
            "`/entrenar [mapa] [minutos]` - Crear sala de entrenamiento"
        ),
        inline=False
    )
    
    embed.set_footer(text="Usa el dashboard para gestionar torneos de forma interactiva")
    await ctx.send(embed=embed)

@bot.command()
async def scrim(ctx):
    await ctx.send("🔥 ¡Scrim disponible! Únanse y prepárense para la partida.")

@bot.command()
async def encuesta(ctx, *, tema=None):
    if tema:
        message = await ctx.send(f"🗳 **Encuesta:** {tema}")
        await message.add_reaction("✅")
        await message.add_reaction("❌")
    else:
        await ctx.send("Usa: `/encuesta [tema]`")

@bot.command()
async def zona(ctx):
    await ctx.send("⚠️ **¡Cierre de zona en 30 segundos!** Prepárense!")

@bot.command()
async def equipo(ctx, jugadores: int = None):
    if jugadores is None:
        await ctx.send("Usa: `/equipo [número_de_equipos]`")
        return
    members = [member for member in ctx.guild.members if not member.bot]
    if jugadores > len(members):
        await ctx.send("❌ No hay suficientes jugadores para formar esos equipos.")
        return
    random.shuffle(members)
    teams = [members[i::jugadores] for i in range(jugadores)]
    msg = "🎲 **Equipos Generados:**\n\n"
    for i, team in enumerate(teams, 1):
        msg += f"**Equipo {i}:** " + ", ".join([m.name for m in team]) + "\n"
    await ctx.send(msg)

@bot.command()
async def entrenar(ctx, mapa=None, tiempo: int = 30):
    if mapa:
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True)
        }
        canal = await ctx.guild.create_text_channel(f"entreno-{mapa}", overwrites=overwrites)
        await ctx.send(f"✅ Canal de entrenamiento **{canal.name}** creado por {tiempo} minutos.")
        await asyncio.sleep(tiempo * 60)
        await canal.delete()
        await ctx.send(f"⏳ Canal de entrenamiento eliminado después de {tiempo} minutos.")
    else:
        await ctx.send("Usa: `/entrenar [mapa] [tiempo_en_minutos]`")

# ----------------- EVENTOS ----------------- #
@bot.event
async def on_ready():
    # Registrar vistas persistentes para cada servidor configurado
    for guild_id, config in server_configs.items():
        if config.get("channel_id") and config.get("message_id"):
            bot.add_view(DashboardViewUser(guild_id), message_id=int(config["message_id"]))
    
    # Registrar vistas de salas
    for guild_id, salas in server_salas.items():
        for sala_id, sala in salas.items():
            if sala.get("mensaje_id"):
                try:
                    bot.add_view(SalaView(sala_id, guild_id), message_id=int(sala["mensaje_id"]))
                except:
                    pass
    
    # Registrar vistas de notificaciones de salas
    config = readConfig()
    if config.get("notificaciones_salas"):
        for guild_id, settings in config["notificaciones_salas"].items():
            if settings.get("mensaje_id"):
                try:
                    bot.add_view(SalasNotificacionesView(guild_id), message_id=int(settings["mensaje_id"]))
                except:
                    pass
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos sincronizados")
    except Exception as e:
        print(f"❌ Error al sincronizar: {e}")
    
    print(f"✅ {bot.user} se ha conectado!")
    print(f"🏆 Torneos cargados: {sum(len(t) for t in server_torneos.values())}")
    print(f"📈 Equipos en ranking: {len(ranking)}")
    print(f"🖥️ Servidores configurados: {len(server_configs)}")
    print(f"🎮 Salas activas: {sum(len(s) for s in server_salas.values())}")

# ----------------- EJECUTAR BOT ----------------- #
token = os.getenv('DISCORD_TOKEN')
if not token:
    print("❌ Error: No se encontró DISCORD_TOKEN")
    print("Por favor, agrega tu token de bot en los Secrets de Replit")
else:
    bot.run(token)
