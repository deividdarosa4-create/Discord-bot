# 🎮 Dashboard MEE6 - Bot de Discord

Dashboard profesional **estilo MEE6** para administrar tu bot de Discord desde una interfaz web moderna.

## ✨ Características

✅ **Autenticación Discord OAuth2** - Login seguro con Discord  
✅ **Dashboard Responsivo** - Interfaz elegante tipo MEE6  
✅ **Configuración por Servidor** - Múltiples servidores soportados  
✅ **Gestión de Roles** - Roles automáticos personalizados  
✅ **Gestión de Salas** - Crear y administrar salas  
✅ **Sistema de Anuncios** - Enviar anuncios con formato  
✅ **Base de Datos SQLite** - Persistencia de datos  
✅ **API REST Completa** - Endpoints para control total  
✅ **Logs y Auditoría** - Registro de todas las acciones  
✅ **Interfaz Moderna** - CSS profesional y responsive  

## 🚀 Inicio Rápido

### 1. Instalar Dependencias
```bash
cd web
npm install
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` en la carpeta `web/`:

```env
DISCORD_CLIENT_ID=tu_client_id
DISCORD_CLIENT_SECRET=tu_client_secret
DISCORD_REDIRECT_URI=http://localhost:5000/auth/callback
GUILD_ID=tu_guild_id
ADMIN_ROLE_IDS=role_id_1,role_id_2
SESSION_SECRET=tu_secret_aleatorio
NODE_ENV=development
PORT=5000
```

### 3. Ejecutar el Servidor

```bash
npm start
```

La dashboard estará disponible en `http://localhost:5000`

## 📋 Obtener Credenciales Discord

1. Ve a [Discord Developer Portal](https://discord.com/developers/applications)
2. Crea una aplicación nueva
3. En **OAuth2 → General**:
   - Copia **Client ID**
   - Copia **Client Secret**
4. En **OAuth2 → Redirects**:
   - Agrega `http://localhost:5000/auth/callback` (desarrollo)
   - O `https://[tu-proyecto].replit.dev/auth/callback` (producción)

## 🎯 Funcionalidades

### 📊 Dashboard Principal
- Vista general del servidor
- Estadísticas de miembros, canales, roles
- Acciones rápidas para navegar

### ⚙️ Configuración
- Seleccionar canales para logs
- Seleccionar canales para anuncios
- Activar/desactivar funciones
- Todos los datos guardados en SQLite

### 👥 Gestión de Roles
- Agregar roles automáticos
- Asignar colores a cada rol
- Eliminar roles
- Sincronización automática

### 🎮 Gestión de Salas
- Crear salas con horarios
- Configurar máximo de jugadores
- Ver jugadores en cada sala
- Eliminar salas

### 📢 Anuncios
- Crear anuncios con formato
- Soporta Markdown
- Historial de anuncios
- Información del autor

### 📊 Logs
- Registro automático de acciones
- Ver histórico completo
- API para acceder a logs

## 🔌 API REST

### Autenticación
```
GET /auth/login              Página de login
GET /auth/callback           Callback de Discord
GET /auth/logout             Cerrar sesión
```

### Configuración
```
GET    /api/guild/:guildId                  Obtener config
POST   /api/guild/:guildId/settings         Guardar config
```

### Roles
```
GET    /api/guild/:guildId/roles            Obtener roles
POST   /api/guild/:guildId/roles            Crear rol
DELETE /api/guild/:guildId/roles/:roleId   Eliminar rol
```

### Salas
```
GET    /api/guild/:guildId/rooms                  Obtener salas
POST   /api/guild/:guildId/rooms                  Crear sala
DELETE /api/guild/:guildId/rooms/:roomId         Eliminar sala
GET    /api/guild/:guildId/rooms/:roomId/players Ver jugadores
```

### Anuncios
```
GET    /api/guild/:guildId/announcements   Obtener anuncios
POST   /api/guild/:guildId/announcements   Crear anuncio
```

### Logs
```
GET    /api/guild/:guildId/logs            Obtener logs
```

## 💾 Base de Datos

Usa **SQLite** con [better-sqlite3](https://www.npmjs.com/package/better-sqlite3):

- **guild_config**: Configuración por servidor
- **auto_roles**: Roles automáticos
- **rooms**: Salas creadas
- **room_players**: Jugadores en salas
- **announcements**: Anuncios
- **logs**: Registro de acciones

Se crea automáticamente en `web/database/bot-dashboard.db`

## 📁 Estructura

```
web/
├── index.js                # Servidor Express + rutas
├── package.json            # Dependencias
├── database/
│   ├── db.js              # Manager de SQLite
│   └── bot-dashboard.db   # Base de datos (automática)
├── views/                 # Templates EJS
│   ├── login.ejs
│   ├── servers.ejs
│   ├── dashboard.ejs
│   ├── settings.ejs
│   ├── roles.ejs
│   ├── rooms.ejs
│   ├── announcements.ejs
│   └── sidebar.ejs
├── public/                # Assets estáticos
│   └── style.css
└── README.md             # Este archivo
```

## 🔐 Seguridad

- Autenticación OAuth2 de Discord
- Sesiones encriptadas con express-session
- Verificación de membresía en servidor
- HTTPS recomendado en producción
- Secrets nunca en el código

## 🎨 Personalización

### Cambiar Tema
Edita `public/style.css` - Variables CSS predefinidas:

```css
--primary: #2c2f33
--accent: #5865f2
--success: #00d084
--danger: #ed4245
```

### Agregar Nueva Página
1. Crea `.ejs` en `views/`
2. Agrega ruta en `index.js`
3. Agrega link en `sidebar.ejs`

## 📦 Dependencias

- **express**: Framework web
- **express-session**: Gestión de sesiones
- **axios**: Cliente HTTP
- **dotenv**: Variables de entorno
- **ejs**: Template engine
- **better-sqlite3**: Base de datos

## 🚀 Deployment en Replit

1. Configura secrets en Replit
2. El workflow ejecuta automáticamente
3. Accede a través del preview web

## 🐛 Troubleshooting

**Error: OAuth mismatch**
- Verifica `DISCORD_REDIRECT_URI` exactamente

**Error: 403 Forbidden**
- Asegúrate de ser admin del servidor
- Verifica permisos del bot

**Datos no se guardan**
- Reinicia el servidor
- Verifica permisos de carpeta `database/`

## 📚 Documentación Completa

Ver `MEE6-SETUP.md` para:
- Guía paso a paso de configuración
- Casos de uso detallados
- Integración con bot de Discord

## 📄 Licencia

MIT - Úsalo libremente

## 🙌 Soporte

Si encuentras problemas:
1. Revisa los logs
2. Verifica todos los secrets
3. Consulta `MEE6-SETUP.md`

---

**¡Dashboard MEE6 lista! 🎮**
