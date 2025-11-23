# 🚀 Guía de Configuración Rápida

## Paso 1: Crear Aplicación en Discord Developer Portal

1. Ve a https://discord.com/developers/applications
2. Haz clic en "New Application"
3. Pon un nombre (ej: "Mi Bot Dashboard")
4. Acepta los términos y crea la app

## Paso 2: Obtener Credenciales

### Client ID y Secret
1. En la app, ve a **OAuth2** → **General**
2. Copia el **Client ID**
3. Haz clic en **Reset Secret** y copia el **Client Secret**

### Token del Bot (opcional, para el bot de Discord)
1. Ve a **Bot** → **Add Bot**
2. Copia el **Token**

## Paso 3: Configurar Redirect URI

1. En **OAuth2** → **General**
2. Haz clic en "Add Redirect"
3. Agrega: `https://[TU-PROYECTO].replit.dev/auth/callback`
4. Guarda los cambios

## Paso 4: Obtener IDs Necesarios

### Guild ID (ID del Servidor)
1. En Discord, activa Modo Desarrollador (Configuración → Avanzado → Modo Desarrollador)
2. Haz clic derecho en tu servidor → Copiar ID

### Role IDs (IDs de Roles Admin)
1. En tu servidor, ve a Configuración → Roles
2. Haz clic derecho en los roles que quieres que sean admin
3. Copia los IDs

## Paso 5: Configurar Variables de Entorno en Replit

1. En Replit, ve a la pestaña **Secrets** (candado)
2. Agrega estas variables (copia/pega exactamente):

```
DISCORD_CLIENT_ID=tu_client_id_aqui
DISCORD_CLIENT_SECRET=tu_client_secret_aqui
DISCORD_REDIRECT_URI=https://[TU-PROYECTO].replit.dev/auth/callback
GUILD_ID=tu_guild_id_aqui
ADMIN_ROLE_IDS=role_id_1,role_id_2
SESSION_SECRET=algo_aleatorio_como_abc123xyz789
NODE_ENV=development
```

## Paso 6: Iniciar el Dashboard

1. Replit debería ejecutar automáticamente el servidor web
2. Accede a través del preview web
3. Haz clic en "Iniciar Sesión con Discord"

## ✅ Listo!

Tu dashboard web está funcionando. Ahora puedes:
- Crear salas
- Ver jugadores
- Enviar anuncios
- Ver logs de actividad

---

**¿Necesitas ayuda?** Revisa el archivo `README.md` para documentación completa.
