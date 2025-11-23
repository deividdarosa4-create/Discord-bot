const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const dbPath = path.join(__dirname, 'bot-dashboard.db');

// Crear o conectar a la base de datos
let db;
try {
  db = new Database(dbPath);
  db.pragma('journal_mode = WAL');
} catch (error) {
  console.error('Error conectando a la base de datos:', error);
  db = new Database(dbPath);
}

// Inicializar tablas
const initDatabase = () => {
  try {
    // Tabla de configuración del servidor
    db.exec(`
      CREATE TABLE IF NOT EXISTS guild_config (
        guild_id TEXT PRIMARY KEY,
        guild_name TEXT,
        guild_icon TEXT,
        log_channel_id TEXT,
        announce_channel_id TEXT,
        features TEXT DEFAULT '{}',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Tabla de roles automáticos
    db.exec(`
      CREATE TABLE IF NOT EXISTS auto_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT NOT NULL,
        role_id TEXT NOT NULL,
        role_name TEXT,
        role_color TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(guild_id, role_id),
        FOREIGN KEY(guild_id) REFERENCES guild_config(guild_id)
      )
    `);

    // Tabla de salas
    db.exec(`
      CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT NOT NULL,
        room_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        open_time TEXT,
        close_time TEXT,
        max_players INTEGER DEFAULT 999,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(guild_id) REFERENCES guild_config(guild_id)
      )
    `);

    // Tabla de jugadores en salas
    db.exec(`
      CREATE TABLE IF NOT EXISTS room_players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id TEXT NOT NULL,
        player_id TEXT NOT NULL,
        player_name TEXT,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(room_id, player_id),
        FOREIGN KEY(room_id) REFERENCES rooms(room_id)
      )
    `);

    // Tabla de anuncios
    db.exec(`
      CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        posted_by TEXT NOT NULL,
        posted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(guild_id) REFERENCES guild_config(guild_id)
      )
    `);

    // Tabla de logs
    db.exec(`
      CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id TEXT NOT NULL,
        action TEXT NOT NULL,
        user TEXT NOT NULL,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(guild_id) REFERENCES guild_config(guild_id)
      )
    `);

    // Tabla de sesiones
    db.exec(`
      CREATE TABLE IF NOT EXISTS sessions (
        sid TEXT PRIMARY KEY,
        session TEXT NOT NULL,
        expires INTEGER NOT NULL
      )
    `);

    console.log('✅ Base de datos inicializada correctamente');
  } catch (error) {
    console.error('Error inicializando BD:', error);
  }
};

initDatabase();

// =================== OPERACIONES DE CONFIG ===================

const getGuildConfig = (guildId) => {
  try {
    const stmt = db.prepare('SELECT * FROM guild_config WHERE guild_id = ?');
    return stmt.get(guildId) || null;
  } catch (error) {
    console.error('Error getting guild config:', error);
    return null;
  }
};

const saveGuildConfig = (guildId, config) => {
  try {
    const existing = getGuildConfig(guildId);
    const stmt = existing
      ? db.prepare(`
          UPDATE guild_config 
          SET guild_name = ?, guild_icon = ?, log_channel_id = ?, announce_channel_id = ?, features = ?, updated_at = CURRENT_TIMESTAMP
          WHERE guild_id = ?
        `)
      : db.prepare(`
          INSERT INTO guild_config (guild_id, guild_name, guild_icon, log_channel_id, announce_channel_id, features)
          VALUES (?, ?, ?, ?, ?, ?)
        `);

    if (existing) {
      stmt.run(
        config.guild_name || '',
        config.guild_icon || '',
        config.log_channel_id || '',
        config.announce_channel_id || '',
        JSON.stringify(config.features || {}),
        guildId
      );
    } else {
      stmt.run(
        guildId,
        config.guild_name || '',
        config.guild_icon || '',
        config.log_channel_id || '',
        config.announce_channel_id || '',
        JSON.stringify(config.features || {})
      );
    }

    return true;
  } catch (error) {
    console.error('Error saving guild config:', error);
    return false;
  }
};

// =================== OPERACIONES DE ROLES ===================

const getAutoRoles = (guildId) => {
  try {
    const stmt = db.prepare('SELECT * FROM auto_roles WHERE guild_id = ? ORDER BY created_at DESC');
    return stmt.all(guildId) || [];
  } catch (error) {
    console.error('Error getting auto roles:', error);
    return [];
  }
};

const addAutoRole = (guildId, roleId, roleName, roleColor) => {
  try {
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO auto_roles (guild_id, role_id, role_name, role_color)
      VALUES (?, ?, ?, ?)
    `);
    stmt.run(guildId, roleId, roleName || '', roleColor || '#000000');
    return true;
  } catch (error) {
    console.error('Error adding auto role:', error);
    return false;
  }
};

const removeAutoRole = (roleId) => {
  try {
    const stmt = db.prepare('DELETE FROM auto_roles WHERE role_id = ?');
    stmt.run(roleId);
    return true;
  } catch (error) {
    console.error('Error removing auto role:', error);
    return false;
  }
};

// =================== OPERACIONES DE SALAS ===================

const getRooms = (guildId) => {
  try {
    const stmt = db.prepare('SELECT * FROM rooms WHERE guild_id = ? ORDER BY created_at DESC');
    return stmt.all(guildId) || [];
  } catch (error) {
    console.error('Error getting rooms:', error);
    return [];
  }
};

