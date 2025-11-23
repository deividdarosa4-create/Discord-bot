# 🎮 Dashboard MEE6 - Guía Completa

Tu dashboard estilo **MEE6** está lista para usar. Esta es la guía completa de configuración.

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

En Replit, ve a **Secrets** (candado 🔒) y agrega:

```
DISCORD_CLIENT_ID=tu_client_id
DISCORD_CLIENT_SECRET=tu_client_secret
DISCORD_REDIRECT_URI=https://[tu-proyecto].replit.dev/auth/callback
GUILD_ID=tu_guild_id
ADMIN_ROLE_IDS=role_id_1,role_id_2
SESSION_SECRET=algo_aleatorio
NODE_ENV=development
```

### 2. Obtener Credenciales

**Discord Developer Portal:**
1. Ve a https://discord.com/developers/applications
2. Crea una app o selecciona la existente
3. **OAuth2 → General**: Copia Client ID y Reset Secret
4. **OAuth2 → Redirects**: Agrega `https://[tu-proyecto].replit.dev/auth/callback`

**En Discord:**
1. Modo Desarrollador: Configuración → Avanzado → Activar
2. Haz clic derecho en tu servidor → Copiar ID
3. Haz clic derecho en roles → Copiar ID

### 3. El Servidor Comenzará Automáticamente

La dashboard estará disponible en el preview web de Replit.

---

## 🎨 Funcionalidades de la Dashboard

### 📊 Dashboard Principal
- Resumen de estadísticas del servidor
- Información de miembros, canales, roles
- Acciones rápidas
- Vista elegante estilo MEE6

### ⚙️ Configuración
- Seleccionar canal para **logs**
- Seleccionar canal para **anuncios**
- Activar/desactivar funciones del bot
- Todo sincronizado con la base de datos

### 👥 Gestión de Roles
- Agregar roles automáticos
- Ver todos los roles configurados
- Eliminar roles con un clic
- Colores personalizados para cada rol

### 🎮 Gestión de Salas
- **Crear salas** con nombre, descripción, horarios
- Configurar **máximo de jugadores**
- Ver horarios de apertura y cierre
- Eliminar salas
- Ver jugadores en cada sala

### 📢 Anuncios
- **Crear anuncios** con título y mensaje
- Soporta Markdown para formato
- Historial de anuncios recientes
- Muestra quién creó cada anuncio

### 📊 Logs y Auditoría
- Registro automático de todas las acciones
- API `/api/guild/:guildId/logs` para acceder

---

## 🔌 API REST Completa

### Autenticación
- `GET /auth/login` - Página de login con Discord OAuth2
- `GET /auth/callback` - Callback de Discord
- `GET /auth/logout` - Cerrar sesión

### Dashboard
- `GET /` - Selector de servidores
- `GET /dashboard/:guildId` - Panel principal
- `GET /dashboard/:guildId/settings` - Configuración
- `GET /dashboard/:guildId/roles` - Gestión de roles
- `GET /dashboard/:guildId/rooms` - Gestión de salas
- `GET /dashboard/:guildId/announcements` - Anuncios

### APIs REST

#### Configuración
```
GET    /api/guild/:guildId
POST   /api/guild/:guildId/settings
```

#### Roles
```
GET    /api/guild/:guildId/roles
POST   /api/guild/:guildId/roles
DELETE /api/guild/:guildId/roles/:roleId
```

#### Salas
```
GET    /api/guild/:guildId/rooms
POST   /api/guild/:guildId/rooms
DELETE /api/guild/:guildId/rooms/:roomId
GET    /api/guild/:guildId/rooms/:roomId/players
```

#### Anuncios
```
GET    /api/guild/:guildId/announcements
POST   /api/guild/:guildId/announcements
```

#### Logs
```
GET    /api/guild/:guildId/logs
```

---

## 💾 Base de Datos SQLite

La dashboard usa **SQLite** (mejor-sqlite3) para persistencia:

### Tablas Disponibles

**guild_config**
```
- guild_id (TEXT, PRIMARY KEY)
- guild_name
- guild_icon
- log_channel_id
- announce_channel_id
- features (JSON)
- created_at, updated_at
```

**auto_roles**
```
- id (INTEGER, PRIMARY KEY)
- guild_id
- role_id (UNIQUE)
- role_name
- role_color
- created_at
```

**rooms**
```
- id (INTEGER, PRIMARY KEY)
- guild_id
- room_id (UNIQUE)
- name, description
- open_time, close_time
- max_players
- is_active
- created_at, updated_at
```

**room_players**
```
- id (INTEGER, PRIMARY KEY)
- room_id
- player_id (UNIQUE por sala)
- player_name
- joined_at
```

