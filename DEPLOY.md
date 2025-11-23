# 🚀 Instrucciones de Despliegue - Dashboard Bot de Discord

## ✅ Lo que se ha Completado

Tu sistema está 100% listo con:

### Bot de Discord (Python)
- ✅ Dashboard interactivo con botones y modales
- ✅ Slash commands (`/dashboard`, `/ranking`, `/salas`, `/panel`)
- ✅ Sistema de torneos completo con roles automáticos
- ✅ Gestión de salas con horarios
- ✅ Ranking global persistente
- ✅ Sincronización JSON

### Dashboard Web (Node.js + Express)
- ✅ Servidor web ejecutándose en puerto 5000
- ✅ Interfaz de login hermosa con Discord
- ✅ Panel administrativo completo
- ✅ API REST para crear/cerrar salas
- ✅ Sistema de logs de actividad
- ✅ Gestión de sesiones segura con OAuth2
- ✅ Base de datos JSON compartida con el bot
- ✅ Interfaz responsive y moderna

---

## 🔐 PASO REQUERIDO: Configurar Variables de Entorno

### 1️⃣ Obtener Credenciales de Discord

Ve a: **https://discord.com/developers/applications**

**Opción A - Si es tu primera aplicación:**
1. Haz clic en "New Application"
2. Pon un nombre (ej: "Tournament Bot")
3. Acepta los términos

**Opción B - Si ya tienes aplicación:**
- Ve a tu aplicación existente

### 2️⃣ Conseguir Client ID y Secret

1. En tu aplicación, ve a **OAuth2** → **General**
2. **Copia el Client ID** (lo verás en la página)
3. Haz clic en **Reset Secret**
4. **Copia el Client Secret** (solo aparece una vez)
5. En Replit, abre la pestaña **Secrets** (icon de candado 🔒)
6. Agrega:
   ```
   DISCORD_CLIENT_ID=<pega-aqui-el-client-id>
   DISCORD_CLIENT_SECRET=<pega-aqui-el-secret>
   ```

### 3️⃣ Configurar Redirect URI

1. En Discord Developer Portal, en **OAuth2** → **General**
2. Haz clic en **Add Redirect**
3. Agrega la URL de tu proyecto Replit:
   ```
   https://[TU-PROYECTO-ID].replit.dev/auth/callback
   ```
   - Puedes ver el ID en la URL de Replit
   - Ejemplo: `https://discord-bot-dashboard.replit.dev/auth/callback`

### 4️⃣ Obtener Guild ID (ID del Servidor)

1. En Discord, **Configuración** → **Avanzado**
2. Activa "Modo Desarrollador"
3. Haz clic derecho en tu servidor
4. Selecciona "Copiar ID"
5. En Replit Secrets, agrega:
   ```
   GUILD_ID=<pega-aqui-el-id>
   ```

### 5️⃣ Obtener Role IDs (IDs de Roles Admin)

1. En tu servidor Discord, **Configuración** → **Roles**
2. Haz clic derecho en cada rol que quieras que sea admin
3. Selecciona "Copiar ID"
4. En Replit Secrets, agrega:
   ```
   ADMIN_ROLE_IDS=<role-id-1>,<role-id-2>
   ```
   - Ejemplo: `ADMIN_ROLE_IDS=1441375993855217775,1441375990776336424`

### 6️⃣ Agregar Session Secret

En Replit Secrets, agrega una clave secreta aleatoria:
```
SESSION_SECRET=tu_secret_aleatorio_aqui_puedes_poner_algo_como_abc123xyz789def456
```

---

## 📋 Checklist Completo de Secrets

Verifica que tienes estas variables en **Secrets**:

- [ ] `DISCORD_TOKEN` - Ya configurado
- [ ] `DISCORD_CLIENT_ID` - Del Developer Portal
- [ ] `DISCORD_CLIENT_SECRET` - Del Developer Portal
- [ ] `DISCORD_REDIRECT_URI` - Tu URL de Replit con `/auth/callback`
- [ ] `GUILD_ID` - ID de tu servidor
- [ ] `ADMIN_ROLE_IDS` - IDs de roles admin separados por comas
- [ ] `SESSION_SECRET` - Clave secreta aleatoria
- [ ] `NODE_ENV=development`

---

## 🎮 Usando el Dashboard

Una vez configuradas las variables:

### En Discord:
1. Usa `/dashboard` - Para el panel interactivo
2. Usa `/panel` - Para panel admin (solo roles autorizados)
3. Usa `/ranking` - Para ver ranking
4. Usa `/salas` - Para ver salas activas

### En la Web:
1. Ve a tu proyecto Replit
2. Haz clic en el preview web
3. Haz clic en "Iniciar Sesión con Discord"
4. Serás redirigido al dashboard admin
5. Desde ahí puedes:
   - Crear nuevas salas
   - Ver jugadores inscritos
   - Enviar anuncios
   - Ver logs de actividad

---

## 📊 Estructura de Archivos

```
/
├── main.py                    # Bot de Discord
├── config.json               # Configuración del bot
├── torneos.json             # Datos de torneos
├── ranking.json             # Ranking de equipos
└── web/                     # Dashboard web
    ├── index.js            # Servidor Express
    ├── package.json        # Dependencias
    ├── database/           # Datos compartidos
    │   ├── salas.json
    │   ├── settings.json
    │   └── logs.json
    ├── views/              # Templates HTML
    ├── public/             # CSS y assets
    └── README.md           # Documentación web
```

---

## 🔄 Workflows Automáticos

Ambos están corriendo automáticamente:

1. **Discord Bot** - `python main.py`
   - Conecta con Discord
   - Escucha comandos

2. **Web Dashboard** - `npm start` en puerto 5000
   - Servidor web accesible desde preview

---

## 🐛 Troubleshooting

### "Error: OAuth mismatch"
- Verifica que `DISCORD_REDIRECT_URI` coincida exactamente con lo configurado en Discord Developer Portal
- Incluye `/auth/callback` al final

### "403 Forbidden en Discord"
- Asegúrate que el bot tiene permisos en tu servidor
- Ve a Discord Developer Portal → Bot → Permissions
- Asegúrate de marcar: Send Messages, Manage Roles, Manage Messages

### "Página en blanco"
- Los secrets pueden tomar 30 segundos en aplicarse
- Reinicia el servidor web
- Abre una ventana incógnito (para limpiar cache)

### "No aparecen mis roles admin"
- Verifica que el ID en `ADMIN_ROLE_IDS` es correcto
- Recuerda separar múltiples IDs con comas: `id1,id2,id3`

---

## 🚀 Próximos Pasos

1. ✅ Configura todas las variables de entorno
2. ✅ Prueба el login con Discord
3. ✅ Crea algunas salas desde la web
4. ✅ Usa los comandos en Discord
5. 📱 (Opcional) Publica tu app si quieres que sea públicamente accesible

---

## 📞 Soporte

- Para documentación técnica: Lee `replit.md`
- Para guía rápida de la web: Lee `web/SETUP.md`
- Para API documentation: Lee `web/README.md`

---

**¡Listo para usar! 🎉**

Una vez configures los secrets, recarga la página y todo debería funcionar sin problemas.
