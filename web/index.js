const express = require('express');
const session = require('express-session');
const axios = require('axios');
require('dotenv').config();
const path = require('path');
const fs = require('fs');
const Store = session.Store;

const app = express();
const PORT = process.env.PORT || 5000;

// Database
const db = require('./database/db');

// Custom SQLite Session Store
class SQLiteSessionStore extends Store {
  constructor() {
    super();
  }

  get(sid, callback) {
    try {
      const sess = db.getSession(sid);
      callback(null, sess);
    } catch (error) {
      callback(error);
    }
  }

  set(sid, sess, callback) {
    try {
      const expires = sess.cookie.expires ? new Date(sess.cookie.expires).getTime() : Date.now() + (30 * 24 * 60 * 60 * 1000);
      db.saveSession(sid, sess, expires);
      if (callback) callback(null);
    } catch (error) {
      if (callback) callback(error);
    }
  }

  destroy(sid, callback) {
    try {
      db.deleteSession(sid);
      if (callback) callback(null);
    } catch (error) {
      if (callback) callback(error);
    }
  }
}

const sessionStore = new SQLiteSessionStore();

// Config file path (shared with bot)
const CONFIG_FILE = path.join(__dirname, '..', 'config.json');

// Helper function to read config.json
const readConfig = () => {
  try {
    if (fs.existsSync(CONFIG_FILE)) {
      const data = fs.readFileSync(CONFIG_FILE, 'utf-8');
      return JSON.parse(data);
    }
    return { configs: {}, torneos: {}, salas: {} };
  } catch (error) {
    console.error('Error reading config:', error);
    return { configs: {}, torneos: {}, salas: {} };
  }
};

// Helper function to write config.json
const writeConfig = (data) => {
  try {
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(data, null, 2));
    return true;
  } catch (error) {
    console.error('Error writing config:', error);
    return false;
  }
};

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, 'public')));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Session configuration
app.use(session({
  store: sessionStore,
  secret: process.env.SESSION_SECRET || 'dev-secret-key-change-in-production',
  resave: false,
  saveUninitialized: false,
  cookie: { 
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    sameSite: 'Lax',
    maxAge: 30 * 24 * 60 * 60 * 1000 // 30 días
  }
}));

// Discord OAuth config
const DISCORD_CLIENT_ID = process.env.DISCORD_CLIENT_ID;
const DISCORD_CLIENT_SECRET = process.env.DISCORD_CLIENT_SECRET;
const DISCORD_REDIRECT_URI = process.env.DISCORD_REDIRECT_URI || 'http://localhost:5000/auth/callback';
const GUILD_ID = process.env.GUILD_ID;
const DISCORD_BOT_TOKEN = process.env.DISCORD_TOKEN;

// Permission constants
const PERMISSION_ADMINISTRATOR = 0x8;

// Helper function to check if user has admin permission in guild
const isUserAdmin = (permissions) => {
  if (!permissions) return false;
  const perms = BigInt(permissions);
  return (perms & BigInt(PERMISSION_ADMINISTRATOR)) === BigInt(PERMISSION_ADMINISTRATOR);
};

// Helper function to send Discord messages
const sendDiscordMessage = async (channelId, content) => {
  if (!channelId || !DISCORD_BOT_TOKEN) {
    console.warn('❌ No channel ID or bot token provided');
    return false;
  }
  
  try {
    await axios.post(`https://discord.com/api/v10/channels/${channelId}/messages`, {
      content: content
    }, {
      headers: {
        'Authorization': `Bot ${DISCORD_BOT_TOKEN}`,
        'Content-Type': 'application/json'
      }
    });
    return true;
  } catch (error) {
    console.error('Error sending Discord message:', error.message);
    return false;
  }
};

// Middleware para verificar autenticación
const isAuthenticated = (req, res, next) => {
  if (req.session.user) {
    next();
  } else {
    res.redirect('/auth/login');
  }
};

// =================== RUTAS DE AUTENTICACIÓN ===================

app.get('/auth/login', (req, res) => {
  const scopes = ['identify', 'guilds', 'guilds.members.read'];
  
  const authUrl = `https://discord.com/api/oauth2/authorize?client_id=${DISCORD_CLIENT_ID}&redirect_uri=${encodeURIComponent(DISCORD_REDIRECT_URI)}&response_type=code&scope=${scopes.join('%20')}`;
  
  res.render('login', { authUrl });
});

