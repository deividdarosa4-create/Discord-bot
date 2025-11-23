const fs = require('fs');
const path = require('path');

const dbPath = path.join(__dirname);

// Rutas de archivos
const sallasFile = path.join(dbPath, 'salas.json');
const settingsFile = path.join(dbPath, 'settings.json');
const logsFile = path.join(dbPath, 'logs.json');

// Garantizar que los archivos existan
const ensureFile = (filePath, defaultData = {}) => {
  if (!fs.existsSync(filePath)) {
    fs.writeFileSync(filePath, JSON.stringify(defaultData, null, 2));
  }
};

// Inicializar archivos
ensureFile(sallasFile, {});
ensureFile(settingsFile, {
  recordatorios: {},
  funciones_activas: {}
});
ensureFile(logsFile, []);

// =================== OPERACIONES DE SALAS ===================

const getSalas = async () => {
  try {
    const data = fs.readFileSync(sallasFile, 'utf8');
    return JSON.parse(data || '{}');
  } catch (error) {
    console.error('Error reading salas:', error);
    return {};
  }
};

const addSala = async (salaId, salaData) => {
  try {
    const salas = await getSalas();
    salas[salaId] = salaData;
    fs.writeFileSync(sallasFile, JSON.stringify(salas, null, 2));
    return salaData;
  } catch (error) {
    console.error('Error adding sala:', error);
    throw error;
  }
};

const removeSala = async (salaId) => {
  try {
    const salas = await getSalas();
    delete salas[salaId];
    fs.writeFileSync(sallasFile, JSON.stringify(salas, null, 2));
  } catch (error) {
    console.error('Error removing sala:', error);
    throw error;
  }
};

const updateSala = async (salaId, salaData) => {
  try {
    const salas = await getSalas();
    salas[salaId] = { ...salas[salaId], ...salaData };
    fs.writeFileSync(sallasFile, JSON.stringify(salas, null, 2));
    return salas[salaId];
  } catch (error) {
    console.error('Error updating sala:', error);
    throw error;
  }
};

// =================== OPERACIONES DE SETTINGS ===================

const getSettings = async () => {
  try {
    const data = fs.readFileSync(settingsFile, 'utf8');
    return JSON.parse(data || '{}');
  } catch (error) {
    console.error('Error reading settings:', error);
    return {};
  }
};

const saveSettings = async (settings) => {
  try {
    fs.writeFileSync(settingsFile, JSON.stringify(settings, null, 2));
    return settings;
  } catch (error) {
    console.error('Error saving settings:', error);
    throw error;
  }
};

const updateSettings = async (newSettings) => {
  try {
    const current = await getSettings();
    const updated = { ...current, ...newSettings };
    return await saveSettings(updated);
  } catch (error) {
    console.error('Error updating settings:', error);
    throw error;
  }
};

// =================== OPERACIONES DE LOGS ===================

const getLogs = async (limit = 100) => {
  try {
    const data = fs.readFileSync(logsFile, 'utf8');
    const logs = JSON.parse(data || '[]');
    return logs.slice(-limit);
  } catch (error) {
    console.error('Error reading logs:', error);
    return [];
  }
};

const addLog = async (logEntry) => {
  try {
    const logs = await getLogs(999);
    logs.push({
      ...logEntry,
      timestamp: logEntry.timestamp || new Date().toISOString()
    });
    
    // Limitar a 1000 logs
    if (logs.length > 1000) {
      logs.shift();
    }
    
    fs.writeFileSync(logsFile, JSON.stringify(logs, null, 2));
    return logEntry;
  } catch (error) {
    console.error('Error adding log:', error);
    throw error;
  }
};

const clearLogs = async () => {
  try {
    fs.writeFileSync(logsFile, JSON.stringify([], null, 2));
  } catch (error) {
    console.error('Error clearing logs:', error);
    throw error;
  }
};

// =================== EXPORTAR ===================

module.exports = {
  getSalas,
  addSala,
  removeSala,
  updateSala,
  getSettings,
  saveSettings,
  updateSettings,
  getLogs,
  addLog,
  clearLogs
};