**announcements**
```
- id (INTEGER, PRIMARY KEY)
- guild_id
- title, message
- posted_by
- posted_at
```

**logs**
```
- id (INTEGER, PRIMARY KEY)
- guild_id
- action, user, details
- created_at
```

---

## 🎯 Casos de Uso

### Caso 1: Configurar Roles Automáticos
1. Ve a **Roles**
2. Haz clic en "+ Agregar Rol"
3. Ingresa el ID del rol y nombre
4. Selecciona un color
5. ¡Listo! Los nuevos miembros recibirán este rol automáticamente

### Caso 2: Crear una Sala para Torneo
1. Ve a **Salas**
2. Haz clic en "+ Crear Sala"
3. Ingresa:
   - Nombre: "Torneo Finals"
   - Descripción: "Final del torneo"
   - Hora de apertura: 19:00
   - Hora de cierre: 21:00
   - Máx. jugadores: 20
4. ¡La sala está lista!

### Caso 3: Enviar Anuncio
1. Ve a **Anuncios**
2. Escribe título: "¡Nuevo Torneo!"
3. Escribe mensaje: "Mañana comienza el torneo..."
4. Haz clic en "Enviar Anuncio"
5. Aparecerá en el historial

---

## 🔗 Conectar con Tu Bot de Discord

El bot de Python puede leer la configuración desde la API:

```python
import requests

guildId = '123456789'
response = requests.get(f'http://localhost:5000/api/guild/{guildId}/settings')
config = response.json()

log_channel_id = config['data']['log_channel_id']
announce_channel_id = config['data']['announce_channel_id']
```

O leer roles automáticos:

```python
response = requests.get(f'http://localhost:5000/api/guild/{guildId}/roles')
roles = response.json()['data']

for role in roles:
    print(f"Rol: {role['role_name']} - Color: {role['role_color']}")
```

---

## 📁 Estructura de Archivos

```
web/
├── index.js                 # Servidor Express + rutas
├── database/
│   ├── db.js               # SQLite manager (mejor-sqlite3)
│   └── bot-dashboard.db    # Base de datos (se crea automáticamente)
├── views/
│   ├── login.ejs           # Página de login
│   ├── servers.ejs         # Selector de servidores
│   ├── dashboard.ejs       # Dashboard principal
│   ├── settings.ejs        # Configuración
│   ├── roles.ejs           # Gestión de roles
│   ├── rooms.ejs           # Gestión de salas
│   ├── announcements.ejs   # Sistema de anuncios
│   ├── sidebar.ejs         # Componente de sidebar
│   └── error.ejs           # Página de error
├── public/
│   └── style.css           # Estilos MEE6
├── package.json            # Dependencias
└── README.md               # Documentación
```

---

## ⚙️ Customización

### Cambiar Colores
Edita `/public/style.css`:

```css
:root {
  --primary: #2c2f33;        /* Color principal (oscuro) */
  --accent: #5865f2;         /* Color de acentos (azul) */
  --success: #00d084;        /* Color de éxito */
  --danger: #ed4245;         /* Color de error */
}
```

### Agregar Nueva Página
1. Crea archivo en `views/` (ej: `stats.ejs`)
2. Agrega ruta en `index.js`:
```javascript
app.get('/dashboard/:guildId/stats', isAuthenticated, async (req, res) => {
  // Tu código aquí
  res.render('stats', { user: req.session.user, guild: userGuild });
});
```
3. Agrega botón en `sidebar.ejs`

---

## 🐛 Troubleshooting

### Error: "OAuth mismatch"
- Verifica que `DISCORD_REDIRECT_URI` sea exacto en secrets y Discord Developer Portal

### Error: "No tienes acceso a este servidor"
- Asegúrate de ser administrador del servidor en Discord
- Verifica que el bot está en el servidor

### Base de datos vacía
- Los datos se crean automáticamente la primera vez
- Archivo: `web/database/bot-dashboard.db`

### Cambios no se guardan
- Verifica que `NODE_ENV=development` está en secrets
- Reinicia el workflow

---

## 🚀 Próximas Mejoras

- [ ] Integración con estadísticas del bot
- [ ] Panel de webhooks personalizados
- [ ] Sistema de prefijos por servidor
- [ ] Dashboard de comandos personalizados
- [ ] Exportar configuración a JSON
- [ ] Importar configuración desde JSON
- [ ] Sistema de permisos granulares

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en `/ logs/Web_Dashboard_*`
2. Verifica que todos los secrets estén configurados
3. Asegúrate de tener permisos en Discord

---

**¡Dashboard MEE6 lista para usar! 🎮**