app.get('/auth/callback', async (req, res) => {
  const code = req.query.code;
  
  if (!code) {
    return res.status(400).render('error', { 
      title: 'Error de Autenticación',
      message: 'Código de autorización no encontrado.'
    });
  }
  
  try {
    // Intercambiar código por token
    const tokenResponse = await axios.post(
      'https://discord.com/api/oauth2/token',
      new URLSearchParams({
        client_id: DISCORD_CLIENT_ID,
        client_secret: DISCORD_CLIENT_SECRET,
        code: code,
        grant_type: 'authorization_code',
        redirect_uri: DISCORD_REDIRECT_URI,
        scope: 'identify guilds guilds.members.read'
      }),
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      }
    );
    
    const accessToken = tokenResponse.data.access_token;
    
    // Obtener datos del usuario
    const userResponse = await axios.get('https://discord.com/api/users/@me', {
      headers: { Authorization: `Bearer ${accessToken}` }
    });
    
    const user = userResponse.data;
    
    // Obtener servidores del usuario
    try {
      const guildsResponse = await axios.get('https://discord.com/api/users/@me/guilds', {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      user.guilds = guildsResponse.data || [];
    } catch (error) {
      user.guilds = [];
    }
    
    // Guardar en sesión
    req.session.user = {
      id: user.id,
      username: user.username,
      avatar: user.avatar,
      guilds: user.guilds,
      access_token: accessToken
    };
    
    req.session.save((err) => {
      if (err) {
        return res.status(500).render('error', { 
          title: 'Error de Sesión',
          message: 'Error al guardar la sesión.'
        });
      }
      res.redirect('/');
    });
    
  } catch (error) {
    console.error('OAuth error:', error.message);
    res.status(500).render('error', { 
      title: 'Error de Autenticación',
      message: 'Error durante la autenticación con Discord.'
    });
  }
});

app.get('/auth/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) console.error('Logout error:', err);
    res.redirect('/auth/login');
  });
});

// =================== RUTAS PRINCIPALES ===================

app.get('/', isAuthenticated, (req, res) => {
  if (!req.session.user || !req.session.user.guilds || req.session.user.guilds.length === 0) {
    return res.render('no-servers', { user: req.session.user });
  }
  
  // Filter guilds - only show ones where user is admin
  const adminGuilds = req.session.user.guilds.filter(guild => isUserAdmin(guild.permissions));
  
  if (adminGuilds.length === 0) {
    return res.render('no-servers', { 
      user: req.session.user,
      message: 'No tienes permisos de administrador en ningún servidor.'
    });
  }
  
  res.render('servers', { 
    user: req.session.user,
    guilds: adminGuilds
  });
});

app.get('/dashboard/:guildId', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    
    const userGuild = req.session.user.guilds.find(g => g.id === guildId);
    if (!userGuild) {
      return res.status(403).render('error', {
        title: 'Acceso Denegado',
        message: 'No tienes acceso a este servidor.'
      });
    }

    const config = db.getGuildConfig(guildId) || {
      guild_id: guildId,
      guild_name: userGuild.name,
      guild_icon: userGuild.icon
    };

    if (!db.getGuildConfig(guildId)) {
      db.saveGuildConfig(guildId, config);
    }

    // Get stats for dashboard
    const fullConfig = readConfig();
    const serverRooms = fullConfig.salas && fullConfig.salas[guildId] ? fullConfig.salas[guildId] : {};
    const activeRooms = Object.values(serverRooms).filter(r => r.jugadores).length;
    const totalPlayers = Object.values(serverRooms).reduce((sum, r) => sum + (r.jugadores ? r.jugadores.length : 0), 0);
    
    const recentLogs = db.getLogs(guildId, 10);

    res.render('dashboard-home', {
      user: req.session.user,
      guild: userGuild,
      config: config,
      activeRooms: activeRooms,
      totalPlayers: totalPlayers,
      activeTournaments: 0,
      announcementsToday: 0,
      recentLogs: recentLogs
    });
  } catch (error) {
    console.error('Dashboard error:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar el dashboard.'
    });
  }
});