const createRoom = (guildId, roomId, name, description, openTime, closeTime, maxPlayers) => {
  try {
    console.log(`🔧 DB: Inserting room - Guild: ${guildId}, RoomID: ${roomId}, Name: ${name}`);
    const stmt = db.prepare(`
      INSERT INTO rooms (guild_id, room_id, name, description, open_time, close_time, max_players)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);
    const result = stmt.run(guildId, roomId, name, description, openTime, closeTime, maxPlayers);
    console.log(`🔧 DB: Insert result:`, result);
    
    // Verify insertion
    const verify = db.prepare('SELECT * FROM rooms WHERE room_id = ?').get(roomId);
    console.log(`🔧 DB: Verification query result:`, verify);
    
    return true;
  } catch (error) {
    console.error('Error creating room:', error);
    return false;
  }
};

const deleteRoom = (roomId) => {
  try {
    db.prepare('DELETE FROM room_players WHERE room_id = ?').run(roomId);
    db.prepare('DELETE FROM rooms WHERE room_id = ?').run(roomId);
    return true;
  } catch (error) {
    console.error('Error deleting room:', error);
    return false;
  }
};

const getRoomPlayers = (roomId) => {
  try {
    const stmt = db.prepare('SELECT * FROM room_players WHERE room_id = ? ORDER BY joined_at DESC');
    return stmt.all(roomId) || [];
  } catch (error) {
    console.error('Error getting room players:', error);
    return [];
  }
};

const addPlayerToRoom = (roomId, playerId, playerName) => {
  try {
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO room_players (room_id, player_id, player_name)
      VALUES (?, ?, ?)
    `);
    stmt.run(roomId, playerId, playerName);
    return true;
  } catch (error) {
    console.error('Error adding player to room:', error);
    return false;
  }
};

const removePlayerFromRoom = (roomId, playerId) => {
  try {
    const stmt = db.prepare('DELETE FROM room_players WHERE room_id = ? AND player_id = ?');
    stmt.run(roomId, playerId);
    return true;
  } catch (error) {
    console.error('Error removing player from room:', error);
    return false;
  }
};

// =================== OPERACIONES DE ANUNCIOS ===================

const getAnnouncements = (guildId, limit = 50) => {
  try {
    const stmt = db.prepare(`
      SELECT * FROM announcements 
      WHERE guild_id = ? 
      ORDER BY posted_at DESC 
      LIMIT ?
    `);
    return stmt.all(guildId, limit) || [];
  } catch (error) {
    console.error('Error getting announcements:', error);
    return [];
  }
};

const createAnnouncement = (guildId, title, message, postedBy) => {
  try {
    const stmt = db.prepare(`
      INSERT INTO announcements (guild_id, title, message, posted_by)
      VALUES (?, ?, ?, ?)
    `);
    stmt.run(guildId, title, message, postedBy);
    return true;
  } catch (error) {
    console.error('Error creating announcement:', error);
    return false;
  }
};

// =================== OPERACIONES DE LOGS ===================

const getLogs = (guildId, limit = 100) => {
  try {
    const stmt = db.prepare(`
      SELECT * FROM logs 
      WHERE guild_id = ? 
      ORDER BY created_at DESC 
      LIMIT ?
    `);
    return stmt.all(guildId, limit) || [];
  } catch (error) {
    console.error('Error getting logs:', error);
    return [];
  }
};

const addLog = (guildId, action, user, details) => {
  try {
    const stmt = db.prepare(`
      INSERT INTO logs (guild_id, action, user, details)
      VALUES (?, ?, ?, ?)
    `);
    stmt.run(guildId, action, user, details || '');
    return true;
  } catch (error) {
    console.error('Error adding log:', error);
    return false;
  }
};

// =================== OPERACIONES DE SESIONES ===================

const saveSession = (sid, session, expires) => {
  try {
    const stmt = db.prepare(`
      INSERT OR REPLACE INTO sessions (sid, session, expires)
      VALUES (?, ?, ?)
    `);
    // Store expires as Unix timestamp (milliseconds)
    stmt.run(sid, JSON.stringify(session), expires);
    return true;
  } catch (error) {
    console.error('Error saving session:', error);
    return false;
  }
};

const getSession = (sid) => {
  try {
    const stmt = db.prepare('SELECT session, expires FROM sessions WHERE sid = ? AND expires > ?');
    const result = stmt.get(sid, Date.now());
    if (result) {
      return JSON.parse(result.session);
    }
    return null;
  } catch (error) {
    console.error('Error getting session:', error);
    return null;
  }
};

const deleteSession = (sid) => {
  try {
    const stmt = db.prepare('DELETE FROM sessions WHERE sid = ?');
    stmt.run(sid);
    return true;
  } catch (error) {
    console.error('Error deleting session:', error);
    return false;
  }
};

// =================== EXPORTAR ===================

module.exports = {
  db,
  getGuildConfig,
  saveGuildConfig,
  getAutoRoles,
  addAutoRole,
  removeAutoRole,
  getRooms,
  createRoom,
  deleteRoom,
  getRoomPlayers,
  addPlayerToRoom,
  removePlayerFromRoom,
  getAnnouncements,
  createAnnouncement,
  getLogs,
  addLog,
  saveSession,
  getSession,
  deleteSession
};
