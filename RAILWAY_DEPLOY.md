# 🚀 Deployment en Railway (24/7 Gratuito con Créditos)

## ¿Por qué Railway?
✅ $5 USD en créditos gratis al registrarse  
✅ Tu proyecto corre 24/7 mientras haya créditos  
✅ Soporte para Node.js + Python  
✅ Variables de entorno seguras  
✅ Logs en tiempo real  

---

## 📋 PASO A PASO:

### 1️⃣ REGÍSTRATE EN RAILWAY
- Ve a: https://railway.app
- Haz click en "Sign Up" (o usa GitHub)
- Confirma tu email
- **Obtendrás automáticamente $5 USD de crédito gratis**

### 2️⃣ CREA UN NUEVO PROYECTO
- Haz click en "+ New Project"
- Selecciona "Deploy from GitHub"
- Conecta tu cuenta de GitHub
- Selecciona este repositorio

### 3️⃣ CONFIGURA VARIABLES DE ENTORNO
En Railway, agrega estas variables (Variables → Add Variable):

```
DISCORD_TOKEN=<tu_token_del_bot>
DISCORD_CLIENT_ID=<client_id>
DISCORD_CLIENT_SECRET=<client_secret>
DISCORD_REDIRECT_URI=https://tu-proyecto.up.railway.app/auth/callback
GUILD_ID=1441364295282851863
ADMIN_ROLE_IDS=1441375993855217775,1441375990776336424
SESSION_SECRET=<genera_una_cadena_aleatoria_larga>
```

### 4️⃣ INICIA EL DEPLOYMENT
- Railway detectará automáticamente Node.js y Python
- Haz click en "Deploy"
- Espera a que compile (2-5 minutos)

### 5️⃣ ACCEDE A TU PROYECTO
- Railway asignará automáticamente una URL: `https://tu-proyecto.up.railway.app`
- ¡Tu bot y dashboard están VIVOS 24/7!

---

## 📊 MONITOREO

En Railway puedes ver:
- ✅ Logs en tiempo real
- ✅ Uso de recursos (CPU, memoria)
- ✅ Historial de deployments
- ✅ Variables de entorno seguras

---

## 💰 COSTOS DESPUÉS DE CRÉDITOS GRATIS

Después que se agoten los $5:
- **Opción 1**: Esperar al siguiente mes (reset de créditos)
- **Opción 2**: Pagar ~$5-10/mes (muy barato)
- **Opción 3**: Usar otra plataforma

---

## ⚠️ NOTAS IMPORTANTES

1. **URL pública**: Railway te dará una URL raandom, actualiza el `DISCORD_REDIRECT_URI` con la correcta
2. **Persistencia**: Los archivos JSON se guardan en Railway, pero desaparecerán si eliminas el proyecto
3. **Logs**: Revisa los logs si algo falla
4. **Reinicio automático**: Railway reinicia automáticamente si hay un error

---

## 🆘 Si tienes problemas:

1. Revisa los logs en Railway (Dashboard → Logs)
2. Verifica que todas las variables de entorno estén correctas
3. Asegúrate que el DISCORD_TOKEN sea válido
4. Confirma los permisos del bot en Discord

---

¡**Tu sistema está listo para Railway!** 🎉