app.get('/dashboard/:guildId/settings', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const userGuild = req.session.user.guilds.find(g => g.id === guildId);
    
    if (!userGuild) {
      return res.status(403).render('error', {
        title: 'Acceso Denegado',
        message: 'No tienes acceso a este servidor.'
      });
    }

    const config = db.getGuildConfig(guildId);
    
    res.render('settings', {
      user: req.session.user,
      guild: userGuild,
      config: config || {}
    });
  } catch (error) {
    console.error('Settings error:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar configuración.'
    });
  }
});

app.get('/dashboard/:guildId/roles', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const userGuild = req.session.user.guilds.find(g => g.id === guildId);
    
    if (!userGuild) {
      return res.status(403).render('error', {
        title: 'Acceso Denegado',
        message: 'No tienes acceso a este servidor.'
      });
    }

    const roles = db.getAutoRoles(guildId);
    
    res.render('roles', {
      user: req.session.user,
      guild: userGuild,
      roles: roles || []
    });
  } catch (error) {
    console.error('Roles error:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar roles.'
    });
  }
});

app.get('/dashboard/:guildId/rooms', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const userGuild = req.session.user.guilds.find(g => g.id === guildId);
    
    if (!userGuild) {
      return res.status(403).render('error', {
        title: 'Acceso Denegado',
        message: 'No tienes acceso a este servidor.'
      });
    }

    const fullConfig = readConfig();
    const serverRooms = fullConfig.salas && fullConfig.salas[guildId] ? fullConfig.salas[guildId] : {};
    
    const activeRooms = Object.entries(serverRooms)
      .map(([id, room]) => ({
        room_id: id,
        nombre: room.nombre,
        hora_apertura: room.hora_apertura,
        hora_cierre: room.hora_cierre,
        jugadores: room.jugadores || [],
        max_players: room.max_players || 50
      }))
      .filter(r => r.jugadores.length > 0 || true);
    
    const closedRooms = [];
    
    res.render('salas-pro', {
      user: req.session.user,
      guild: userGuild,
      activeRooms: activeRooms,
      closedRooms: closedRooms,
      channels: [],
      roles: []
    });
  } catch (error) {
    console.error('Rooms error:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar salas.'
    });
  }
});

// New API routes for Pro Rooms
app.post('/api/salas/crear/:guildId', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const { nombre, max_players, hora_apertura, hora_cierre, channel_id, role_id, custom_message, description } = req.body;
    
    const roomId = String(Date.now());
    console.log(`🎮 Creating pro room: ${nombre} in guild ${guildId}`);
    
    const fullConfig = readConfig();
    if (!fullConfig.salas) fullConfig.salas = {};
    if (!fullConfig.salas[guildId]) fullConfig.salas[guildId] = {};
    
    fullConfig.salas[guildId][roomId] = {
      nombre: nombre,
      hora_apertura: hora_apertura,
      hora_cierre: hora_cierre,
      jugadores: [],
      max_players: max_players,
      canal_id: channel_id,
      rol_id: role_id,
      mensaje_personalizado: custom_message,
      descripcion: description,
      mensaje_id: '',
      estado: 'activa'
    };
    
    writeConfig(fullConfig);
    console.log(`✅ Pro room created: ${roomId}`);
    db.addLog(guildId, 'room_pro_created', req.session.user.username, `Sala PRO creada: ${nombre}`);
    
    const config = db.getGuildConfig(guildId);
    if (config && config.announce_channel_id && channel_id) {
      const embed = `🎮 **${nombre}**\n\n${custom_message || 'Únete a nuestra sala'}\n\n⏰ ${hora_apertura} - ${hora_cierre}\n👥 Cupo: ${max_players}`;
      await sendDiscordMessage(channel_id, embed);
    }
    
    res.json({ success: true, room_id: roomId });
  } catch (error) {
    console.error('Error creating pro room:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/salas/cerrar/:roomId', isAuthenticated, async (req, res) => {
  try {
    const { roomId } = req.params;
    const fullConfig = readConfig();
    
    for (const guildId in fullConfig.salas) {
      if (fullConfig.salas[guildId][roomId]) {
        delete fullConfig.salas[guildId][roomId];
        writeConfig(fullConfig);
        db.addLog(guildId, 'room_pro_closed', req.session.user.username, `Sala cerrada: ${roomId}`);
        return res.json({ success: true });
      }
    }
    
    res.status(404).json({ success: false, error: 'Sala no encontrada' });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/dashboard/:guildId/announcements', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const userGuild = req.session.user.guilds.find(g => g.id === guildId);
    
    if (!userGuild) {
      return res.status(403).render('error', {
        title: 'Acceso Denegado',
        message: 'No tienes acceso a este servidor.'
      });
    }

    const announcements = db.getAnnouncements(guildId);
    
    res.render('announcements', {
      user: req.session.user,
      guild: userGuild,
      announcements: announcements || []
    });
  } catch (error) {
    console.error('Announcements error:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar anuncios.'
    });
  }
});

// =================== API REST ===================

// GET /api/guild/:guildId
app.get('/api/guild/:guildId', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const config = db.getGuildConfig(guildId);
    res.json({ success: true, data: config });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/guild/:guildId/settings
app.post('/api/guild/:guildId/settings', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const { log_channel_id, announce_channel_id, features } = req.body;
    
    const config = db.getGuildConfig(guildId) || {};
    config.log_channel_id = log_channel_id || config.log_channel_id;
    config.announce_channel_id = announce_channel_id || config.announce_channel_id;
    config.features = features || config.features;
    
    const success = db.saveGuildConfig(guildId, config);
    db.addLog(guildId, 'settings_updated', req.session.user.username, 'Configuración actualizada');
    
    res.json({ success, data: config });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/guild/:guildId/roles
app.get('/api/guild/:guildId/roles', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const roles = db.getAutoRoles(guildId);
    res.json({ success: true, data: roles });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/guild/:guildId/roles
app.post('/api/guild/:guildId/roles', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const { role_id, role_name, role_color } = req.body;
    
    const success = db.addAutoRole(guildId, role_id, role_name, role_color);
    if (success) {
      db.addLog(guildId, 'role_added', req.session.user.username, `Rol automático: ${role_name}`);
    }
    
    res.json({ success });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// DELETE /api/guild/:guildId/roles/:roleId
app.delete('/api/guild/:guildId/roles/:roleId', isAuthenticated, (req, res) => {
  try {
    const { guildId, roleId } = req.params;
    const success = db.removeAutoRole(roleId);
    
    if (success) {
      db.addLog(guildId, 'role_removed', req.session.user.username, `Rol removido: ${roleId}`);
    }
    
    res.json({ success });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/guild/:guildId/rooms
app.get('/api/guild/:guildId/rooms', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const fullConfig = readConfig();
    const serverRooms = fullConfig.salas && fullConfig.salas[guildId] ? fullConfig.salas[guildId] : {};
    const rooms = Object.entries(serverRooms).map(([id, room]) => ({
      room_id: id,
      name: room.nombre,
      open_time: room.hora_apertura,
      close_time: room.hora_cierre,
      players_count: room.jugadores ? room.jugadores.length : 0
    }));
    res.json({ success: true, data: rooms });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/guild/:guildId/rooms
app.post('/api/guild/:guildId/rooms', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const { name, description, open_time, close_time, max_players } = req.body;
    const roomId = String(Date.now());
    
    console.log(`📍 Creating room: ${name} in guild ${guildId}`);
    
    const fullConfig = readConfig();
    if (!fullConfig.salas) fullConfig.salas = {};
    if (!fullConfig.salas[guildId]) fullConfig.salas[guildId] = {};
    
    fullConfig.salas[guildId][roomId] = {
      nombre: name,
      hora_apertura: open_time,
      hora_cierre: close_time,
      jugadores: [],
      canal_id: db.getGuildConfig(guildId)?.log_channel_id || '',
      mensaje_id: ''
    };
    
    writeConfig(fullConfig);
    console.log(`✅ Room created in config.json: ${roomId}`);
    db.addLog(guildId, 'room_created', req.session.user.username, `Sala creada: ${name}`);
    
    const config = db.getGuildConfig(guildId);
    if (config && config.announce_channel_id) {
      const message = `🎮 **Nueva Sala Creada**\n\n**Nombre:** ${name}\n**Horario:** ${open_time} - ${close_time}`;
      await sendDiscordMessage(config.announce_channel_id, message);
    }
    
    res.json({ success: true, room_id: roomId });
  } catch (error) {
    console.error(`❌ Room creation error:`, error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// DELETE /api/guild/:guildId/rooms/:roomId
app.delete('/api/guild/:guildId/rooms/:roomId', isAuthenticated, (req, res) => {
  try {
    const { guildId, roomId } = req.params;
    
    const fullConfig = readConfig();
    if (fullConfig.salas && fullConfig.salas[guildId] && fullConfig.salas[guildId][roomId]) {
      delete fullConfig.salas[guildId][roomId];
      writeConfig(fullConfig);
      db.addLog(guildId, 'room_deleted', req.session.user.username, `Sala eliminada: ${roomId}`);
      res.json({ success: true });
    } else {
      res.status(404).json({ success: false, error: 'Sala no encontrada' });
    }
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/guild/:guildId/rooms/:roomId/players
app.get('/api/guild/:guildId/rooms/:roomId/players', isAuthenticated, (req, res) => {
  try {
    const { roomId } = req.params;
    const players = db.getRoomPlayers(roomId);
    res.json({ success: true, data: players });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// POST /api/guild/:guildId/announcements
app.post('/api/guild/:guildId/announcements', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const { title, message } = req.body;
    
    console.log(`📍 Creating announcement: "${title}" in guild ${guildId}`);
    
    const success = db.createAnnouncement(guildId, title, message, req.session.user.username);
    
    if (success) {
      console.log(`✅ Announcement created successfully`);
      db.addLog(guildId, 'announcement_posted', req.session.user.username, `Anuncio: ${title}`);
      
      // Send Discord message
      const config = db.getGuildConfig(guildId);
      console.log(`🔍 Guild config:`, config);
      
      if (config && config.announce_channel_id) {
        const discordMessage = `📢 **${title}**\n\n${message}`;
        console.log(`📤 Sending to channel ${config.announce_channel_id}`);
        const sent = await sendDiscordMessage(config.announce_channel_id, discordMessage);
        console.log(`📤 Discord message sent:`, sent);
      } else {
        console.warn(`⚠️ No announce channel configured for guild ${guildId}`);
      }
      
      res.json({ success: true });
    } else {
      console.error(`❌ Failed to create announcement in database`);
      res.status(400).json({ success: false, error: 'No se pudo crear el anuncio en la base de datos' });
    }
  } catch (error) {
    console.error(`❌ Announcement creation error:`, error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/guild/:guildId/announcements
app.get('/api/guild/:guildId/announcements', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const announcements = db.getAnnouncements(guildId);
    res.json({ success: true, data: announcements });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// GET /api/guild/:guildId/logs
app.get('/api/guild/:guildId/logs', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const logs = db.getLogs(guildId);
    res.json({ success: true, data: logs });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// =================== NOTIFICACIONES DE SALAS ===================

app.get('/dashboard/:guildId/notificaciones-salas', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const userGuild = req.session.user.guilds.find(g => g.id === guildId);
    
    if (!userGuild) {
      return res.status(403).render('error', {
        title: 'Acceso Denegado',
        message: 'No tienes acceso a este servidor.'
      });
    }

    const fullConfig = readConfig();
    const settings = fullConfig.notificaciones_salas && fullConfig.notificaciones_salas[guildId] ? 
      fullConfig.notificaciones_salas[guildId] : {
        notifications_enabled: true,
        notification_role: '@here',
        send_dm: true,
        custom_message: '🔥 ¡Únete a la sala! Tenemos espacio para ti',
        room_name: 'Sala Free Fire',
        room_schedule: '19:00 - 23:00',
        jugadores_listos: []
      };

    const jugadoresAnotados = settings.jugadores_listos || [];
    const jugadoresConfirmados = jugadoresAnotados.filter(j => j.estado === 'confirmado') || [];
    const jugadoresNotificados = jugadoresAnotados.filter(j => j.estado === 'notificado') || [];

    res.render('notificaciones-salas', {
      user: req.session.user,
      guild: userGuild,
      settings: settings,
      jugadoresAnotados: jugadoresAnotados,
      jugadoresConfirmados: jugadoresConfirmados,
      jugadoresNotificados: jugadoresNotificados
    });
  } catch (error) {
    console.error('Notificaciones error:', error);
    res.status(500).render('error', {
      title: 'Error',
      message: 'Error al cargar notificaciones de salas.'
    });
  }
});

app.post('/api/guild/:guildId/notificaciones-salas/config', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const { notifications_enabled, notification_role, send_dm, custom_message, room_name, room_schedule } = req.body;

    const fullConfig = readConfig();
    if (!fullConfig.notificaciones_salas) fullConfig.notificaciones_salas = {};
    if (!fullConfig.notificaciones_salas[guildId]) fullConfig.notificaciones_salas[guildId] = {};

    fullConfig.notificaciones_salas[guildId] = {
      ...fullConfig.notificaciones_salas[guildId],
      notifications_enabled,
      notification_role,
      send_dm,
      custom_message,
      room_name,
      room_schedule
    };

    writeConfig(fullConfig);
    db.addLog(guildId, 'notificaciones_updated', req.session.user.username, 'Configuración de notificaciones actualizada');

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/guild/:guildId/notificaciones-salas/test', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const fullConfig = readConfig();
    const settings = fullConfig.notificaciones_salas && fullConfig.notificaciones_salas[guildId] ? 
      fullConfig.notificaciones_salas[guildId] : {};

    const config = db.getGuildConfig(guildId);
    if (config && config.announce_channel_id && settings.notifications_enabled) {
      const testMessage = `🧪 **Notificación de Prueba**\n\n${settings.custom_message}\n\n🎮 ${settings.room_name}\n⏰ ${settings.room_schedule}`;
      await sendDiscordMessage(config.announce_channel_id, testMessage);
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/guild/:guildId/notificaciones-salas/notificar', isAuthenticated, async (req, res) => {
  try {
    const { guildId } = req.params;
    const fullConfig = readConfig();
    const settings = fullConfig.notificaciones_salas && fullConfig.notificaciones_salas[guildId] ? 
      fullConfig.notificaciones_salas[guildId] : {};

    const config = db.getGuildConfig(guildId);
    if (config && config.announce_channel_id && settings.notifications_enabled) {
      const notifyMessage = `${settings.notification_role} 🔥 **${settings.room_name}**\n\n${settings.custom_message}\n\n⏰ ${settings.room_schedule}\n👥 ${settings.jugadores_listos?.length || 0} jugadores listos`;
      await sendDiscordMessage(config.announce_channel_id, notifyMessage);

      if (settings.send_dm && settings.jugadores_listos && settings.jugadores_listos.length > 0) {
        for (const jugador of settings.jugadores_listos) {
          try {
            const user = await bot.fetch_user(jugador.user_id);
            await user.send(`✉️ Notificación: ${settings.custom_message}\n⏰ ${settings.room_schedule}`);
          } catch (e) {}
        }
      }
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.delete('/api/guild/:guildId/notificaciones-salas/jugador/:userId', isAuthenticated, (req, res) => {
  try {
    const { guildId, userId } = req.params;
    const fullConfig = readConfig();
    if (!fullConfig.notificaciones_salas) fullConfig.notificaciones_salas = {};
    if (!fullConfig.notificaciones_salas[guildId]) fullConfig.notificaciones_salas[guildId] = {};

    const settings = fullConfig.notificaciones_salas[guildId];
    if (settings.jugadores_listos) {
      settings.jugadores_listos = settings.jugadores_listos.filter(j => j.user_id !== userId);
    }

    writeConfig(fullConfig);
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/guild/:guildId/notificaciones-salas/limpiar', isAuthenticated, (req, res) => {
  try {
    const { guildId } = req.params;
    const fullConfig = readConfig();
    if (!fullConfig.notificaciones_salas) fullConfig.notificaciones_salas = {};
    if (!fullConfig.notificaciones_salas[guildId]) fullConfig.notificaciones_salas[guildId] = {};

    fullConfig.notificaciones_salas[guildId].jugadores_listos = [];

    writeConfig(fullConfig);
    db.addLog(guildId, 'notificaciones_cleared', req.session.user.username, 'Lista de jugadores limpiada');

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// =================== ERROR HANDLER ===================

app.use((req, res) => {
  res.status(404).render('error', { 
    title: 'Página no encontrada',
    message: 'La página que buscas no existe.'
  });
});

app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).render('error', { 
    title: 'Error del servidor',
    message: 'Ocurrió un error interno del servidor.'
  });
});

// =================== INICIAR SERVIDOR ===================

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`🌐 Dashboard MEE6 ejecutándose en http://0.0.0.0:${PORT}`);
  console.log(`📊 Modo: ${process.env.NODE_ENV || 'development'}`);
  console.log(`💾 Base de datos: SQLite`);
});

process.on('SIGTERM', () => {
  console.log('SIGTERM recibido, cerrando servidor...');
  server.close(() => {
    console.log('Servidor cerrado.');
    process.exit(0);
  });
});

module.exports = app;
